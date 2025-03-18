"""_summary_
This module contains the implementation of a BERT-CRF tagger for named entity recognition (NER) using the ChemDataExtractor library.
It includes the configuration class `BertCrfConfig`, the tagger class `BertCrfTagger`, and the model class `BertCrfModel`.
The tagger class is responsible for processing and tagging sentences, while the model class defines the BERT-CRF architecture.
Classes:
    BertCrfConfig: Configuration class for the BERT-CRF model.
    BertCrfTagger: Tagger class for named entity recognition using BERT-CRF.
    BertCrfModel: Model class defining the BERT-CRF architecture.
Functions:
    main: Main function to load the model, tokenize a sample sentence, and perform NER tagging.
Usage:
    To use this module, instantiate the `BertCrfTagger` class and call its `tag` or `batch_tag` methods with the input sentences.
    The `main` function provides an example of how to load the model and perform NER tagging on a sample sentence.
"""

import copy
import datetime
import logging
import math
import re
from typing import Dict, List, Optional, Tuple


import torch
import torch.nn as nn
import numpy as np
from transformers import (
    AutoConfig,
    AutoModel,
    BertTokenizer,
    DataCollatorWithPadding,
    DataCollatorForTokenClassification,
    DefaultDataCollator,
    PretrainedConfig,
    PreTrainedModel,
)
from yaspin import yaspin

from ..data import find_data
from ..errors import ConfigurationError
from .bertcrf_modules import TimeDistributed
from .bertcrf_modules import Token as BertCrfToken
from .crf import (ConditionalRandomField,
                                       allowed_transitions)
from .tag import BaseTagger, NER_TAG_TYPE
from .util import (
    combine_initial_dims,
    get_device_of,
    get_range_vector,
    uncombine_initial_dims,
)


log = logging.getLogger(__name__)


class ProcessedTextTagger(BaseTagger):
    """
    Class to process text before the text is fed into any other taggers.
    This class is designed to be used with AllenNlpWrapperTagger and replaces any
    single-number tokens with <nUm> in accordance with the training data.
    """

    tag_type = "processed_text"
    number_pattern = re.compile("([\+\-–−]?\d+(([\.・,\d])+)?)")
    number_string = "<nUm>"

    def tag(self, tokens):
        tags = []
        for token in tokens:
            processed_text = token.text
            if re.fullmatch(self.number_pattern, processed_text):
                processed_text = self.number_string
            tags.append((token, processed_text))
        return tags


class _BertCrfTokenTagger(BaseTagger):
    """
    Class to get the BertCrf token corresponding to a CDE token.
    Intended for internal use with BertCrfTagger.
    """
    tag_type = "_bertcrftoken"

    def tag(self, tokens):
        tags = []
        for token in tokens:
            bertcrftoken = BertCrfToken(text=token.processed_text)
            tags.append((token, bertcrftoken))
        return tags


class BertCrfConfig(PretrainedConfig):
    model_type = "bert"

    def __init__(
        self,
        num_tags: int = 3,
        dropout=0.1,
        label_namespace: str = "labels",
        label_encoding: Optional[str] = None,
        index_and_label: List[Tuple[int, str]] = None,
        constrain_crf_decoding: bool = True,
        include_start_end_transitions: bool = True,
        model_name_or_path: str = None,
        **kwargs,
    ):
        self.num_tags = num_tags
        self.dropout = dropout
        self.label_namespace = label_namespace
        self.label_encoding = label_encoding
        self.index_and_label = index_and_label
        self.constrain_crf_decoding = constrain_crf_decoding
        self.include_start_end_transitions = include_start_end_transitions
        self.model_name_or_path = model_name_or_path
        super().__init__(**kwargs)


