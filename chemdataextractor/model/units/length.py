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

from .quantity_model import QuantityModel
from .unit import Unit
from .dimension import Dimension
from ...parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ...parse.actions import merge, join
import logging

log = logging.getLogger(__name__)


class Length(Dimension):
    pass


class LengthModel(QuantityModel):

    dimensions = Length()


class LengthUnit(Unit):

    def __init__(self, magnitude=0.0, powers=None):
        super(LengthUnit, self).__init__(Length(), magnitude, powers)


class Meter(LengthUnit):

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class Mile(LengthUnit):

    def convert_value_to_standard(self, value):
        return value * 1609.34

    def convert_value_from_standard(self, value):
        return value * 0.000621371

    def convert_error_to_standard(self, error):
        return error * 1609.34

    def convert_error_from_standard(self, error):
        return error * 0.000621371

class Angstrom(LengthUnit):

    def convert_value_to_standard(self, value):
        return value * 10**(-10)

    def convert_value_from_standard(self, value):
        return value / 10**(-10)

    def convert_error_to_standard(self, error):
        return error * 10**(-10)

    def convert_error_from_standard(self, error):
        return error / 10**(-10)

units_dict = {R('m(eter(s)?)?', group=0): Meter, R('mile[s]?', group=0): Mile, R('Å', group=0): Angstrom}
Length.units_dict = units_dict
