# -*- coding: utf-8 -*-
"""
Parser for automatic parsing, without user-written parsing rules.
Mainly used for tables.

Models must be constructed in a certain way for them to work optimally with autoparsers. Namely, they should have:

- A specifier field with an associated parse expression (Optional, only required if autoparsers are desired). These parse expressions will be updated automatically using forward-looking Interdependency Resolution if the updatable flag is set to True.
- These specifiers should also have required set to True so that spurious matches are not found.
- If applicable, a compound entity, named compound.

Any parse_expressions set in the model should have an added action to ensure that the results are a single word. An example would be to call add_action(join) on each parse expression.

.. codeauthor:: Taketomo Isazawa <ti250@cam.ac.uk>

.. codeauthor:: Juraj Mavračić <jm2111@cam.ac.uk>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import six
import copy

from .cem import cem, chemical_label, lenient_chemical_label
from .actions import merge, join
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group, SkipTo, Or
from ..utils import first
from .quantity import magnitudes_dict, value_element, extract_units, value_element_plain, lbrct, rbrct
from .base import BaseSentenceParser, BaseParser, BaseTableParser

import xml.etree.ElementTree as etree

log = logging.getLogger(__name__)


def construct_unit_element(dimensions):
    """
    Construct an element for detecting units for the dimensions given.
    Any magnitude modifiers (e.g. kilo) will be automatically handled.

    :param Dimension dimensions: The dimensions that the element produced will look for.
    :returns: An Element to look for units of given dimensions. If None or Dimensionless are passed in, returns None.
    :rtype: BaseParserElement or None
    """
    if not dimensions or not dimensions.units_dict:
        return None
    # Handle all the magnitudes
    units_regex = '^(('
    for element in magnitudes_dict.keys():
        units_regex += '(' + element.pattern + ')|'
    units_regex = units_regex[:-1]
    units_regex += ')?'
    units_regex += '('
    # Case where we have a token that's just brackets
    units_regex += '((\(|\[))|((\)|\]))|\-|'
    # Handle all the units
    for element in dimensions.units_dict:
        units_regex += '(' + element.pattern + ')|'
    units_regex += '(\/)'
    # Case when we have powers, or one or more units
    units_regex2 = units_regex + '|([\+\-–−]?\d+(\.\d+)?)'
    units_regex2 += '))+$'
    units_regex += '))+'
    units_regex += (units_regex2[1:-2] + '*')
    units_regex += '$'
    return (R(pattern=units_regex) + ZeroOrMore(R(pattern=units_regex) | R(pattern=units_regex2))).add_action(merge)


def construct_category_element(category_dict):
    """
    Construct an element for detecting categories.

    :param Category category: The Category to look for.
    :rtype: BaseParserElement or None
    """
    category_regex = '^'
    if not category_dict:
        return None
    # Handle all the units
    for element in category_dict:
        category_regex += '(' + element.pattern + ')|'
    category_regex = category_regex[:-1]
    category_regex += '$'
    return (R(pattern=category_regex))('raw_value').add_action(merge)


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
            log.debug(e)
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

    def interpret(self, result, start, end):
        # print(etree.tostring(result))
        if result is None:
            return
        requirements = True
        property_entities = {}
        log.debug(etree.tostring(result))
        # print(etree.tostring(result))

        if hasattr(self.model, 'dimensions') and not self.model.dimensions:
            # the specific entities of a DimensionlessModel are retrieved explicitly and packed into a dictionary
            raw_value = first(result.xpath('./raw_value/text()'))
            log.debug(raw_value)
            if not raw_value and self.model.fields['raw_value'].required and not self.model.fields['raw_value'].contextual:
                requirements = False
            if raw_value != 'NoValue':
                value = self.extract_value(raw_value)
            else:
                value = None
            error = self.extract_error(raw_value)
            property_entities.update({"raw_value": raw_value,
                                      "value": value,
                                      "error": error})

        elif hasattr(self.model, 'dimensions') and self.model.dimensions:
            # the specific entities of a QuantityModel are retrieved explicitly and packed into a dictionary
            # print(etree.tostring(result))
            raw_value = first(result.xpath('./raw_value/text()'))
            if not raw_value and self.model.fields['raw_value'].required and not self.model.fields['raw_value'].contextual:
                requirements = False
            raw_units = first(result.xpath('./raw_units/text()'))
            if raw_value != 'NoValue':
                value = self.extract_value(raw_value)
            else:
                value = None
            error = self.extract_error(raw_value)
            units = None
            try:
                units = self.extract_units(raw_units, strict=True)
            except TypeError as e:
                log.debug(e)

            property_entities.update({"raw_value": raw_value,
                                      "raw_units": raw_units,
                                      "value": value,
                                      "error": error,
                                      "units": units})

        for field_name, field in six.iteritems(self.model.fields):
            if field_name not in ['raw_value', 'raw_units', 'value', 'units', 'error']:
                try:
                    data = self._get_data(field_name, field, result)
                    if data is not None:
                        property_entities.update(data)
                # if field is required, but empty, the requirements have not been met
                except TypeError as e:
                    log.debug(self.model)
                    log.debug(e)
                    requirements = False

        model_instance = self.model(**property_entities)

        if requirements:
            # records the parser that was used to generate this record, can be used for evaluation
            model_instance.record_method = self.__class__.__name__
            yield model_instance

    def _get_data(self, field_name, field, result):
        if hasattr(field, 'model_class'):
            field_result = first(result.xpath('./' + field_name))
            if field_result is None and field.required and not field.contextual:
                raise TypeError('Could not find element for ' + str(field_name))
            elif field_result is None:
                return None
            field_data = {}
            for subfield_name, subfield in six.iteritems(field.model_class.fields):
                data = self._get_data(subfield_name, subfield, field_result)
                if data is not None:
                    field_data.update(data)
            field_object = field.model_class(**field_data)
            log.debug('Created for' + field_name)
            log.debug(field_object)
            return {field_name: field_object}
        elif hasattr(field, 'field'):
            # Case that we have listtype
            # Always only takes the first found one though
            field = field.field
            field_data = self._get_data(field_name, field, result)
            if field_data is not None:
                if field_data[field_name] is None:
                    return None
                field_data = [field_data[field_name]]
            elif field_data is None and field.required and not field.contextual:
                raise TypeError('Could not find element for ' + str(field_name))
            elif field_data is None:
                return None
            return {field_name: field_data}
        else:
            field_result = first(result.xpath('./' + field_name + '/text()'))
            if field_result is None and field.required and not field.contextual:
                raise TypeError('Could not find element for ' + str(field_name))
            return {field_name: field_result}


class AutoSentenceParser(BaseAutoParser, BaseSentenceParser):

    def __init__(self, lenient=False):
        super(AutoSentenceParser, self).__init__()
        self.lenient = lenient

    @property
    def root(self):
        # is always found, our models currently rely on the compound
        chem_name = (cem | chemical_label | lenient_chemical_label)
        compound_model = self.model.compound.model_class
        labels = compound_model.labels.parse_expression('labels')
        entities = [labels]

        if hasattr(self.model, 'dimensions') and not self.model.dimensions:
            # the mandatory elements of Dimensionless model are grouped into a entities list
            specifier = self.model.specifier.parse_expression('specifier')
            value_phrase = value_element_plain()
            entities.append(specifier)
            entities.append(value_phrase)

        elif hasattr(self.model, 'dimensions') and self.model.dimensions:
            # the mandatory elements of Quantity model are grouped into a entities list
            # print(self.model, self.model.dimensions)
            unit_element = Group(
                construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('raw_units'))
            specifier = self.model.specifier.parse_expression('specifier')
            if self.lenient:
                value_phrase = (value_element(unit_element) | value_element_plain())
            else:
                value_phrase = value_element(unit_element)

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
        return root_phrase


class AutoTableParser(BaseAutoParser, BaseTableParser):
    """ Additions for automated parsing of tables"""
    @property
    def root(self):
        # is always found, our models currently rely on the compound
        chem_name = (cem | chemical_label | lenient_chemical_label)
        compound_model = self.model.compound.model_class
        labels = compound_model.labels.parse_expression('labels')
        entities = [labels]
        no_value_element = W('NoValue')('raw_value')

        if hasattr(self.model, 'dimensions') and not self.model.dimensions:
            # the mandatory elements of Dimensionless model are grouped into a entities list
            specifier = self.model.specifier.parse_expression('specifier')
            value_phrase = value_element_plain() | no_value_element
            entities.append(specifier)
            entities.append(value_phrase)

        elif hasattr(self.model, 'dimensions') and self.model.dimensions:
            # the mandatory elements of Quantity model are grouped into a entities list
            # print(self.model, self.model.dimensions)
            unit_element = Group(
                construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('raw_units'))
            specifier = self.model.specifier.parse_expression('specifier') + Optional(W('/')) + Optional(
                unit_element)
            value_phrase = ((value_element_plain() | no_value_element) + Optional(unit_element))
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
        return root_phrase
