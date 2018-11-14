# -*- coding: utf-8 -*-
"""
chemdataextractor.parse.mp_new
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Melting Point parser using the QuantityParser framework

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re

from lxml import etree

from .cem import cem, chemical_label, lenient_chemical_label, solvent_name
from .common import lbrct, dt, rbrct
from ..utils import first
from ..physicalmodels import Compound, MeltingPoint
from ..units.temperatures import Temperature
from .actions import merge, join
from .quantity import QuantityParser, value
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore

log = logging.getLogger(__name__)

prefix = Optional(I('a')).hide() + (Optional(lbrct) + W('Tm') + Optional(rbrct) | R('^m\.?pt?\.?$', re.I) | I('melting') + Optional((I('point') | I('temperature') | I('range'))) | R('^m\.?$', re.I) + R('^pt?\.?$', re.I)).hide() + Optional(lbrct + W('Tm') + rbrct) + Optional(W('=') | I('of') | I('was') | I('is') | I('at')).hide() + Optional(I('in') + I('the') + I('range') + Optional(I('of')) | I('about')).hide()

delim = R('^[:;\.,]$')

# TODO: Consider allowing degree symbol to be optional. The prefix should be restrictive enough to stop false positives.
units = ((W('°') + Optional(R('^[CFK]\.?$'))) | W('K\.?'))('units').add_action(merge)

mp = (prefix + Optional(delim).hide() + value(units))('mp')

bracket_any = lbrct + OneOrMore(Not(mp) + Not(rbrct) + Any()) + rbrct

solvent_phrase = (R('^(re)?crystalli[sz](ation|ed)$', re.I) + (I('with') | I('from')) + cem | solvent_name)
cem_mp_phrase = (Optional(solvent_phrase).hide() + Optional(cem) + Optional(I('having')).hide() + Optional(delim).hide() + Optional(bracket_any).hide() + Optional(delim).hide() + Optional(lbrct) + mp + Optional(rbrct))('mp_phrase')
to_give_mp_phrase = ((I('to') + (I('give') | I('afford') | I('yield') | I('obtain')) | I('affording') | I('afforded') | I('gave') | I('yielded')).hide() + Optional(dt).hide() + (cem | chemical_label | lenient_chemical_label) + ZeroOrMore(Not(mp) + Not(cem) + Any()).hide() + mp)('mp_phrase')
obtained_mp_phrase = ((cem | chemical_label) + (I('is') | I('are') | I('was')).hide() + (I('afforded') | I('obtained') | I('yielded')).hide() + ZeroOrMore(Not(mp) + Not(cem) + Any()).hide() + mp)('mp_phrase')

mp_phrase = cem_mp_phrase | to_give_mp_phrase | obtained_mp_phrase


class MpParser(QuantityParser):
    """
    MpParser rewritten to be based on QuantityParser
    """
    root = mp_phrase
    dimensions = Temperature()

    def interpret(self, result, start, end):
        try:
            units = self.extract_units(first(result.xpath('./mp/units/text()')), strict=True)
            compound = Compound(
                melting_points=[
                    MeltingPoint(
                        value=self.extract_value(first(result.xpath('./mp/value/text()'))),
                        units=units
                    )
                ]
            )
        except TypeError as e:
            log.debug(e)
            compound = Compound()
        cem_el = first(result.xpath('./cem'))
        if cem_el is not None:
            compound.names = cem_el.xpath('./name/text()')
            compound.labels = cem_el.xpath('./label/text()')
        yield compound
