#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tagger wrappers that wrap AllenNLP functionality. Used for and named entity recognition.

"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import math
import logging
import re
import copy
import datetime

from .tag import BaseTagger
from ..data import find_data

import torch
import json
from yaspin import yaspin
from allennlp.data.tokenizers.token import Token as AllenNLPToken
from allennlp.models.archival import load_archive
from allennlp.predictors import SentenceTaggerPredictor
from allennlp.data.instance import Instance
from allennlp.data.fields.text_field import TextField


log = logging.getLogger(__name__)


class ProcessedTextTagger(BaseTagger):
    """
    Class to process text before the text is fed into any other taggers.
    This class is designed to be used with AllenNlpWrapperTagger and replaces any
    single-number tokens with <nUm> in accordance with the training data.
    """
    tag_type = "processed_text"
    number_pattern = re.compile('([\+\-–−]?\d+(([\.・,\d])+)?)')
    number_string = "<nUm>"

    def tag(self, tokens):
        tags = []
        for token in tokens:
            processed_text = token.text
            if re.fullmatch(self.number_pattern, processed_text):
                processed_text = self.number_string
            tags.append((token, processed_text))
        return tags


class _AllenNlpTokenTagger(BaseTagger):
    """
    Class to get the AllenNLP token corresponding to a CDE token.
    Intended for internal use with AllenNlpWrapperTagger.
    """
    tag_type = "_allennlptoken"

    def tag(self, tokens):
        tags = []
        for token in tokens:
            allennlptoken = AllenNLPToken(text=token.processed_text)
            tags.append((token, allennlptoken))
        return tags


