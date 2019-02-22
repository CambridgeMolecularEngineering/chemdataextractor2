# -*- coding: utf-8 -*-
"""
Base classes for parsing sentences and tables.
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

    def extract_error(self, string):
        """Extract the error from a string

        Usage::
            bp = BaseParser()
            test_string = '150±5'
            end_value = bp.extract_error(test_string)
            print(end_value) # 5

        Arguments:
            string {[type]} -- [description]
        """
        return extract_error(string)

    def extract_value(self, string):
        """
        Takes a string and returns a float or a list representing the string given.

        Usage::
            bp = BaseParser()
            test_string = '150 to 160'
            end_value = bp.extract_value(test_string)
            print(end_value) # [150., 160.]

        :param str string: A representation of the values as a string
        :returns: The string expressed as a float or a list of floats if it was a value range.
        :rtype: list(float)
        """
        return extract_value(string)

    def extract_units(self, string, strict=False):
        """
        Takes a string and returns a Unit.
        Raises TypeError if strict and the dimensions do not match the expected dimensions
        or the string has extraneous characters, e.g. if a string Fe was given, and we were
        looking for a temperature, strict=False would return Fahrenheit, strinct=True would
        raise a TypeError.

        Usage::
            bp = QuantityParser()
            bp.model = QuantityModel()
            bp.model.dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
            test_string = 'Kh2/(km/s)-1/2'
            end_units = bp.extract_units(test_string, strict=True)
            print(end_units) # Units of: (10^1.5) * Hour^(2.0)  Meter^(0.5)  Second^(-0.5)  Kelvin^(1.0)

        :param str string: A representation of the units as a string
        :param bool strict: Whether to raise a TypeError if the dimensions of the parsed units do not have the expected dimensions.
        :returns: The string expressed as a Unit
        :rtype: chemdataextractor.quantities.Unit
        """
        return extract_units(string, self.model.dimensions, strict)


class BaseSentenceParser(BaseParser):
    """
    Base class for parsing sentences. To implement a parser for a new property,
    impelement the interpret function.
    """

    def parse_sentence(self, tokens):
        for result in self.root.scan(tokens):
            for model in self.interpret(*result):
                yield model


class BaseTableParser(BaseParser):
    """
    Base class for parsing new-style tables. To implement a parser for a new property,
    impelement the interpret function.
    """

    def parse_cell(self, cell):
        if self.root is not None:
            for result in self.root.scan(cell.tagged_tokens):
                try:
                    for model in self.interpret(*result):
                        yield model
                except (AttributeError, TypeError) as e:
                    print(e)
                    pass
