# -*- coding: utf-8 -*-
"""
New and improved named entity recognition (NER) for Chemical entity mentions (CEM).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .tag import EnsembleTagger
from .bertcrf_tagger import _BertCrfTokenTagger, ProcessedTextTagger
from .bertcrf_tagger import BertCrfTagger


tokentagger = _BertCrfTokenTagger()
processtagger = ProcessedTextTagger()


class CemTagger(EnsembleTagger):
    """
    A state of the art Named Entity Recognition tagger for both organic and inorganic materials
    that uses a tagger based on BERT with a Conditional Random Field to constrain the outputs.
    More details in the paper (https://pubs.acs.org/doi/full/10.1021/acs.jcim.1c01199).
    """
    taggers = [tokentagger,
               processtagger,
               BertCrfTagger(),
              ]
