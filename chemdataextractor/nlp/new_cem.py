# -*- coding: utf-8 -*-
"""
New and improved named entity recognition (NER) for Chemical entity mentions (CEM).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re

import six

from ..data import find_data
from .finetuned_bert_crf_wrapper import _BertCrfTagger
from .tag import EnsembleTagger, NER_TAG_TYPE
from .allennlpwrapper import _AllenNlpTokenTagger, ProcessedTextTagger, AllenNlpWrapperTagger

from allennlp.data.token_indexers import PretrainedBertIndexer


# Finetuned BERT to CRF
indexers = {
    "bert": PretrainedBertIndexer(do_lowercase=False, use_starting_offsets=True, truncate_long_sequences=False, pretrained_model=find_data("models/scibert_cased_vocab-1.0.txt")),
}

tokentagger = _AllenNlpTokenTagger()
processtagger = ProcessedTextTagger()


class BertFinetunedCRFCemTagger(AllenNlpWrapperTagger):
    """
    A Chemical Entity Mention tagger using a finetuned BERT model with a CRF to constrain the outputs.
    """
    tag_type = NER_TAG_TYPE
    indexers = indexers
    model = "models/bert_finetuned_crf_model-1.0a"
    overrides = {"model.text_field_embedder.token_embedders.bert.pretrained_model": find_data("models/scibert_cased_weights-1.0.tar.gz")}

    def process(self, tag):
        return tag.replace("CEM", "CM")


class CemTagger(EnsembleTagger):
    """
    A state of the art Named Entity Recognition tagger for both organic and inorganic materials
    that uses a tagger based on BERT with a Conditional Random Field to constrain the outputs.
    More details in the paper (https://pubs.acs.org/doi/full/10.1021/acs.jcim.1c01199).
    """
    taggers = [tokentagger, processtagger, BertFinetunedCRFCemTagger()]
