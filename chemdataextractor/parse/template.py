"""
Basic property parser template for Quantity Models
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
from lxml import etree
from .cem import cem, chemical_label, lenient_chemical_label, chemical_name
from .common import lbrct, dt, rbrct
from ..utils import first
from ..nlp.tokenize import ChemWordTokenizer, ChemSentenceTokenizer
from .actions import merge, join, fix_whitespace, flatten
from .base import BaseSentenceParser
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group, End
from .auto import construct_unit_element, match_dimensions_of, value_element, BaseAutoParser, construct_category_element
import six
log = logging.getLogger(__name__)

delim = R('^[:;\.,]$')


class QuantityModelTemplateParser(BaseAutoParser, BaseSentenceParser):
    """Template parser for QuantityModel-type structures

    Finds Cem, Specifier, Value and Units from single sentences

    Other entities are merged contextually
    """


    @property
    def specifier_phrase(self):
        """The model specifier"""
        return self.model.specifier.parse_expression('specifier')

    @property
    def value_phrase(self):
        """Value and units"""
        if hasattr(self.model, 'dimensions') and not self.model.dimensions:
            return value_element()
        elif hasattr(self.model, 'category') and self.model.category:
            return self.model.category.parse_expression('category')

        unit_element = Group(construct_unit_element(self.model.dimensions).with_condition(
            match_dimensions_of(self.model))('raw_units'))
        return value_element(unit_element)

    @property
    def cem_phrase(self):
        """CEM phrases"""
        return self.model.compound.model_class.parsers[0].root

    @property
    def prefix(self):
        """Specifier prefix phrase e.g. Tc equal to"""
        return (self.specifier_phrase
                  + OneOrMore(Not(self.cem_phrase | self.specifier_phrase | self.value_phrase) + Any().hide())
                  + Optional(I('values')).hide()
                  + Optional(delim).hide()
                  + Optional((I('varies') + I('from')) |
                             R('^increase(s|d)?') | I('falls') | I('reaches')).hide()
                  + Optional(I('steeply')).hide()
                  + Optional(I('recorded') | I('reported')).hide()
                  + Optional(I('of') | I('was') | I('is') | I('at') | I('near') |
                             I('above') | I('below') | I('with') | I('to') | I('were') | I('a')).hide()
                  + Optional(I('reported') | I('determined') |
                             I('estimated') | I('found') | I('occurs')).hide()
                  + Optional(I('temperatures')).hide()
                  + Optional(I('as') | (I('to') + I('be'))).hide()
                  + Optional(I('in') + I('the') + I('range')).hide()
                  + Optional(I('as') + I('high') + I('as'))
                  + Optional(I('ranging') + I('from')).hide()
                  + Optional(I('of')).hide()
                  + Optional(I('rather') | I('quite')).hide()
                  + Optional(I('high') | I('low') | I('maximum') | I('minimum')).hide()
                  + Optional(I('the')).hide()
                  + Optional(delim | lbrct | rbrct)
                  + Optional(I('of') | I('about') | I('approximately') | I('typically') | I('ca.') | I('around') | I('at') | I('above') | I('below') | I('high') | I('low')
                             | ((I('higher') | I('lower') | I('more') | I('less')) + I('than')) | I('order') | (I('for') + I('instance')) | (I('up') + I('to')) | I('reaching') | I('value')).hide()
                  + Optional(I('a') | I('an') | I('as')).hide()
                  + Optional(I('maximum')).hide()
                  + Optional(I('of')).hide()
                  + ZeroOrMore(lbrct | delim | rbrct)
                  + Optional(self.specifier_phrase)
                  + Optional(I('of')).hide()
                  + Optional(I('the')).hide()
                  + Optional(I('order')).hide()
                  + Optional((I('up') | I('equal')) + I('to')).hide()
                  + Optional(I('of')).hide()
                  + ZeroOrMore(lbrct | delim | rbrct)
                  + Optional(W('=') | W('~') | W('≈') |
                             W('≃') | W('>') | W('<')).hide()
                  + ZeroOrMore(lbrct | delim | rbrct).hide()).add_action(join)

    @property
    def specifier_and_value(self):
        """Specifier and value + units"""
        return Group(self.prefix + self.value_phrase)

    @property
    def cem_before_specifier_and_value_phrase(self):
        """Phrases ordered CEM, Specifier, Value, Unit"""
        return  (
            self.cem_phrase
            + OneOrMore(Not(self.cem_phrase | self.specifier_phrase | self.specifier_and_value) + Any().hide())
            + self.specifier_and_value)('root_phrase')

    @property
    def specifier_before_cem_and_value_phrase(self):
        return (
            self.specifier_phrase
            + OneOrMore(Not(self.cem_phrase | self.specifier_phrase | self.value_phrase) + Any().hide())
            + self.cem_phrase
            + OneOrMore(Not(self.cem_phrase | self.specifier_phrase | self.value_phrase) + Any().hide())
            + Optional(self.prefix)
            + self.value_phrase)('root_phrase')

    @property
    def cem_after_specifier_and_value_phrase(self):
        """Phrases ordered specifier, value, unit, CEM"""
        return (
            self.specifier_and_value
            + OneOrMore(Not(self.cem_phrase | self.specifier_phrase | self.value_phrase) + Any().hide())
            + self.cem_phrase)('root_phrase')

    @property
    def value_specifier_cem_phrase(self):
        """Phrases ordered value unit specifier cem"""
        return (self.value_phrase
            + Optional(delim | lbrct | rbrct)
            + Optional(I('which') | I('there')).hide()
            + Optional(I('likely') | I('close') |
                        (I('can') + I('be'))).hide()
            + Optional(I('corresponds') |
                        I('associated') | I('corresponding')).hide()
            + Optional(I('to') | I('with') | I('is')).hide()
            + Optional(I('the') | I('a')).hide()
            + Optional(I('transition')).hide()
            + Optional(I('to').hide())
            + Optional(I('a')).hide()
            + self.specifier_phrase
            + Not(I('='))
            + Not(self.value_phrase)
            + Optional(I('of') | I('in')).hide()
            + self.cem_phrase)('root_phrase')

    @property
    def root(self):
        """Root Phrases"""
        root_phrase = Group(self.specifier_before_cem_and_value_phrase | self.cem_after_specifier_and_value_phrase | self.value_specifier_cem_phrase | self.cem_before_specifier_and_value_phrase | Group(self.specifier_and_value)('root_phrase'))
        return root_phrase

class MultiQuantityModelTemplateParser(BaseAutoParser, BaseSentenceParser):
    """Template for parsing sentences that contain nested or chained entities

        MULTIPLE ENTITY PHRASES

        1) Single compound, multiple specifiers, multiple phase transitions e.g. BiFeO3 has TC = 1093 K and TN = 640 K
        2) single compound, single specifier, multiple transitions e.g. BiFeO3 shows magnetic transitions at 1093 and 640 K

        3) multiple compounds, single specifier, multiple transitions e.g. TC in BiFeO3 and LaFeO3 of 640 and 750 K
        4) multiple compounds, single specifier, single transition e.g. TC of 640 K in BifEO3, LaFeO3 and MnO

        5) multiple compounds, multiple specifiers, multiple transitions e.g. BiFeO3 and LaFeO3 have Tc = 640 K and TN = 750 K respectively

    Arguments:
        BaseAutoParser {[type]} -- [description]
        BaseSentenceParser {[type]} -- [description]
    """
    @property
    def specifier_phrase(self):
        """Specifier Phrase"""
        return self.model.specifier.parse_expression('specifier')

    @property
    def prefix(self):
        """Specifier and prefix"""
        return (self.specifier_phrase
                  + Optional(I('values')).hide()
                  + Optional(delim).hide()
                  + Optional((I('varies') + I('from')) |
                             R('^increase(s|d)?') | I('falls') | I('reaches')).hide()
                  + Optional(I('steeply')).hide()
                  + Optional(I('recorded') | I('reported')).hide()
                  + Optional(I('of') | I('was') | I('is') | I('at') | I('near') |
                             I('above') | I('below') | I('with') | I('to') | I('were') | I('a')).hide()
                  + Optional(I('reported') | I('determined') |
                             I('estimated') | I('found') | I('occurs')).hide()
                  + Optional(I('temperatures')).hide()
                  + Optional(I('as') | (I('to') + I('be'))).hide()
                  + Optional(I('in') + I('the') + I('range')).hide()
                  + Optional(I('as') + I('high') + I('as'))
                  + Optional(I('ranging') + I('from')).hide()
                  + Optional(I('of')).hide()
                  + Optional(I('rather') | I('quite')).hide()
                  + Optional(I('high') | I('low') | I('maximum') | I('minimum')).hide()
                  + Optional(I('the')).hide()
                  + Optional(delim | lbrct | rbrct)
                  + Optional(I('of') | I('about') | I('approximately') | I('typically') | I('ca.') | I('around') | I('at') | I('above') | I('below') | I('high') | I('low')
                             | ((I('higher') | I('lower') | I('more') | I('less')) + I('than')) | I('order') | (I('for') + I('instance')) | (I('up') + I('to')) | I('reaching') | I('value')).hide()
                  + Optional(I('a') | I('an') | I('as')).hide()
                  + Optional(I('maximum')).hide()
                  + Optional(I('of')).hide()
                  + ZeroOrMore(lbrct | delim | rbrct)
                  + Optional(self.specifier_phrase)
                  + Optional(I('of')).hide()
                  + Optional(I('the')).hide()
                  + Optional(I('order')).hide()
                  + Optional((I('up') | I('equal')) + I('to')).hide()
                  + Optional(I('of')).hide()
                  + ZeroOrMore(lbrct | delim | rbrct)
                  + Optional(W('=') | W('~') | W('≈') |
                             W('≃') | W('>') | W('<')).hide()
                  + ZeroOrMore(lbrct | delim | rbrct).hide()).add_action(join)

    @property
    def single_cem(self):
        """Any cem"""
        return Group(cem | chemical_label | Group(chemical_name)('compound'))

    @property
    def unit(self):
        """Unit element"""
        return Group(construct_unit_element(self.model.dimensions).with_condition(
            match_dimensions_of(self.model))('raw_units'))

    @property
    def value_with_optional_unit(self):
        """Value possibly followed by a unit"""
        if hasattr(self.model, 'dimensions') and not self.model.dimensions:
            return value_element()
        elif hasattr(self.model, 'category') and self.model.category:
            return self.model.category.parse_expression('category')
        value = value_element()
        return Group(value + Optional(self.unit))

    @property
    def value_phrase(self):
        """Value with unit"""
        if hasattr(self.model, 'dimensions') and not self.model.dimensions:
            return value_element()
        elif hasattr(self.model, 'category') and self.model.category:
            return self.model.category.parse_expression('category')
        return value_element(self.unit)

    @property
    def list_of_values(self):
        """List of values with either multiple units or one at the end"""
        # option 1: single unit at the end
        option_1 = Group(self.value_with_optional_unit
                         + Optional(OneOrMore(delim.hide() + self.value_with_optional_unit))
                         + Optional(delim).hide()
                         + (I('and') | I('or')).hide()
                         + Optional(delim).hide()
                         + self.value_phrase)('value_list')
        # option 2: Multiple units
        option_2 = (self.value_phrase
                    + Optional(OneOrMore(delim.hide() + self.value_phrase))
                    + Optional(delim).hide()
                    + (I('and') | I('or') | delim).hide()
                    + self.value_phrase)('value_list')
        return (option_1 | option_2)

    @property
    def list_of_cems(self):
        """List of cems e.g. cem1, cem2, cem3 and cem4"""
        return Group(self.single_cem
                + Optional(lbrct + R('^\d+$') + rbrct).hide()
                + ZeroOrMore(delim.hide() | self.single_cem | R('^\d+$'))
                + (I('and') | I('or')).hide()
                + self.single_cem
                + Optional(lbrct + R('^\d+$') + rbrct).hide()
                + Optional(I('compounds') | I('samples')))('cem_list')

    @property
    def single_specifier_and_value_with_optional_unit(self):
        """Specifier plus value and possible unit"""
        return Group(self.prefix + self.value_with_optional_unit)('property')

    @property
    def single_specifier_and_value(self):
        """Specifier value and unit"""
        return Group(self.prefix + self.value_phrase)('property')

    @property
    def list_of_properties(self):
        """List of specifiers and units"""
        return Group(Optional(lbrct).hide()
                             + self.single_specifier_and_value_with_optional_unit
                             + (I('and') | delim | (I('that') + I('exhibits'))).hide()
                             + self.single_specifier_and_value
                             + Optional(rbrct).hide())('property_list')

    @property
    def multi_entity_phrase_1(self):
        """Single compound, multiple specifiers, values
         e.g. BiFeO3 has TC1 = 1093 K and Tc2 = 640 K
        """
        return Group(self.single_cem
                         + OneOrMore(Not(self.single_cem | self.specifier_phrase | self.value_phrase) + Any().hide())
                         + self.list_of_properties)('multi_entity_phrase_1')

    @property
    def multi_entity_phrase_2(self):
        """single compound, single specifier, multiple transitions
        e.g. BiFeO3 shows magnetic transitions at 1093 and 640 K
        """
        return Group(self.single_cem
                         + OneOrMore(Not(self.single_cem | self.specifier_phrase | self.value_phrase) + Any().hide())
                         + self.specifier_phrase
                         + OneOrMore(Not(self.single_cem | self.specifier_phrase | self.value_phrase) + Any().hide())
                         + self.list_of_values
                         + Optional(delim).hide()
                         + Optional(I('respectively')))('multi_entity_phrase_2')

    @property
    def multi_entity_phrase_3a(self):
        """multiple compounds, single specifier, multiple transitions cems first
        e.g. TC in BiFeO3 and LaFeO3 of 640 and 750 K
        """
        return Group(Optional(self.specifier_phrase)
                    + Optional(I('in') | I('for')).hide()
                    + self.list_of_cems
                    + OneOrMore(Not(self.single_cem | self.specifier_phrase | self.value_phrase) + Any().hide())
                    + self.prefix
                    + self.list_of_values
                    + Optional(delim.hide() + I('respectively').hide()))('multi_entity_phrase_3')

    @property
    def multi_entity_phrase_3b(self):
        """multiple compounds, single specifier, multiple transitions cems last
        e.g. Tc = 750 and 640 K in LaFeO3 and BiFeO3, respectivel
        """
        return Group(self.prefix
                          + self.list_of_values
                          + Optional(I('in') | I('for'))
                          + self.list_of_cems
                          + Optional(delim + I('respectively')))('multi_entity_phrase_3')

    @property
    def multi_entity_phrase_3c(self):
        """multiple compounds, single specifier, multiple transitions cems last
        e.g. curie temperatures from 100 K in MnO to 300 K in NiO
        """
        return Group(self.single_specifier_and_value
                          + Optional(I('for') | I('in')).hide()
                          + self.single_cem
                          + (Optional(I('up')) + I('to')).hide()
                          + self.value_phrase
                          + Optional(I('in') | I('for')).hide()
                          + self.single_cem)('multi_entity_phrase_3')

    @property
    def multi_entity_phrase_3(self):
        """Combined phrases of type 3"""
        return Group(self.multi_entity_phrase_3a | self.multi_entity_phrase_3b | self.multi_entity_phrase_3c)

    @property
    def multi_entity_phrase_4a(self):
        """multiple compounds, single specifier, single transition
        e.g. TC of 640 K in BifEO3, LaFeO3 and MnO

        """
        return Group(self.single_specifier_and_value
                          + OneOrMore(Not(self.single_cem | self.specifier_phrase | self.value_phrase) + Any().hide())
                          + self.list_of_cems)('multi_entity_phrase_4')

    @property
    def multi_entity_phrase_4b(self):
        """Cems first"""
        return Group(self.list_of_cems
                    + OneOrMore(Not(self.single_cem | self.specifier_phrase | self.value_phrase) + Any().hide())
                    + self.single_specifier_and_value)('multi_entity_phrase_4')

    @property
    def multi_entity_phrase_4(self):
        return Group(self.multi_entity_phrase_4a | self.multi_entity_phrase_4b)

    @property
    def root(self):
        return (self.multi_entity_phrase_1 | self.multi_entity_phrase_2 | self.multi_entity_phrase_3 | self.multi_entity_phrase_4)

    def interpret(self, result, start, end):
        if result.tag == 'multi_entity_phrase_1':
            for model in self.interpret_multi_entity_1(result, start, end):
                # records the parser that was used to generate this record, can be used for evaluation
                model.record_method = self.__class__.__name__
                yield model
        elif result.tag == 'multi_entity_phrase_2':
            for model in self.interpret_multi_entity_2(result, start, end):
                model.record_method = self.__class__.__name__
                yield model
        elif result.tag == 'multi_entity_phrase_3':
            for model in self.interpret_multi_entity_3(result, start, end):
                model.record_method = self.__class__.__name__
                yield model
        elif result.tag == 'multi_entity_phrase_4':
            for model in self.interpret_multi_entity_4(result, start, end):
                model.record_method = self.__class__.__name__
                yield model
        else:
            yield None

    def interpret_multi_entity_1(self, result, start, end):
        """Interpret phrases that have a single CEM and multiple values with multiple specifiers
        """
        if result is None:
            return

        cem_el = first(result.xpath('./compound'))

        if cem_el is None:
            yield None

        property_list = first(result.xpath('./property_list'))
        if property_list is None:
            yield None

        c = self.model.compound.model_class()
        # add names and labels
        c.names = cem_el.xpath('./names/text()')
        c.labels = cem_el.xpath('./labels/text()')

        properties = property_list.xpath('./property')
        last_unit = None
        for pt in properties[::-1]:  # Reverse order to make sure we get a unit
            requirements = True
            specifier = first(pt.xpath('./specifier/text()'))
            raw_value = first(pt.xpath('./raw_value/text()'))
            raw_units = first(pt.xpath('./raw_units/text()'))
            if not raw_units:
                raw_units = last_unit
            else:
                last_unit = raw_units

            value = self.extract_value(raw_value)
            error = self.extract_error(raw_value)
            units = None
            try:
                units = self.extract_units(raw_units, strict=True)
            except TypeError as e:
                requirements=False
                log.debug(e)

            property_entities = {
                'specifier': specifier,
                'raw_value': raw_value,
                'raw_units': raw_units,
                'error': error,
                'value': value,
                'units': units,
                'compound': c}

            model_instance = self.model(**property_entities)
            if requirements:
                model_instance.record_method = self.__class__.__name__
                yield model_instance

    def interpret_multi_entity_2(self, result, start, end):
        """single compound, single specifier, multiple transitions e.g. BiFeO3 shows magnetic transitions at 1093 and 640 K
        """
        if result is None:
            return
        cem_el = first(result.xpath('./compound'))

        if cem_el is None:
            yield None
        specifier = first(result.xpath('./specifier/text()'))
        if specifier is None:
            yield None

        value_list = first(result.xpath('./value_list'))

        if value_list is None:
            yield None

        c = self.model.compound.model_class()
        # add names and labels
        c.names = cem_el.xpath('./names/text()')
        c.labels = cem_el.xpath('./labels/text()')

        raw_values_list = value_list.xpath('./raw_value')
        raw_units_list = value_list.xpath('./raw_units')

        last_unit = None
        for i, v in enumerate(raw_values_list[::-1]):  # Reverse order to make sure we get a unit
            raw_value = first(v.xpath('./text()'))
            requirements = True
            try:
                raw_units = first(raw_units_list[::-1][i].xpath('./text()'))
                last_unit = raw_units
            except IndexError:
                if last_unit:
                    raw_units = last_unit
                else:
                    requirements = False

            value = self.extract_value(raw_value)
            error = self.extract_error(raw_value)
            units = None
            try:
                units = self.extract_units(raw_units, strict=True)
            except TypeError as e:
                requirements=False
                log.debug(e)

            property_entities = {
                'specifier': specifier,
                'raw_value': raw_value,
                'raw_units': raw_units,
                'error': error,
                'value': value,
                'units': units,
                'compound': c}

            model_instance = self.model(**property_entities)
            if requirements:
                model_instance.record_method = self.__class__.__name__
                yield model_instance

    def interpret_multi_entity_3(self, result, start, end):
        """interpret multiple compounds, single specifier, multiple transitions"""
        if result is None:
            return

        cem_list = first(result.xpath('./cem_list'))

        if cem_list is None:
            yield None

        specifier = first(result.xpath('./specifier/text()'))

        if specifier is None:
            yield None

        value_list = first(result.xpath('./value_list'))

        if value_list is None:
            yield None

        raw_values_list = value_list.xpath('./raw_value')
        raw_units_list = value_list.xpath('./raw_units')

        last_unit = None
        for i, v in enumerate(raw_values_list[::-1]):  # Reverse order to make sure we get a unit

            raw_value = first(v.xpath('./text()'))
            requirements = True
            try:
                raw_units = first(raw_units_list[::-1][i].xpath('./text()'))
                last_unit = raw_units
            except IndexError:
                if last_unit:
                    raw_units = last_unit
                else:
                    requirements = False
            c = None
            try:
                compound = cem_list[::-1][i]
                c = self.model.compound.model_class(
                    names=compound.xpath('./names/text()',
                    labels=compound.xpath('./labels/text()')))
            except Exception:
                requirements = False

            value = self.extract_value(raw_value)
            error = self.extract_error(raw_value)
            units = None
            try:
                units = self.extract_units(raw_units, strict=True)
            except TypeError as e:
                requirements=False
                log.debug(e)

            property_entities = {
                'specifier': specifier,
                'raw_value': raw_value,
                'raw_units': raw_units,
                'error': error,
                'value': value,
                'units': units,
                'compound': c}

            model_instance = self.model(**property_entities)
            if requirements:
                model_instance.record_method = self.__class__.__name__
                yield model_instance

    def interpret_multi_entity_4(self, result, start, end):
        """interpret multiple compounds, single specifier, single transition"""
        if result is None:
            return
        requirements = True

        cem_list = first(result.xpath('./cem_list'))

        if cem_list is None:
            yield None

        specifier = first(result.xpath('./property/specifier/text()'))
        raw_value = first(result.xpath('./property/raw_value/text()'))
        raw_units = first(result.xpath('./property/raw_units/text()'))

        if specifier is None:
            yield None

        value = self.extract_value(raw_value)
        error = self.extract_error(raw_value)
        units = None
        try:
            units = self.extract_units(raw_units, strict=True)
        except TypeError as e:
            requirements=False
            log.debug(e)

        for cem in cem_list:  # Reverse order to make sure we get a unit
            c = None
            try:
                c = self.model.compound.model_class(
                    names=cem.xpath('./names/text()',
                    labels=cem.xpath('./labels/text()')))
            except Exception:
                requirements = False

            property_entities = {
                'specifier': specifier,
                'raw_value': raw_value,
                'raw_units': raw_units,
                'error': error,
                'value': value,
                'units': units,
                'compound': c}

            model_instance = self.model(**property_entities)
            if requirements:
                model_instance.record_method = self.__class__.__name__
                yield model_instance