class AllenNlpWrapperTagger(BaseTagger):
    """
    A wrapper for an AllenNLP model. Tested with a CRF Tagger but should work with any sequence labeller trained
    in allennlp.
    """
    model = None
    tag_type = None
    indexers = None
    overrides = None

    def __init__(self, indexers=None,
                 weights_location=None,
                 gpu_id=None,
                 archive_location=None,
                 tag_type=None,
                 min_batch_size=None,
                 max_batch_size=None,
                 max_allowed_length=None):
        """
        :param indexers (dict(str, ~allennlp.data.token_indexers.TokenIndexer), optional): A dictionary of all the AllenNLP indexers to be used with the taggers.
            Please refer to their documentation for more detail.
        :param weights_location (str, optional): Location for weights.
            Corresponds to weights_file parameter for the load_archive function from AllenNLP.
        :param gpu_id (int, optional): The ID for the GPU to be used. If None is passed in, ChemDataExtractor will
            automatically detect if a GPU is available and use that. To explicitly use the CPU, pass in a value of -1.
        :param archive_location (str, optional): The location where the model is archived. Corresponds to the archive_file
            parameter in the load_archive function from AllenNLP. Alternatively, you can set this parameter to None and set
            the class property ``model``, which will then search for the model inside of ChemDataExtractor's default model directory.
        :param tag_type (obj, optional): Override the class's tag type. Refer to the documentation for
            :class:`~chemdataextractor.nlp.tag.BaseTagger` for more information on how to use tag types.
        :param min_batch_size (int, optional): The minimum batch size to use when predicting. Default 100.
        :param max_batch_size (int, optional): The maximum batch size to use when predicting. Default 300.
        :param max_allowed_length (int, optional): The maximum allowed length of a sentence when predicting.
            Default 220. Any sentences longer than this will be split into multiple smaller sentences via a sliding window approach and the
            results will be collected. Needs to be a multiple of 4 for correct predictions.
        """
        if tag_type is not None:
            self.tag_type = tag_type
        if indexers is not None:
            self.indexers = indexers
        if self.indexers is None:
            self.indexers = {}
        self._gpu_id = gpu_id
        if archive_location is None:
            archive_location = find_data(self.model)
        self._weights_location = weights_location
        self._archive_location = archive_location
        self._predictor = None
        if self.overrides is None:
            self.overrides = {}

        self.min_batch_size = min_batch_size
        if min_batch_size is None:
            self.min_batch_size = 100

        self.max_batch_size = max_batch_size
        if max_batch_size is None:
            self.max_batch_size = 300

        self.max_allowed_length = max_allowed_length
        if max_allowed_length is None:
            self.max_allowed_length = 220

    def process(self, tag):
        """
        Process the given tag. This can be used for example if the names of tags in training are different
        from what ChemDataExtractor expects.


        :param tag str: The raw string output from the predictor.

        :returns: A processed version of the tag
        :rtype: str
        """
        return tag

    @property
    def predictor(self):
        """
        The AllenNLP predictor for this tagger.
        """
        if self._predictor is None:
            with yaspin(text="Initialising AllenNLP model", side="right").simpleDots as sp:
                gpu_id = self._gpu_id
                if gpu_id is None and torch.cuda.is_available():
                    gpu_id = torch.cuda.current_device()
                loaded_archive = load_archive(archive_file=self._archive_location, weights_file=self._weights_location,
                                              overrides=json.dumps(self.overrides))
                model = loaded_archive.model
                if gpu_id is not None and gpu_id >= 0:
                    model = model.cuda(gpu_id)
                model = model.eval()
                self._predictor = copy.deepcopy(SentenceTaggerPredictor(model=model, dataset_reader=None))
                sp.ok("✔")
        return self._predictor

    def tag(self, tokens):
        tags = list(self.batch_tag([tokens])[0])
        return tags

    def batch_tag(self, sents):
        """
        :param chemdataextractor.doc.text.RichToken sents:
        :returns: list(list(~chemdataextractor.doc.text.RichToken, obj))

        Take a list of lists of all the tokens from all the elements in a document, and return a list of lists of (token, tag) pairs.
        One thing to note is that the resulting list of lists of (token, tag) pairs need not be in the same order as the incoming list
        of lists of tokens, as sorting is done so that we can bucket sentences by their lengths.
        More information can be found in the :class:`~chemdataextractor.nlp.tag.BaseTagger` documentation, and :ref:`in this guide<creating_taggers>`.
        """
        log.debug(len(sents))
        start_time = datetime.datetime.now()

        # Divide up the sentence so that we don't get sentences longer than BERT can handle
        all_allennlptokens, sentence_subsentence_map = self._get_subsentences(sents)

        # Create batches
        all_allennlptokens = sorted(all_allennlptokens, key=len)
        instances = self._create_batches(all_allennlptokens)

        instance_time = datetime.datetime.now()
        log.debug("".join(["Created instances:", str(instance_time - start_time)]))
        log.debug("Num Batches: ", len(instances))
        predictions = []
        for instance in instances:
            prediction_start_time = datetime.datetime.now()
            log.debug("".join(["Batch size:", str(len(instance))]))
            with torch.no_grad():
                batch_predictions = self.predictor.predict_batch_instance(instance)
            predictions.extend(batch_predictions)
            prediction_end_time = datetime.datetime.now()
            log.debug("".join(["Batch time:", str(prediction_end_time - prediction_start_time)]))

        id_predictions_map = {}
        for allensentence, prediction in zip(all_allennlptokens, predictions):
            id_predictions_map[id(allensentence)] = prediction["tags"]

        # Assign tags to each sentence
        tags = self._assign_tags(sents, sentence_subsentence_map, id_predictions_map)

        end_time = datetime.datetime.now()
        log.debug("".join(["Total time for batch_tag:", str(end_time - start_time)]))

        return tags

    def _get_subsentences(self, sents):
        """
        ChemDataExtractor may encounter sentences that are longer than what some of the
        taggers in AllenNLP may support. (e.g. a BERT based tagger only supports sequences
        up to 512 tokens long). This method gets around this limitation by splitting such
        long sentences into multiple overlapping subsentences using a sliding window,
        and returning a map between these subsentences and their parent sentence.
        """
        sentence_subsentence_map = {}
        all_allennlptokens = []
        max_allowed_length = self.max_allowed_length

        for sent in sents:
            subsentences = [sent]

            if len(sent) > max_allowed_length:
                num_sent_divisions = len(sent) / max_allowed_length
                num_tokens_per_subsentence = math.ceil(math.ceil(len(sent) / num_sent_divisions) / 4) * 4
                increment = math.ceil(num_tokens_per_subsentence / 2)
                subsentences = [sent[: num_tokens_per_subsentence]]
                i = increment
                while i + increment < len(sent):
                    subsentences.append(sent[i: i + num_tokens_per_subsentence])
                    i += increment

            allennlpsents_for_sent = []
            for subsent in subsentences:
                allennlptokens = []
                for token in subsent:
                    allennlptokens.append(token._allennlptoken)
                allennlpsents_for_sent.append(id(allennlptokens))
                all_allennlptokens.append(allennlptokens)
            sentence_subsentence_map[id(sent)] = allennlpsents_for_sent

        return all_allennlptokens, sentence_subsentence_map

    def _create_batches(self, all_allennlptokens):
        """
        Create batches to feed into the predictor within the given batch size range.
        To try to be more efficient, these batches are sorted by the length of the sentences.
        """
        min_batch_size = self.min_batch_size
        max_batch_size = self.max_batch_size
        new_list_sequence_delta = 5
        instances = []

        if len(all_allennlptokens) > min_batch_size:
            current_list_min_sequence_length = len(all_allennlptokens[0])
            divided_sents = []
            sents_current = []
            for sent in all_allennlptokens:
                if (len(sent) > current_list_min_sequence_length + new_list_sequence_delta and len(sents_current) > min_batch_size) or len(sents_current) > max_batch_size:
                    divided_sents.append(sents_current)
                    sents_current = [sent]
                    current_list_min_sequence_length = len(sent)
                else:
                    sents_current.append(sent)
            divided_sents.append(sents_current)

            for div_sents in divided_sents:
                division_instances = []
                for sent in div_sents:
                    division_instances.append(Instance({"tokens": TextField(tokens=sent, token_indexers=self.indexers)}))
                instances.append(division_instances)

        else:
            for allennlptokens in all_allennlptokens:
                instances.append(Instance({"tokens": TextField(tokens=allennlptokens, token_indexers=self.indexers)}))
            instances = [instances]
        return instances

    def _assign_tags(self, sents, sentence_subsentence_map, id_predictions_map):
        """
        Assign the tags to the correct sentences based on the map between the sentences
        and subsentences as created in the get_subsentences method.

        See the paper on new NER (citation to be added) for more detail on how the tags
        are allocated from each subsentence.
        """
        tags = []
        for sent in sents:
            sent_tags = []
            allen_ids = sentence_subsentence_map[id(sent)]
            for allen_id in allen_ids:
                sent_tags.append(id_predictions_map[allen_id])
            if len(sent_tags) == 1:
                consolidated_tags = sent_tags[0]
            else:
                consolidated_tags = []
                _ranges_used = []
                num_tokens_per_subsentence = len(sent_tags[0])
                quarter_loc = int(num_tokens_per_subsentence / 4)
                for index, subsent_tags in enumerate(sent_tags):
                    if index == 0:
                        consolidated_tags.extend(subsent_tags[: -quarter_loc])
                        _ranges_used.append(len(subsent_tags[: -quarter_loc]))
                    elif index == len(sent_tags) - 1:
                        consolidated_tags.extend(subsent_tags[quarter_loc:])
                        _ranges_used.append(len(subsent_tags[quarter_loc:]))
                    else:
                        consolidated_tags.extend(subsent_tags[quarter_loc: -quarter_loc])
                        _ranges_used.append(len(subsent_tags[quarter_loc: 3 * quarter_loc]))
            if len(sent) != len(consolidated_tags):
                raise TypeError("The length of the sentence {} and the length of the consolidated tags {} are different.".format(len(sent), len(consolidated_tags)))
            tags.append(zip(sent, [self.process(tag) for tag in consolidated_tags]))
        return tags
