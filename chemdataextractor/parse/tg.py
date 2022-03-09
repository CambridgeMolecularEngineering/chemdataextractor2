# -*- coding: utf-8 -*-
"""
Glass transition temperature parser.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re

from .cem import cem, chemical_label, lenient_chemical_label, solvent_name
from .quantity import value_element
from .common import lbrct, dt, rbrct, hyphen
from ..utils import first
from .actions import merge, join
from .base import BaseParser
from .elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore

log = logging.getLogger(__name__)


prefix = (Optional(I('a')).hide()
          + (Optional(lbrct) + W('Tg') + Optional(rbrct) | I('glass') + Optional(I('transition')) + Optional((I('temperature') | I('range') | (I('temp') + I('.')))) | W('transition') + Optional((I('temperature') | I('range') | I('temp.')))).hide()
          + Optional(lbrct + W('Tg') + rbrct)
          + Optional(W('=') | I('of') | I('was') | I('is') | I('at')).hide()
          + Optional(I('in') + I('the') + I('range') + Optional(I('of')) | I('about') | ('around') | I('ca') | I('ca.')).hide())


delim = R('^[:;\.,]$')

# TODO: Consider allowing degree symbol to be optional. The prefix should be restrictive enough to stop false positives.
units = (W('°') + Optional(R('^[CFK]\.?$')) | W('K\.?') | W('°C'))('units').add_action(merge)

value = value_element()(None)
temp_range = (Optional(R('^[\-–−]$')) + value)('value').add_action(merge)
temp_value = value('value').add_action(merge)
temp = Optional(lbrct).hide() + (temp_range | temp_value)('value') + Optional(rbrct).hide()

tg = (prefix + Optional(delim).hide() + temp + units)('tg')

bracket_any = lbrct + OneOrMore(Not(tg) + Not(rbrct) + Any()) + rbrct

cem_tg_phrase = (Optional(cem) + Optional(I('having')).hide() + Optional(delim).hide() + Optional(bracket_any).hide() + Optional(delim).hide() + Optional(lbrct) + tg + Optional(rbrct))('tg_phrase')

obtained_tg_phrase = ((cem | chemical_label) + (I('is') | I('are') | I('was')).hide() + (I('measured') | I('obtained') | I('yielded')).hide() + ZeroOrMore(Not(tg) + Not(cem) + Any()).hide() + tg)('tg_phrase')

tg_phrase = cem_tg_phrase | obtained_tg_phrase


class TgParser(BaseParser):
    """"""
    root = tg_phrase

    def interpret(self, result, start, end):
        compound = self.model.fields['compound'].model_class()
        glass_transition = self.model(value=first(result.xpath('./tg/value/text()')),
                    units=first(result.xpath('./tg/units/text()')))
        cem_el = first(result.xpath('./cem'))
        if cem_el is not None:
            compound.names = cem_el.xpath('./name/text()')
            compound.labels = cem_el.xpath('./label/text()')
        glass_transition.compound = compound
        yield glass_transition

