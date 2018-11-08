# -*- coding: utf-8 -*-
"""
chemdataextractor.units.temperatures.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Units and models for lengths.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from ..parse.elements import R

import logging

from .quantities import QuantityModel, Unit, Dimension

log = logging.getLogger(__name__)


class Length(Dimension):
    pass


class LengthModel(QuantityModel):

    dimensions = Length()


class LengthUnit(Unit):

    def __init__(self, exponent=0.0, powers=None):
        super(LengthUnit, self).__init__(Length(), exponent, powers)


class Meter(LengthUnit):

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value


class Mile(LengthUnit):

    def convert_to_standard(self, value):
        return value * 1609.34

    def convert_from_standard(self, value):
        return value / 1609.34

units_dict = {R('m(eter(s)?)?', group=0): Meter, R('mile[s]?', group=0): Mile}
Length.units_dict = units_dict
