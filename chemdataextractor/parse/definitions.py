# -*- coding: utf-8 -*-
"""
Parsers for generic specifier definitions
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging

from .common import lbrct, dt, rbrct, delim
from ..utils import first
from ..model import Compound
from .actions import merge, join
from .base import BaseParser
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group
from lxml import etree
log = logging.getLogger(__name__)

#: Greek symbols
greek_symbols = R('[\u0370-\u03ff\u1f00-\u1fff]')('specifier')

#: Critical temperature e.g. Tc, Tmax, etc
critical_temperature = R('T[C|c|N|n|max|on|1-2|A-Z]')('specifier')

#: Possible definition specifiers
specifier_options = (greek_symbols | critical_temperature)

#: Definition phrase 1: "definition, specifier" or "definition (specifier)"
definition_phrase_1 = (OneOrMore(T('JJ') | T('NN') | T('NNP') | T('HYPH') | T('VBG'))('phrase').add_action(join) + Optional(delim) + Optional(rbrct) + specifier_options + Optional(rbrct))('definition')

#: Add new definitions to this phrase
specifier_definition = (definition_phrase_1)('definition')
