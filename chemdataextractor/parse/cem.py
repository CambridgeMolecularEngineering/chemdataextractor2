# -*- coding: utf-8 -*-
"""
Chemical entity mention parser elements.
..codeauthor:: Matt Swain (mcs07@cam.ac.uk)
..codeauthor:: Callum Court (cc889@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractproperty, abstractmethod
import logging
import re
from lxml import etree

from .actions import join, fix_whitespace, merge
from .common import roman_numeral, cc, nnp, hyph, nns, nn, cd, ls, optdelim, rbrct, lbrct, sym, jj, hyphen, quote, \
    dt, delim
from .base import BaseSentenceParser, BaseTableParser
from .elements import I, R, W, T, ZeroOrMore, Optional, Not, Group, End, Start, OneOrMore, Any, SkipTo, Every
from .cem_factory import _CemFactory

log = logging.getLogger(__name__)


# The below are all just for backwards compatibility - may be worth removing at some point...
# See the cem_factory file for more information on what each of these mean
default_cem_factory = _CemFactory.with_default_configuration()

icm = default_cem_factory.icm
bcm = default_cem_factory.bcm
joining_characters = default_cem_factory.joining_characters
cm = default_cem_factory.cm

alphanumeric = default_cem_factory.alphanumeric
lenient_alphanumeric = default_cem_factory.lenient_alphanumeric

numeric = default_cem_factory.numeric
lenient_numeric = default_cem_factory.lenient_numeric

letter_number = default_cem_factory.letter_number
lenient_letter_number = default_cem_factory.lenient_letter_number

cm_blocklist = default_cem_factory.cm_blocklist

exclude_prefix = default_cem_factory.exclude_prefix

comma = default_cem_factory.comma
colon = default_cem_factory.colon

include_prefix = default_cem_factory.include_prefix

label_type = default_cem_factory.label_type

synthesis_of = default_cem_factory.synthesis_of

to_give = default_cem_factory.to_give

label_blocklist = default_cem_factory.label_blocklist

prefixed_label = default_cem_factory.prefixed_label

strict_chemical_label = default_cem_factory.strict_chemical_label

lenient_chemical_label = default_cem_factory.lenient_chemical_label

very_lenient_chemical_label = default_cem_factory.very_lenient_chemical_label

chemical_label = default_cem_factory.chemical_label

chemical_label_phrase1 = default_cem_factory.chemical_label_phrase1
chemical_label_phrase2 = default_cem_factory.chemical_label_phrase2
chemical_label_phrase3 = default_cem_factory.chemical_label_phrase3

doped_chemical_identifier = default_cem_factory.doped_chemical_identifier
doping_value = default_cem_factory.doping_value
doping_range = default_cem_factory.doping_range


doping_label_1 = default_cem_factory.doping_label_1
doping_label_2 = default_cem_factory.doping_label_2

doped_chemical_label = default_cem_factory.doped_chemical_label
chemical_label_phrase = default_cem_factory.chemical_label_phrase

informal_chemical_symbol = default_cem_factory.informal_chemical_symbol

metals = default_cem_factory.metals
transition_metals = default_cem_factory.transition_metals
lanthanides = default_cem_factory.lanthanides
ion_symbol = default_cem_factory.ion_symbol
other_symbol = default_cem_factory.other_symbol

informal_values = default_cem_factory.informal_values

informal_chemical_label_1 = default_cem_factory.informal_chemical_label_1
informal_chemical_label_2 = default_cem_factory.informal_chemical_label_2

informal_chemical_label = default_cem_factory.informal_chemical_label
chemical_label_phrase = default_cem_factory.chemical_label_phrase

element_name = default_cem_factory.element_name

element_symbol = default_cem_factory.element_symbol

registry_number = default_cem_factory.registry_number

amino_acid = default_cem_factory.amino_acid

amino_acid_name = default_cem_factory.amino_acid_name

formula = default_cem_factory.formula

solvent_formula = default_cem_factory.solvent_formula

nmr_solvent = default_cem_factory.nmr_solvent

other_solvent = default_cem_factory.other_solvent

solvent_name_options = default_cem_factory.solvent_name_options
solvent_name = default_cem_factory.solvent_name
chemical_name_blocklist = default_cem_factory.chemical_name_blocklist
proper_chemical_name_options = default_cem_factory.proper_chemical_name_options

mixture_component = default_cem_factory.mixture_component
mixture_phrase = default_cem_factory.mixture_phrase

chemical_name_options = default_cem_factory.chemical_name_options

chemical_name = default_cem_factory.chemical_name

likely_abbreviation = default_cem_factory.likely_abbreviation

lenient_name = default_cem_factory.lenient_name

label_name_cem = default_cem_factory.label_name_cem
labelled_as = default_cem_factory.labelled_as
optquote = default_cem_factory.optquote

name_with_optional_bracketed_label = default_cem_factory.name_with_optional_bracketed_label

label_before_name = default_cem_factory.label_before_name
lenient_name_with_bracketed_label = default_cem_factory.lenient_name_with_bracketed_label

name_with_comma_within = default_cem_factory.name_with_comma_within

name_with_doped_label = default_cem_factory.name_with_doped_label

name_with_informal_label = default_cem_factory.name_with_informal_label

cem = default_cem_factory.cem

cem_phrase = default_cem_factory.cem_phrase

r_equals = default_cem_factory.r_equals
of_table = default_cem_factory.of_table

bracketed_after_name = default_cem_factory.bracketed_after_name
comma_after_name = default_cem_factory.comma_after_name

compound_heading_ending = default_cem_factory.compound_heading_ending

# Section number, to allow at the start of a heading
section_no = default_cem_factory.section_no

compound_heading_style1 = default_cem_factory.compound_heading_style1
compound_heading_style2 = default_cem_factory.compound_heading_style2
compound_heading_style3 = default_cem_factory.compound_heading_style3
compound_heading_style4 = default_cem_factory.compound_heading_style4
compound_heading_style5 = default_cem_factory.compound_heading_style5
compound_heading_style6 = default_cem_factory.compound_heading_style6
# TODO: Capture label type in output

compound_heading_phrase = default_cem_factory.compound_heading_phrase

names_only = default_cem_factory.names_only

labels_only = default_cem_factory.labels_only

roles_only = default_cem_factory.roles_only


def standardize_role(role):
    """Convert role text into standardized form."""
    role = role.lower()
    if any(c in role for c in {'synthesis', 'give', 'yield', 'afford', 'product', 'preparation of'}):
        return 'product'
    return role


# TODO jm2111, Problems here! The parsers don't have a parse method anymore. Ruins parsing of captions.
class CompoundParser(BaseSentenceParser):
    """Chemical name possibly with an associated label."""
    _label = None
    _root_phrase = None

    @property
    def root(self):
        label = self.model.labels.parse_expression('labels')
        label_name_cem = (label + optdelim + chemical_name)('compound')

        label_before_name = Optional(synthesis_of | to_give) + label_type + optdelim + label_name_cem + ZeroOrMore(optdelim + cc + optdelim + label_name_cem)

        name_with_optional_bracketed_label = (Optional(synthesis_of | to_give) + chemical_name + Optional(lbrct + Optional(labelled_as + optquote) + (label) + optquote + rbrct))('compound')

        # Very lenient name and label match, with format like "name (Compound 3)"
        lenient_name_with_bracketed_label = (Start() + Optional(synthesis_of) + lenient_name + lbrct + label_type.hide() + label + rbrct)('compound')

        # Chemical name with a doped label after
        # name_with_doped_label = (chemical_name + OneOrMore(delim | I('with') | I('for')) + label)('compound')

        # Chemical name with an informal label after
        # name_with_informal_label = (chemical_name + Optional(R('compounds?')) + OneOrMore(delim | I('with') | I('for')) + informal_chemical_label)('compound')
        return Group(name_with_informal_label | name_with_doped_label | lenient_name_with_bracketed_label | label_before_name | name_with_comma_within | name_with_optional_bracketed_label)('cem_phrase')

    def interpret(self, result, start, end):
        # TODO: Parse label_type into label model object
        # print(etree.tostring(result))
        for cem_el in result.xpath('./compound'):
            c = self.model(
                names=cem_el.xpath('./names/text()'),
                labels=cem_el.xpath('./labels/text()'),
                roles=[standardize_role(r) for r in cem_el.xpath('./roles/text()')]
            )
            c.record_method = self.__class__.__name__
            yield c


class ChemicalLabelParser(BaseSentenceParser):
    """Chemical label occurrences with no associated name."""
    _label = None
    _root_phrase = None

    @property
    def root(self):
        label = self.model.labels.parse_expression('labels')
        if self._label is label:
            return self._root_phrase
        self._root_phrase = (chemical_label_phrase | Group(label)('chemical_label_phrase'))
        self._label = label
        return self._root_phrase

    def interpret(self, result, start, end):
        # print(etree.tostring(result))
        roles = [standardize_role(r) for r in result.xpath('./roles/text()')]
        for label in result.xpath('./labels/text()'):
            yield self.model(labels=[label], roles=roles)


class CompoundHeadingParser(BaseSentenceParser):
    """Better matching of abbreviated names in dedicated compound headings."""

    root = compound_heading_phrase
    parse_full_sentence = True

    def interpret(self, result, start, end):
        roles = [standardize_role(r) for r in result.xpath('./roles/text()')]
        labels = result.xpath('./labels/text()')
        if len(labels) > 1:
            for label in labels:
                yield self.model(labels=[label], roles=roles)
            for name in result.xpath('./names/text()'):
                yield self.model(names=[name], roles=roles)
        else:
            yield self.model(
                names=result.xpath('./names/text()'),
                labels=labels,
                roles=roles
            )


class CompoundTableParser(BaseTableParser):
    entities = (cem | chemical_label | lenient_chemical_label) | ((I('Formula') | I('Compound')).add_action(join))('specifier')
    root = OneOrMore(entities + Optional(SkipTo(entities)))('root_phrase')

    @property
    def root(self):
        # is always found, our models currently rely on the compound
        chem_name = (cem | chemical_label | lenient_chemical_label)
        compound_model = self.model
        labels = compound_model.labels.parse_expression('labels')
        entities = [labels]

        specifier = (I('Formula') | I('Compound') | I('Alloy')).add_action(join)('specifier')
        entities.append(specifier)

        # the optional, user-defined, entities of the model are added, they are tagged with the name of the field
        for field in self.model.fields:
            if field not in ['raw_value', 'raw_units', 'value', 'units', 'error', 'specifier']:
                if self.model.__getattribute__(self.model, field).parse_expression is not None:
                    entities.append(self.model.__getattribute__(self.model, field).parse_expression(field))

        # the chem_name has to be parsed last in order to avoid a conflict with other elements of the model
        entities.append(chem_name)

        # logic for finding all the elements in any order

        combined_entities = entities[0]
        for entity in entities[1:]:
            combined_entities = (combined_entities | entity)
        root_phrase = OneOrMore(combined_entities + Optional(SkipTo(combined_entities)))('root_phrase')
        self._root_phrase = root_phrase
        self._specifier = self.model.specifier
        return root_phrase

    def interpret(self, result, start, end):
        # TODO: Parse label_type into label model object
        if result.xpath('./specifier/text()') and \
        (result.xpath('./names/names/text()') or result.xpath('./labels/text()')):
            c = self.model(
                names=result.xpath('./names/names/text()'),
                labels=result.xpath('./labels/text()'),
                roles=[standardize_role(r) for r in result.xpath('./roles/text()')]
            )
            if c is not None:
                c.record_method = self.__class__.__name__
                yield c
