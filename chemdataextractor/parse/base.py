# -*- coding: utf-8 -*-
"""

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractproperty, abstractmethod
import logging

log = logging.getLogger(__name__)


class BaseParser(object):
    """"""
    model = None

    @abstractproperty
    def root(self):
        pass

    @abstractmethod
    def interpret(self, result, start, end):
        pass

    # def parse(self, tokens):
    #     for result in self.root.scan(tokens):
    #         for model in self.interpret(*result):
    #             yield model

    def __init__(self):
        self.needs_update = True

    @property
    def root_phrase(self):
        if self.needs_update:
            self._root_phrase = self.root
            self.needs_update = False
            return self._root_phrase
        else:
            return self._root_phrase


class BaseSentenceParser(BaseParser):
    """"""

    def parse_sentence(self, tokens):
        for result in self.root_phrase.scan(tokens):
            for model in self.interpret(*result):
                yield model


class BaseTableParser(BaseParser):
    """"""

    def parse_table(self, tokens):
        for result in self.root_phrase.scan(tokens):
            for model in self.interpret(*result):
                yield model
