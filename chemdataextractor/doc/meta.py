# -*- coding: utf-8 -*-
"""
MetaData Document elements

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractproperty, abstractmethod
import collections
import logging
import re

import six

from ..model.base import ModelList
from ..nlp.lexicon import ChemLexicon, Lexicon
from ..nlp.cem import CemTagger, IGNORE_PREFIX, IGNORE_SUFFIX, SPECIALS, SPLITS, CiDictCemTagger, CsDictCemTagger, CrfCemTagger
from ..nlp.abbrev import ChemAbbreviationDetector
from ..nlp.tag import NoneTagger
from ..nlp.pos import ChemCrfPosTagger, CrfPosTagger, ApPosTagger, ChemApPosTagger
from ..nlp.tokenize import ChemSentenceTokenizer, ChemWordTokenizer, regex_span_tokenize, SentenceTokenizer, WordTokenizer, FineWordTokenizer
from ..text import CONTROL_RE
from ..utils import memoized_property, python_2_unicode_compatible, first
from .element import BaseElement
from ..parse.definitions import specifier_definition
from ..parse.cem import chemical_name
from ..model.model import Compound, NmrSpectrum, IrSpectrum, UvvisSpectrum, MeltingPoint, GlassTransition

from lxml import etree


log = logging.getLogger(__name__)

class MetaData(BaseElement):

    def __init__(self, data):
        super(MetaData, self).__init__()
        print(data)
        self._data = data
        self._title = None
        self._authors = None
        self._publisher = None
        self._journal = None
        self._volume = None
        self._issue = None
        self._firstpage = None
        self._lastpage = None
        self._doi = None
        self._date = None
        self._language = None
        self._pdf_url = None
        self._html_url = None
        for key, value in data.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return {k: v for k, v in self.data.items() if v}.__str__()
    
    @property
    def records(self):
        return []

    def to_dict(self):
        return {k: v for k, v in self.data.items() if v}

    @property
    def title(self):
        return self._title

    @property
    def authors(self):
        return self._authors

    @property
    def publisher(self):
        return self._publisher

    @property
    def journal(self):
        return self._journal

    @property
    def volume(self):
        return self._volume
    
    @property
    def issue(self):
        return self._issue
    
    @property
    def firstpage(self):
        return self._firstpage
    
    @property
    def lastpage(self):
        return self._lastpage
    
    @property
    def doi(self):
        return self._doi
    
    @property
    def pdf_url(self):
        return self._pdf_url
    
    @property
    def html_url(self):
        return self._html_url
    
    @property
    def date(self):
        return self._date
    
    @property
    def data(self):
        return {k.lstrip('_'): v for k, v in self._data.items()}
    
    @property
    def abbreviation_definitions(self):
        return []
    
    @property
    def definitions(self):
        return []