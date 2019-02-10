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
from ..model.units.dimension import Dimensionless
from .actions import merge, join
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group, SkipTo, Or
from ..utils import first
from .quantity import QuantityParser, magnitudes_dict, value_element, extract_units, value_element_plain
from ..model import Compound
from ..doc.text import Sentence, Cell

from ..model.units.quantity_model import QuantityModel, DimensionlessModel, BaseModel
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


class BaseAutoParser(QuantityParser):
    model = None
    _specifier = None
    _root_phrase = None

    def __init__(self, model):
        super(BaseAutoParser, self).__init__()
        self.model = model
        if hasattr(self.model, 'dimensions'):
            self.dimensions = self.model.dimensions

    @property
    def root(self):
        if self._specifier is self.model.specifier:
            return self._root_phrase

        # is always found, our models currently rely on the compound
        chem_name = (cem | chemical_label | lenient_chemical_label)
        entities = []

        if issubclass(self.model, DimensionlessModel):
            # the mandatory elements of Dimensionless model are grouped into a entities list
            specifier = self.model.specifier('specifier')
            value_phrase = value_element_plain()('value_phrase')
            entities.append(specifier)
            entities.append(value_phrase)

        if issubclass(self.model, QuantityModel) and not issubclass(self.model, DimensionlessModel):
            # the mandatory elements of Quantity model are grouped into a entities list
            unit_element = Group(
                construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('units'))(
                'value_phrase')
            specifier = self.model.specifier('specifier') + Optional(lbrct) + Optional(W('/')) + Optional(
                unit_element) + Optional(rbrct)
            value_phrase = value_element_plain()('value_phrase')
            entities.append(specifier)
            entities.append(value_phrase)

        if issubclass(self.model, BaseModel) and not issubclass(self.model, QuantityModel):
            # now we are parsing an element that has no value but some custom string
            # therefore, there will be no matching interpret function, all entities are custom except for the specifier
            specifier = self.model.specifier('specifier')
            entities.append(specifier)

        # the optional, user-defined, entities of the model are added, they are tagged with the name of the field
        for field in self.model.fields:
            if field not in ['raw_value', 'raw_units', 'value', 'units', 'error']:
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
        try:
            requirements = True
            property_entities = {}
            # print(etree.tostring(result))

            # specifier is mandatory
            specifier = first(result.xpath('./specifier/text()'))
            if specifier is None:
                requirements = False

            if issubclass(self.model, DimensionlessModel):
                # the specific entities of a DimensionlessModel are retrieved explicitly and packed into a dictionary
                raw_value = first(result.xpath('./value_phrase/value/text()'))
                value = self.extract_value(raw_value)
                error = self.extract_error(raw_value)
                property_entities.update({"raw_value": raw_value,
                                     "value": value,
                                     "error": error})

            if issubclass(self.model, QuantityModel) and not issubclass(self.model, DimensionlessModel):
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

            # custom entities defined in the particular model are retrieved and added to the dictionary
            for field in self.model.fields:
                if field not in ['raw_value', 'raw_units', 'value', 'units', 'error']:
                    data = first(result.xpath('./' + field + '/text()'))
                    # if field is required, but empty, the requirements have not been met
                    if self.model.__getattribute__(self.model, field).required and data is None:
                        requirements = False
                    property_entities.update({str(field): data})

            arg_dict = {self.model.__name__: [self.model(**property_entities)]}
            compound = Compound(**arg_dict)
            cem_el = first(result.xpath('./cem'))

            if cem_el is not None and requirements is not False:
                compound.names = cem_el.xpath('./name/text()')
                compound.labels = cem_el.xpath('./label/text()')
                yield compound

        except TypeError as e:
            # log.debug(e)
            # compound = Compound()
            pass
        except AttributeError as e:
            # For some cases of doing extract_units/extract_value/extract_error
            # compound = Compound()
            pass


class TableAutoParser(BaseAutoParser):
    """ Additions for automated parsing of tables"""
    def parse(self, cell):
        string = cell[0] + ' '
        string += ' '.join(cell[1]) + ' '
        string += ' '.join(cell[2])
        sent = Cell(string)
        try:
            for result in self.root.scan(sent.tagged_tokens):
                for model in self.interpret(*result):
                    yield model
        except AttributeError as e:
            # model is not parsable
            pass


def parse_table(model, category_table):
    """
    Parses a table. The model and the category table have to be provided.

    :param model: subclass of BaseModel
    :param category_table: list, output of TableDataExtractor
    :return: Yields one result at a time
    """
    atp = TableAutoParser(model)
    for cell in category_table:
        if atp.parse(cell):
            for result in atp.parse(cell):
                if result.serialize() != {}:
                    yield result.serialize()



