# -*- coding: utf-8 -*-
"""

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractproperty, abstractmethod
from .quantity import extract_error, extract_units, extract_value
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

    def extract_error(self, string):
        """Extract the error from a string

        Usage::
            qp = QuantityParser()
            test_string = '150±5'
            end_value = qp.extract_error(test_string)
            print(end_value) # 5

        Arguments:
            string {[type]} -- [description]
        """
        return extract_error(string)

    def extract_value(self, string):
        """
        Takes a string and returns a float or a list representing the string given.

        Usage::
            qp = QuantityParser()
            test_string = '150 to 160'
            end_value = qp.extract_value(test_string)
            print(end_value) # [150., 160.]

        :param str string: A representation of the values as a string
        :returns: The string expressed as a float or a list of floats if it was a value range.
        :rtype: list(float)
        """
        return extract_value(string)

    def extract_units(self, string, strict=False):
        """
        Takes a string and returns a Unit.
        Raises TypeError if strict and the dimensions do not match the expected dimensions.

        Usage::
            qp = QuantityParser()
            qp.dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
            test_string = 'Kh2/(km/s)-1/2'
            end_units = qp.extract_units(test_string, strict=True)
            print(end_units) # Units of: (10^1.5) * Hour^(2.0)  Meter^(0.5)  Second^(-0.5)  Kelvin^(1.0)

        :param str string: A representation of the units as a string
        :param bool strict: Whether to raise a TypeError if the dimensions of the parsed units do not have the expected dimensions.
        :returns: The string expressed as a Unit
        :rtype: chemdataextractor.quantities.Unit
        """
        return extract_units(string, self.model.dimensions, strict)


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
