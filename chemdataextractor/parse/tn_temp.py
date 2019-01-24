# -*- coding: utf-8 -*-
"""
Temporary test solution for the sort of parser that would be generated automatically by code for Tc.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

from .auto import BaseAutoParser, AutoTableParser, construct_unit_element, match_dimensions_of, value_element, value_element_plain, cem, chemical_label, lenient_chemical_label
from ..utils import first
from ..model.model import NeelTemperature, Compound
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group
from .common import lbrct, rbrct


class NeelTemperatureParser(BaseAutoParser):
    model = NeelTemperature

    @property
    def root(self):
        if self._specifier is self.model.specifier:
            return self._root_phrase
        unit_element = Group(construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('units'))('neeltemp')
        specifier = self.model.specifier('specifier')
        value_phrase = value_element(unit_element)('neeltemp')
        chem_name = (cem | chemical_label | lenient_chemical_label)
        entities = (value_phrase | specifier | chem_name)
        root_phrase = OneOrMore(entities | Any().hide())('neeltempphrase')
        self._root_phrase = root_phrase
        self._specifier = self.model.specifier
        return root_phrase

    def interpret(self, result, start, end):
        try:
            # print(etree.tostring(result))
            # Change this to MODEL_PHRASE?
            raw_value = first(result.xpath('./neeltemp/value/text()'))
            raw_units = first(result.xpath('./neeltemp/units/text()'))
            #TODO: How to add property_name to Compound automatically?
            compound = Compound(
                neel_temperature=[
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


class NeelTemperatureTableParser(AutoTableParser):
    model = NeelTemperature

    @property
    def root(self):
        # Not sure if this is valid, there must be a better way of doing this?
        if self._specifier is self.model.specifier:
            return self._root_phrase
        unit_element = Group(construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))('units'))('neeltemp')
        specifier = self.model.specifier('specifier') + Optional(lbrct) + Optional(W('/')) + Optional(unit_element) + Optional(rbrct)
        value_phrase = value_element_plain()('neeltemp')
        chem_name = (cem | chemical_label | lenient_chemical_label)
        entities = (value_phrase | specifier | chem_name)
        root_phrase = OneOrMore(entities | Any().hide())('neeltempphrase')
        self._root_phrase = root_phrase
        self._specifier = self.model.specifier
        return root_phrase

    def interpret(self, result, start, end):
        try:
            # print(etree.tostring(result))
            # Change this to MODEL_PHRASE?
            raw_value = first(result.xpath('./neeltemp/value/text()'))
            raw_units = first(result.xpath('./neeltemp/units/text()'))
            compound = Compound(
                neel_temperature=[
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
