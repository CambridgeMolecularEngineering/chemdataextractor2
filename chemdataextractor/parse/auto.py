# -*- coding: utf-8 -*-
"""
Parser for automatic parsing, without user-written parsing rules.
Mainly used for tables.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)

:codeauthor: Juraj Mavračić (jm2111@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging

from .common import lbrct, rbrct
from .cem import cem, chemical_label, lenient_chemical_label
from .actions import merge, join
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group, SkipTo, Or
from ..utils import first
from .quantity import magnitudes_dict, value_element, extract_units, value_element_plain
from .base import BaseSentenceParser, BaseParser, BaseTableParser

import xml.etree.ElementTree as etree


def construct_unit_element(dimensions):
    """
    Construct an element for detecting units for the dimensions given.
    Any magnitude modifiers (e.g. kilo) will be automatically handled.

    :param Dimension dimensions: The dimensions that the element produced will look for.
    :returns: An Element to look for units of given dimensions. If None or Dimensionless are passed in, returns None.
    :rtype: BaseParserElement or None
    """
    if not dimensions:
        return None
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
    return OneOrMore(R(pattern=units_regex)).add_action(merge)


def match_dimensions_of(model):
    """
    Produces a function that checks whether the given results of parsing match the
    dimensions of the model provided.

    :param QuantityModel model: The model with which to check dimensions.
    :returns: A function which will return True if the results of parsing match the model's dimensions, False if not.
    :rtype: function(tuple(list(Element), int) -> bool)
    """
    def check_match(result):
        try:
            extract_units(result[0].text, model.dimensions, strict=True)
            return True
        except TypeError as e:
            return False
    return check_match


def create_entities_list(entities):
    """
    For a list of Base parser entities, creates an entity of structure. For example, with 4 entities in the list, the output is::

        (entities[0] | entities[1] | entities[2] | entities[3])

    :param entities: BaseParserElement type objects
    :return: BaseParserElement type object
    """
    result = entities[0]
    for entity in entities[1:]:
        result = (result | entity)
    return result


class BaseAutoParser(BaseParser):
    model = None
    _specifier = None
    _root_phrase = None

    @property
    def root(self):
        if self._specifier is self.model.specifier:
            return self._root_phrase

        # is always found, our models currently rely on the compound
        chem_name = (cem | chemical_label | lenient_chemical_label)
        entities = []

        if hasattr(self.model, 'dimensions') and not self.model.dimensions:
            # the mandatory elements of Dimensionless model are grouped into a entities list
            specifier = self.model.specifier.parse_expression('specifier')
            value_phrase = value_element_plain()('value_phrase')
            entities.append(specifier)
            entities.append(value_phrase)

        elif hasattr(self.model, 'dimensions') and self.model.dimensions:
            # the mandatory elements of Quantity model are grouped into a entities list
            # print(self.model, self.model.dimensions)
            unit_element = Group(
                construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('units'))(
                'value_phrase')
            specifier = self.model.specifier.parse_expression('specifier') + Optional(lbrct) + Optional(W('/')) + Optional(
                unit_element) + Optional(rbrct)
            value_phrase = (value_element_plain()('value_phrase') + Optional(unit_element))
            entities.append(specifier)
            entities.append(value_phrase)

        elif hasattr(self.model, 'specifier'):
            # now we are parsing an element that has no value but some custom string
            # therefore, there will be no matching interpret function, all entities are custom except for the specifier
            specifier = self.model.specifier.parse_expression('specifier')
            entities.append(specifier)

        # the optional, user-defined, entities of the model are added, they are tagged with the name of the field
        for field in self.model.fields:
            if field not in ['raw_value', 'raw_units', 'value', 'units', 'error', 'specifier']:
                if self.model.__getattribute__(self.model, field).parse_expression is not None:
                    entities.append(self.model.__getattribute__(self.model, field).parse_expression(field))

        # the chem_name has to be parsed last in order to avoid a conflict with other elements of the model
        entities.append(chem_name)

        # logic for finding all the elements in any order
        combined_entities = create_entities_list(entities)
        root_phrase = OneOrMore(combined_entities + Optional(SkipTo(combined_entities)))('root_phrase')
        self._root_phrase = root_phrase
        self._specifier = self.model.specifier
        return root_phrase

    def interpret(self, result, start, end):
        requirements = True
        property_entities = {}

        if hasattr(self.model, 'dimensions') and not self.model.dimensions:
            # the specific entities of a DimensionlessModel are retrieved explicitly and packed into a dictionary
            raw_value = first(result.xpath('./value_phrase/value/text()'))
            value = self.extract_value(raw_value)
            error = self.extract_error(raw_value)
            property_entities.update({"raw_value": raw_value,
                                      "value": value,
                                      "error": error})

        elif hasattr(self.model, 'dimensions') and self.model.dimensions:
            # the specific entities of a QuantityModel are retrieved explicitly and packed into a dictionary
            raw_value = first(result.xpath('./value_phrase/value/text()'))
            raw_units = first(result.xpath('./value_phrase/units/text()'))
            value = self.extract_value(raw_value)
            error = self.extract_error(raw_value)
            units = self.extract_units(raw_units, strict=True)
            property_entities.update({"raw_value": raw_value,
                                      "raw_units": raw_units,
                                      "value": value,
                                      "error": error,
                                      "units": units})

        # custom entities defined in the particular model and 'specifier' are retrieved and added to the dictionary
        # 'compound' is handled separately below
        for field in self.model.fields:
            if field not in ['raw_value', 'raw_units', 'value', 'units', 'error', 'compound']:
                data = first(result.xpath('./' + field + '/text()'))
                # if field is required, but empty, the requirements have not been met
                if data is None \
                        and self.model.__getattribute__(self.model, field).required\
                        and not self.model.__getattribute__(self.model, field).contextual:
                    requirements = False
                property_entities.update({str(field): data})

        model_instance = self.model(**property_entities)

        if 'compound' in self.model.fields:
            cem_el = first(result.xpath('./cem'))
            compound = self.model.fields['compound'].model_class()

            if cem_el is not None:
                compound.names = cem_el.xpath('./name/text()')
                compound.labels = cem_el.xpath('./label/text()')
                model_instance.compound = compound
            elif cem_el is None \
                    and self.model.compound.required\
                    and not self.model.compound.contextual:
                requirements = False

        if requirements:
            yield model_instance


class AutoSentenceParser(BaseAutoParser, BaseSentenceParser):
    pass


class AutoTableParser(BaseAutoParser, BaseTableParser):
    """ Additions for automated parsing of tables"""
    pass


# def parse_table(model, category_table):
#     """
#     Parses a table. The model and the category table have to be provided.
#
#     :param model: subclass of BaseModel
#     :param category_table: list, output of TableDataExtractor
#     :return: Yields one result at a time
#     """
#     atp = AutoTableParser(model)
#     for cell in category_table:
#         if atp.parse_cell(cell):
#             for result in atp.parse_cell(cell):
#                 if result.serialize() != {}:
#                     yield result.serialize()



