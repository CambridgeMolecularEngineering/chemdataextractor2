# -*- coding: utf-8 -*-
"""
Chemistry-aware natural language processing framework.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .abbrev import AbbreviationDetector, ChemAbbreviationDetector
from .tokenize import SentenceTokenizer, ChemSentenceTokenizer, WordTokenizer, ChemWordTokenizer, FineWordTokenizer, BertWordTokenizer
from .pos import ApPosTagger, ChemApPosTagger, CrfPosTagger, ChemCrfPosTagger
from .cem import LegacyCemTagger, CiDictCemTagger, CsDictCemTagger, CrfCemTagger
from .new_cem import CemTagger
from .tag import NoneTagger, ApTagger, CrfTagger, DictionaryTagger, RegexTagger
from .lexicon import Lexicon, ChemLexicon