class BertCrfTagger(BaseTagger):

    model = "models/hf_bert_crf_tagger"
    tag_type = NER_TAG_TYPE

    def __init__(
        self,
        gpu_id=None,
        archive_location=None,
        tag_type=None,
        min_batch_size=None,
        max_batch_size=None,
        max_allowed_length=None,
    ):
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
        :param max_batch_size (int, optional): The maximum batch size to use when predicting. Default 200.
        :param max_allowed_length (int, optional): The maximum allowed length of a sentence when predicting.
            Default 220. Any sentences longer than this will be split into multiple smaller sentences via a sliding window approach and the
            results will be collected. Needs to be a multiple of 4 for correct predictions.
        """
        if tag_type is not None:
            self.tag_type = tag_type
        self._gpu_id = gpu_id
        if archive_location is None:
            archive_location = find_data(self.model)
        self._archive_location = archive_location
        self._predictor = None
        self.min_batch_size = min_batch_size
        if min_batch_size is None:
            self.min_batch_size = 50
        self.max_batch_size = max_batch_size
        if max_batch_size is None:
            self.max_batch_size = 100

        self.max_allowed_length = max_allowed_length
        if max_allowed_length is None:
            self.max_allowed_length = 220

        self.bert_tokenizer = BertTokenizer.from_pretrained(
            find_data(self.model), do_lower_case=False
        )

    def collate_batch(self, instances):
        """
        Collate a batch of samples into a dictionary of tensors.
        """
        input_ids = [d["input_ids"] for d in instances]
        offsets = [d["offsets"] for d in instances]
        crf_mask = [d["crf_mask"] for d in instances]
        batched_input_ids = nn.utils.rnn.pad_sequence(
            input_ids, batch_first=True, padding_value=0
        )
        batched_offsets = nn.utils.rnn.pad_sequence(
            offsets, batch_first=True, padding_value=0
        )
        batched_crf_mask = nn.utils.rnn.pad_sequence(
            crf_mask, batch_first=True, padding_value=0
        )
        return {
            "input_ids": batched_input_ids,
            "offsets": batched_offsets,
            "crf_mask": batched_crf_mask,
        }

    def process(self, tag):
        return tag.replace("CEM", "CM")

    def get_predictor_inputs(self, tokens):
        """
        Get the inputs for the predictor
        """
        text = (token.text for token in tokens)
        token_wordpiece_ids = [
            [
                self.bert_tokenizer.wordpiece_tokenizer.vocab[wordpiece]
                for wordpiece in self.bert_tokenizer.wordpiece_tokenizer.tokenize(token)
            ]
            for token in text
        ]

        offsets = []
        offset = 1
        # Count amount of wordpieces accumulated
        pieces_accumulated = 0
        for token in token_wordpiece_ids:

            # For initial offsets, the current value of ``offset`` is the start of
            # the current wordpiece, so add it to ``offsets`` and then increment it.
            offsets.append(offset)
            offset += len(token)

            pieces_accumulated += len(token)

        flat_token_wordpiece_ids = [
            wordpiece_id for token in token_wordpiece_ids for wordpiece_id in token
        ]
        wordpiece_ids = (
            [self.bert_tokenizer.cls_token_id]
            + flat_token_wordpiece_ids
            + [self.bert_tokenizer.sep_token_id]
        )
        mask = [1 for _ in offsets]

        return {
            "input_ids": torch.LongTensor(wordpiece_ids),
            "offsets": torch.LongTensor(offsets),
            "crf_mask": torch.LongTensor(mask),
        }

    @property
    def predictor(self):
        """
        The predictor for this tagger.
        """
        if self._predictor is None:
            with yaspin(
                text="Initialising BertCrf model", side="right"
            ).simpleDots as sp:
                gpu_id = self._gpu_id
                if gpu_id is None and torch.cuda.is_available():
                    print("Automatically activating GPU support")
                    gpu_id = torch.cuda.current_device()
                model = BertCrfModel.from_pretrained(
                    find_data("models/hf_bert_crf_tagger")
                )
                if gpu_id is not None and gpu_id >= 0:
                    model = model.to(f"cuda:{gpu_id}")
                model = model.eval()
                self._predictor = copy.deepcopy(model)
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
        all_bertcrftokens, sentence_subsentence_map = self._get_subsentences(
            sents)

        # Create batches
        all_bertcrftokens = sorted(all_bertcrftokens, key=len)
        instances = self._create_batches(all_bertcrftokens)
        
        instance_time = datetime.datetime.now()
        log.debug("".join(["Created instances:", str(instance_time - start_time)]))
        log.debug("Num Batches: %d", len(instances))
        predictions = []
        for instance in instances:
            prediction_start_time = datetime.datetime.now()
            log.debug("".join(["Batch size:", str(len(instance))]))
            with torch.no_grad():
                batch_predictions = self.predictor.forward_on_instances(instance)
            predictions.extend(batch_predictions)
            prediction_end_time = datetime.datetime.now()
            log.debug(
                "".join(
                    ["Batch time:", str(prediction_end_time - prediction_start_time)]
                )
            )
        id_predictions_map = {}
        for allensentence, prediction in zip(all_bertcrftokens, predictions):
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
        all_bertcrftokens = []
        max_allowed_length = self.max_allowed_length

        for sent in sents:
            subsentences = [sent]

            if len(sent) > max_allowed_length:
                num_sent_divisions = len(sent) / max_allowed_length
                num_tokens_per_subsentence = (
                    math.ceil(math.ceil(len(sent) / num_sent_divisions) / 4) * 4
                )
                increment = math.ceil(num_tokens_per_subsentence / 2)
                subsentences = [sent[:num_tokens_per_subsentence]]
                i = increment
                while i + increment < len(sent):
                    subsentences.append(sent[i : i + num_tokens_per_subsentence])
                    i += increment

            bertcrfsents_for_sent = []
            for subsent in subsentences:
                bertcrftokens = []
                for token in subsent:
                    bertcrftokens.append(token._bertcrftoken)
                bertcrfsents_for_sent.append(id(bertcrftokens))
                all_bertcrftokens.append(bertcrftokens)
            sentence_subsentence_map[id(sent)] = bertcrfsents_for_sent

        return all_bertcrftokens, sentence_subsentence_map

    def _create_batches(self, all_bertcrftokens):
        """
        Create batches to feed into the predictor within the given batch size range.
        To try to be more efficient, these batches are sorted by the length of the sentences.
        """
        min_batch_size = self.min_batch_size
        max_batch_size = self.max_batch_size
        new_list_sequence_delta = 5
        instances = []

        if len(all_bertcrftokens) > min_batch_size:
            current_list_min_sequence_length = len(all_bertcrftokens[0])
            divided_sents = []
            sents_current = []
            for sent in all_bertcrftokens:
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
                    division_instances.append(self.get_predictor_inputs(sent))
                instances.append(self.collate_batch(division_instances))

        else:
            for bertcrftokens in all_bertcrftokens:
                instances.append(self.get_predictor_inputs(bertcrftokens))
            # just a single batch
            instances = [self.collate_batch(instances)]
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
                        consolidated_tags.extend(subsent_tags[:-quarter_loc])
                        _ranges_used.append(len(subsent_tags[:-quarter_loc]))
                    elif index == len(sent_tags) - 1:
                        consolidated_tags.extend(subsent_tags[quarter_loc:])
                        _ranges_used.append(len(subsent_tags[quarter_loc:]))
                    else:
                        consolidated_tags.extend(subsent_tags[quarter_loc:-quarter_loc])
                        _ranges_used.append(
                            len(subsent_tags[quarter_loc : 3 * quarter_loc])
                        )
            if len(sent) != len(consolidated_tags):
                raise TypeError(
                    f"The length of the sentence {len(sent)} and the length of the consolidated tags {len(consolidated_tags)} are different for the tagger for {self.tag_type}."
                )
            tags.append(zip(sent, [self.process(tag) for tag in consolidated_tags]))
        return tags


class BertCrfModel(PreTrainedModel):
    config_class = BertCrfConfig  # Required for saving/loading

    def __init__(self, config):

        super().__init__(config)
        self.bert_model = AutoModel.from_config(
            AutoConfig.from_pretrained(config.model_name_or_path)
        )
        self.num_tags = config.num_tags
        self.tag_projection_layer = TimeDistributed(
            nn.Linear(self.bert_model.config.hidden_size, self.num_tags, bias=True)
        )

        self.label_encoding = config.label_encoding
        self.index_and_label = config.index_and_label
        self.index_to_label = self._index_to_label()
        self.label_to_index = self._label_to_index()

        if config.constrain_crf_decoding:
            if not config.label_encoding:
                raise ConfigurationError(
                    "constrain_crf_decoding is True, but "
                    "no label_encoding was specified."
                )
            labels = self.index_to_label
            constraints = allowed_transitions(config.label_encoding, labels)
        else:
            constraints = None

        self.include_start_end_transitions = config.include_start_end_transitions
        self.crf = ConditionalRandomField(
            self.num_tags,
            constraints,
            include_start_end_transitions=config.include_start_end_transitions,
        )

        # Dropout for regularization
        self.dropout = nn.Dropout(config.dropout)

    def _index_to_label(self):
        return {index: label for index, label in self.index_and_label}

    def _label_to_index(self):
        return {label: index for index, label in self.index_and_label}

    def forward(self, input_ids, offsets, crf_mask, token_type_ids=None):

        if token_type_ids is None:
            token_type_ids = torch.zeros_like(input_ids)

        input_mask = (input_ids != 0).long()

        # input_ids may have extra dimensions, so we reshape down to 2-d
        # before calling the BERT model and then reshape back at the end.
        outputs = self.bert_model(
            input_ids=combine_initial_dims(input_ids),
            token_type_ids=combine_initial_dims(token_type_ids),
            attention_mask=combine_initial_dims(input_mask),
        )

        last_hidden_state = outputs.last_hidden_state
        last_hidden_state = self.dropout(last_hidden_state)

        # At this point, mix is (batch_size * d1 * ... * dn, sequence_length, embedding_dim)
        # offsets is (batch_size, d1, ..., dn, orig_sequence_length)
        offsets2d = combine_initial_dims(offsets)
        # now offsets is (batch_size * d1 * ... * dn, orig_sequence_length)
        range_vector = get_range_vector(
            offsets2d.size(0), device=get_device_of(last_hidden_state)
        ).unsqueeze(1)
        # selected embeddings is also (batch_size * d1 * ... * dn, orig_sequence_length)
        selected_embeddings = last_hidden_state[range_vector, offsets2d]

        output_embeddings = uncombine_initial_dims(selected_embeddings, offsets.size())

        # Project onto tag space
        logits = self.tag_projection_layer(output_embeddings)
        best_paths = self.crf.viterbi_tags(logits, crf_mask)

        predicted_tags = [x for x, y in best_paths]

        output = {"logits": logits, "mask": crf_mask, "tags": predicted_tags}

        return output

    def forward_on_instances(
        self, instances: Dict[str, torch.Tensor]
    ) -> List[Dict[str, np.ndarray]]:
        """
        Takes a list of  :class:`~allennlp.data.instance.Instance`s, converts that text into
        arrays using this model's :class:`Vocabulary`, passes those arrays through
        :func:`self.forward()` and :func:`self.decode()` (which by default does nothing)
        and returns the result.  Before returning the result, we convert any
        ``torch.Tensors`` into numpy arrays and separate the
        batched output into a list of individual dicts per instance. Note that typically
        this will be faster on a GPU (and conditionally, on a CPU) than repeated calls to
        :func:`forward_on_instance`.

        Parameters
        ----------
        instances : Dict[str, torch.Tensor], required
            The instances to run the model on.

        Returns
        -------
        A list of the models output for each instance.
        """
        batch_size = instances["input_ids"].size(0)
        with torch.no_grad():
            instances = {k: v.to(self.device) for k, v in instances.items()}
            outputs = self.decode(self(**instances))

            instance_separated_output: List[Dict[str, np.ndarray]] = [
                {} for _ in range(batch_size)
            ]
            for name, output in list(outputs.items()):
                if isinstance(output, torch.Tensor):
                    # NOTE(markn): This is a hack because 0-dim pytorch tensors are not iterable.
                    # This occurs with batch size 1, because we still want to include the loss in that case.
                    # if output.dim() == 0:
                    #     output = output.unsqueeze(0)

                    output = output.detach().cpu().numpy()
                for instance_output, batch_element in zip(
                    instance_separated_output, output
                ):
                    instance_output[name] = batch_element
            return instance_separated_output

    def decode(self, output_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Converts the tag ids to the actual tags.
        ``output_dict["tags"]`` is a list of lists of tag_ids,
        so we use an ugly nested list comprehension.
        """
        output_dict["tags"] = [
            [self.index_to_label[tag] for tag in instance_tags]
            for instance_tags in output_dict["tags"]
        ]
        return output_dict
