# -*- coding: utf-8 -*-
"""
Base parser for automatically parsing

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re
from abc import abstractproperty
import copy

from .common import lbrct, rbrct
from ..model.units.unit import DimensionlessUnit
from .cem import cem, chemical_label, lenient_chemical_label
from ..model.units.dimension import Dimensionless
from ..model.units.temperature import Temperature, TemperatureModel
from .actions import merge, join
from .base import BaseParser
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group
from fractions import Fraction
from ..model.base import ListType
from ..utils import first
from ..model.units.quantity_model import DimensionlessModel
from .quantity import QuantityParser, magnitudes_dict, value_element, extract_units, value_element_plain
from ..model import Compound
from ..doc.text import Sentence
from lxml import etree


def construct_unit_element(dimensions):
    if isinstance(dimensions, Dimensionless):
        return Any()
    units_regex = '(('
    for element in magnitudes_dict.keys():
        units_regex += '(' + element.pattern + ')|'
    units_regex = units_regex[:-1]
    units_regex += ')?'
    units_regex += '('
    for element in dimensions.units_dict:
        units_regex += '(' + element.pattern + ')|'
    units_regex = units_regex[:-1]
    units_regex += ')'
    units_regex += ')+'
    return OneOrMore(R(pattern=units_regex, group=0)).add_action(merge)


def match_dimensions_of(model):
    def check_match(result):
        if extract_units(result[0].text, model.dimensions).dimensions == model.dimensions:
            return True
        return False
    return check_match


def create_total_phrase(model):
    manually_created = ['value', 'units', 'specifier', '']
    for field in model.fields:
        if field.name not in manually_created:
            pass


model = TemperatureModel


class BaseAutoParser(QuantityParser):
    model = model
    _specifier = None

    def __init__(self):
        self.dimensions = self.model.dimensions

    @property
    def root(self):
        if self._specifier is model.specifier:
            return self._root_phrase
        unit_element = Group(construct_unit_element(model.dimensions).with_condition(match_dimensions_of(model))('units'))('baseautoparserproperty')
        specifier = model.specifier('specifier')
        value_phrase = value_element(unit_element)('baseautoparserproperty')
        chem_name = (cem | chemical_label | lenient_chemical_label)
        entities = (value_phrase | specifier | chem_name)
        root_phrase = OneOrMore(entities | Any().hide())('baseautoparserpropertyphrase')
        self._root_phrase = root_phrase
        self._specifier = model.specifier
        return root_phrase

    def interpret(self, result, start, end):
        try:
            # print(etree.tostring(result))
            # Change this to MODEL_PHRASE?
            raw_value = first(result.xpath('./baseautoparserproperty/value/text()'))
            raw_units = first(result.xpath('./baseautoparserproperty/units/text()'))
            #TODO: How to add property_name to Compound automatically?
            compound = Compound(
                property_name=[
                    self.model(
                        raw_value=raw_value,
                        raw_units=raw_units,
                        value=self.extract_value(raw_value),
                        error=self.extract_error(raw_value),
                        units=self.extract_units(raw_units, strict=True)
                    )
                ]
            )
        except TypeError as e:
            # log.debug(e)
            compound = Compound()
        except AttributeError as e:
            # For some cases of doing extract_units/extract_value/extract_error
            compound = Compound()
        cem_el = first(result.xpath('./cem'))
        if cem_el is not None:
            compound.names = cem_el.xpath('./name/text()')
            compound.labels = cem_el.xpath('./label/text()')
        yield compound


class AutoTableParser(BaseAutoParser):
    model = model
    _specifier = None

    @property
    def root(self):
        # Not sure if this is valid, there must be a better way of doing this?
        if self._specifier is model.specifier:
            return self._root_phrase
        unit_element = Group(construct_unit_element(model.dimensions).with_condition(match_dimensions_of(model))('units'))('baseautoparserproperty')
        specifier = model.specifier('specifier') + Optional(lbrct) + Optional(W('/')) + Optional(unit_element) + Optional(rbrct)
        value_phrase = value_element_plain()('baseautoparserproperty')
        chem_name = (cem | chemical_label | lenient_chemical_label)
        entities = (value_phrase | specifier | chem_name)
        root_phrase = OneOrMore(entities | Any().hide())('baseautoparserpropertyphrase')
        self._root_phrase = root_phrase
        self._specifier = model.specifier
        return root_phrase

    def parse(self, cell):
        string = cell[0] + ' '
        string += ' '.join(cell[1]) + ' '
        string += ' '.join(cell[2])
        sent = Sentence(string)
        for result in self.root.scan(sent.tagged_tokens):
            for model in self.interpret(*result):
                yield model



