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

from .common import lbrct, rbrct
from .cem import cem, chemical_label, lenient_chemical_label
from ..model.units.dimension import Dimensionless
from .actions import merge, join
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group, SkipTo
from ..utils import first
from .quantity import QuantityParser, magnitudes_dict, value_element, extract_units, value_element_plain
from ..model import Compound
from ..doc.text import Sentence
import xml.etree.ElementTree as etree



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


class BaseAutoParser(QuantityParser):
    model = None
    _specifier = None
    value_phrase_tag = 'baseautoparserproperty'
    root_phrase_tag = 'baseautopropertyphrase'
    property_name = 'property_name'

    def __init__(self):
        self.dimensions = self.model.dimensions

    @property
    def root(self):
        if self._specifier is self.model.specifier:
            return self._root_phrase
        unit_element = Group(construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('units'))(self.value_phrase_tag)
        specifier = self.model.specifier('specifier')
        value_phrase = value_element(unit_element)(self.value_phrase_tag)
        chem_name = (cem | chemical_label | lenient_chemical_label)
        entities = (value_phrase | specifier | chem_name)
        root_phrase = OneOrMore(entities | Any().hide())(self.root_phrase_tag)
        self._root_phrase = root_phrase
        self._specifier = self.model.specifier
        return root_phrase

    def interpret(self, result, start, end):
        try:
            print(etree.tostring(result))
            # Change this to MODEL_PHRASE?
            raw_value = first(result.xpath('./' + self.value_phrase_tag + '/value/text()'))
            raw_units = first(result.xpath('./' + self.value_phrase_tag + '/units/text()'))
            arg_dict = {self.property_name: [self.model(raw_value=raw_value,
                        raw_units=raw_units, value=self.extract_value(raw_value),
                        error=self.extract_error(raw_value),
                        units=self.extract_units(raw_units, strict=True))]}
            compound = Compound(**arg_dict)
            yield compound
        except TypeError as e:
            # log.debug(e)
            compound = Compound()
        except AttributeError as e:
            # For some cases of doing extract_units/extract_value/extract_error
            compound = Compound()
        cem_el = first(result.xpath('./cem'))
        #if cem_el is not None:
        #    compound.names = cem_el.xpath('./name/text()')
        #    compound.labels = cem_el.xpath('./label/text()')
        #yield compound


class AutoTableParser(BaseAutoParser):
    model = None
    _specifier = None

    # @property
    # def root(self):
    #     if self._specifier is self.model.specifier:
    #         return self._root_phrase
    #     unit_element = Group(construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('units'))(self.value_phrase_tag)
    #     specifier = self.model.specifier('specifier') + Optional(lbrct) + Optional(W('/')) + Optional(unit_element) + Optional(rbrct)
    #     value_phrase = value_element_plain()(self.value_phrase_tag)
    #     chem_name = (cem | chemical_label | lenient_chemical_label)
    #     entities = (value_phrase | specifier | chem_name)
    #     root_phrase = OneOrMore(entities | Any().hide())(self.root_phrase_tag)
    #     self._root_phrase = root_phrase
    #     self._specifier = self.model.specifier
    #     print(dir(self.model))
    #     return root_phrase

    @property
    def root(self):
        if self._specifier is self.model.specifier:
            return self._root_phrase
        # will always be possible to find from model:
        unit_element = Group(construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('units'))( self.value_phrase_tag)
        # will always be possible to find from model:
        specifier = self.model.specifier('specifier') + Optional(lbrct) + Optional(W('/')) + Optional(unit_element) + Optional(rbrct)
        # is always there:
        value_phrase = value_element_plain()(self.value_phrase_tag)
        # is always there:
        chem_name = (cem | chemical_label | lenient_chemical_label)

        # NOW COMES the tricky part
        # 1. all other sensible elements of the model need to be added (sensible means that their R,I,W,... can be found
        # 2. some of the elements have to be made optional, for example even chem_name will have to be optional in the future for a later-stage interdependency resolution

        entities = (value_phrase | specifier | chem_name)

        #root_phrase = OneOrMore(entities | Any().hide())(self.root_phrase_tag)
        #root_phrase = All(value_phrase, specifier, chem_name)(self.root_phrase_tag)

        #root_phrase = (entities + entities + ZeroOrMore(Any()) + entities)(self.root_phrase_tag)

        #any_before_entity =

        # complex_entity = (entities | (Any() + entities) | (Any() + Not(entities)))


        # 0. Ignores space in between the tokens
        # root_phrase = (entities + entities + entities)(self.root_phrase_tag)

        # 1. Problem, counts the Any() as well as the entities
        # complex_entity = (entities | (Any() + entities) | (Any() + Not(entities)))
        # root_phrase = (complex_entity + complex_entity + complex_entity)(self.root_phrase_tag)

        # 2. Using the SkipTo() function, works quite well but not perfect
        # for some reason the etree structure is there but the interpret function seems to have problems
        # TODO Check the interpret function etc.
        root_phrase = (entities + SkipTo(entities) + entities + SkipTo(entities) + entities)(self.root_phrase_tag)

        # 3. building up on 2
        # root_phrase = (entities + )(self.root_phrase_tag)


        # root_phrase = OneOrMore(complex_entity)(self.root_phrase_tag)

        #root_phrase = (( entities | (Any() + entities) | (Any() + Not(entities)) ) + entities + entities)(self.root_phrase_tag)



        self._root_phrase = root_phrase
        self._specifier = self.model.specifier
        # print(dir(self.model))
        # print(self.model.fields)
        return root_phrase

    def parse(self, cell):
        string = cell[0] + ' '
        string += ' '.join(cell[1]) + ' '
        string += ' '.join(cell[2])
        sent = Sentence(string)
        for result in self.root.scan(sent.tagged_tokens):
            for model in self.interpret(*result):
                yield model



