# -*- coding: utf-8 -*-
"""
chemdataextractor.parse.quantity
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parser for finding quantities and units

Taketomo Isazawa (ti250@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re
from abc import abstractproperty

from .cem import cem, chemical_label, lenient_chemical_label, solvent_name
from .common import lbrct, dt, rbrct
from ..utils import first
from ..model import Compound, MeltingPoint
from .actions import merge, join
from .base import BaseParser
from .elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore


class QuantityParser(BaseParser):

    @abstractproperty
    def units(self):
        pass

    joined_range = R('^[\+\-–−]?\d+(\.\d+)?[\-–−~∼˜]\d+(\.\d+)?$')('value').add_action(merge)
    spaced_range = (R('^[\+\-–−]?\d+(\.\d+)?$') + Optional(units).hide() + (R('^[\-–−~∼˜]$') + R('^[\+\-–−]?\d+(\.\d+)?$') | R('^[\+\-–−]\d+(\.\d+)?$')))('value').add_action(merge)
    to_range = (R('^[\+\-–−]?\d+(\.\d+)?$') + Optional(units).hide() + (I('to') + R('^[\+\-–−]?\d+(\.\d+)?$') | R('^[\+\-–−]\d+(\.\d+)?$')))('value').add_action(join)
    value_range = (Optional(R('^[\-–−]$')) + (joined_range | spaced_range | to_range))('value').add_action(merge)
    value_single = (Optional(R('^[~∼˜\<\>]$')) + Optional(R('^[\-–−]$')) + R('^[\+\-–−]?\d+(\.\d+)?$'))('value').add_action(merge)
    value = Optional(lbrct).hide() + (value_range | value_single)('value') + Optional(rbrct).hide()

    def interpret_value(self, string):
        split_by_num = re.split('([\d\.]+(?![\d\.]+))', string)
        values = []
        for value in split_by_num:
            try:
                float_val = float(value)
                values.append(float_val)
            except:
                pass
        if len(values) == 1:
            values = values[0]
        return values
