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
    trigger_phrase = None
    """
    Optional :class:`~chemdataextractor.parse.elements.BaseParserElement` instance.
    All sentences are run through this before the full root phrase is applied to the
    sentence. If nothing is found for this phrase, the sentence will not go through
    the full root phrase. This is done for performance reasons, and if not set,
    ChemDataExtractor will perform as it did in previous versions. If this phrase is
    set to an appropriate value, it can help ChemDataExtractor perform at up to 2x
    its previous speed.

    To ensure that this works as intended, the :class:`~chemdataextractor.parse.elements.BaseParserElement`
    should be a simple parse rule (substantially simpler than the :class:`~chemdataextractor.parse.base.BaseParser.root`)
    that takes little time to process.
    """

    @abstractproperty
    def root(self):
        pass

    @abstractmethod
    def interpret(self, result, start, end):
        pass

    def extract_error(self, string):
        """
        Extract the error from a string

        Usage::

            bp = BaseParser()
            test_string = '150±5'
            end_value = bp.extract_error(test_string)
            print(end_value) # 5

        :param str string: A representation of the value and error as a string
        :returns: The error expressed as a float .
        :rtype: float
        """
        return extract_error(string)

    def extract_value(self, string):
        """
        Takes a string and returns a list of floats representing the string given.

        Usage::

            bp = BaseParser()
            test_string = '150 to 160'
            end_value = bp.extract_value(test_string)
            print(end_value) # [150., 160.]

        :param str string: A representation of the values as a string
        :returns: The value expressed as a list of floats of length 1 if the value had no range,
            and as a list of floats of length 2 if it was a range.
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

    def parse_sentence(self, sentence):
        """
        Parse a sentence. This function is primarily called by the
        :attr:`~chemdataextractor.doc.text.Sentence.records` property of
        :class:`~chemdataextractor.doc.text.Sentence`.

        :param list[(token,tag)] tokens: List of tokens for parsing. When this method
            is called by :attr:`chemdataextractor.doc.text.Sentence.records`,
            the tokens passed in are :attr:`chemdataextractor.doc.text.Sentence.tagged_tokens`.
        :returns: All the models found in the sentence.
        :rtype: Iterator[:class:`chemdataextractor.model.base.BaseModel`]
        """
        if self.trigger_phrase is not None:
            trigger_phrase_results = [result for result in self.trigger_phrase.scan(sentence.tokens)]
        if self.trigger_phrase is None or trigger_phrase_results:
            for result in self.root.scan(sentence.tokens):
                for model in self.interpret(*result):
                    yield model


class BaseTableParser(BaseParser):
    """
    Base class for parsing new-style tables. To implement a parser for a new property,
    impelement the interpret function.
    """

    def parse_cell(self, cell):
        """
        Parse a cell. This function is primarily called by the
        :attr:`~chemdataextractor.doc.table.Table.records` property of
        :class:`~chemdataextractor.doc.table.Table`.

        :param list[(token,tag)] tokens: List of tokens for parsing. When this method
            is called by :attr:`chemdataextractor.doc.text.table.Table`,
            the tokens passed in are in the same form as
            :attr:`chemdataextractor.doc.text.Sentence.tagged_tokens`, after the
            category table has been flattened into a sentence.
        :returns: All the models found in the table.
        :rtype: Iterator[:class:`chemdataextractor.model.base.BaseModel`]
        """
        if self.trigger_phrase is not None:
            trigger_phrase_results = [result for result in self.trigger_phrase.scan(cell.tokens)]
        if (self.trigger_phrase is None or trigger_phrase_results) and self.root is not None:
            for result in self.root.scan(cell.tokens):
                try:
                    for model in self.interpret(*result):
                        yield model
                except (AttributeError, TypeError) as e:
                    print(e)
                    pass
