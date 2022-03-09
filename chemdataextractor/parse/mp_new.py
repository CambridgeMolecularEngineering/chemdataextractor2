# -*- coding: utf-8 -*-
"""
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
from .actions import merge
from .quantity import value_element
from .base import BaseSentenceParser
from .elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore

log = logging.getLogger(__name__)

prefix = Optional(I('a')).hide() + (Optional(lbrct) + W('Tm') + Optional(rbrct) | R('^m\.?pt?\.?$', re.I) | I('melting') + Optional((I('point') | I('temperature') | I('range'))) | R('^m\.?$', re.I) + Optional(I('.')) + R('^pt?\.?$', re.I) + Optional(I('.'))).hide() + Optional(lbrct + W('Tm') + rbrct) + Optional(W('=') | I('of') | I('was') | I('is') | I('at')).hide() + Optional(I('in') + I('the') + I('range') + Optional(I('of')) | I('about')).hide()

delim = R('^[:;\.,]$')

# TODO: Consider allowing degree symbol to be optional. The prefix should be restrictive enough to stop false positives.
units = ((W('°') + Optional(R('^[CFK]\.?$'))) | W('K\.?') | W('°C'))('raw_units').add_action(merge)

mp = (prefix + Optional(delim).hide() + value_element(units))('mp')

bracket_any = lbrct + OneOrMore(Not(mp) + Not(rbrct) + Any()) + rbrct

solvent_phrase = (R('^(re)?crystalli[sz](ation|ed)$', re.I) + (I('with') | I('from')) + cem | solvent_name)
cem_mp_phrase = (Optional(solvent_phrase).hide() + Optional(cem) + Optional(I('having')).hide() + Optional(delim).hide() + Optional(bracket_any).hide() + Optional(delim).hide() + Optional(lbrct) + mp + Optional(rbrct))('mp_phrase')
to_give_mp_phrase = ((I('to') + (I('give') | I('afford') | I('yield') | I('obtain')) | I('affording') | I('afforded') | I('gave') | I('yielded')).hide() + Optional(dt).hide() + (cem | chemical_label | lenient_chemical_label) + ZeroOrMore(Not(mp) + Not(cem) + Any()).hide() + mp)('mp_phrase')
obtained_mp_phrase = ((cem | chemical_label) + (I('is') | I('are') | I('was')).hide() + (I('afforded') | I('obtained') | I('yielded')).hide() + ZeroOrMore(Not(mp) + Not(cem) + Any()).hide() + mp)('mp_phrase')

mp_phrase = cem_mp_phrase | to_give_mp_phrase | obtained_mp_phrase


class MpParser(BaseSentenceParser):
    """
    MpParser rewritten to extract values and errors.
    """
    root = mp_phrase
    trigger_phrase = prefix

    def interpret(self, result, start, end):
        log.debug(etree.tostring(result))
        try:
            compound = self.model.fields['compound'].model_class()
            raw_value = first(result.xpath('./mp/raw_value/text()'))
            raw_units = first(result.xpath('./mp/raw_units/text()'))
            melting_point = self.model(raw_value=raw_value,
                        raw_units=raw_units)
            cem_el = first(result.xpath('./compound'))
            if cem_el is not None:
                log.debug(etree.tostring(cem_el))
                melting_point.compound = compound
                melting_point.compound.names = cem_el.xpath('./names/text()')
                melting_point.compound.labels = cem_el.xpath('./labels/text()')
            log.debug(melting_point.serialize())
            yield melting_point
        except TypeError as e:
            log.debug(e)
