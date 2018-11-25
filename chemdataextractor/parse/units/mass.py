# -*- coding: utf-8 -*-
"""
chemdataextractor.units.temperatures.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Units and models for masses.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .quantity_model import QuantityModel
from .unit import Unit
from .dimension import Dimension
from ..elements import R
import logging

log = logging.getLogger(__name__)


class Mass(Dimension):
    pass


class MassModel(QuantityModel):

    dimensions = Mass()


class MassUnit(Unit):

    def __init__(self, magnitude=0.0, powers=None):
        super(MassUnit, self).__init__(Mass(), magnitude, powers)


class Gram(MassUnit):

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class Pound(MassUnit):

    def convert_value_to_standard(self, value):
        return value * 453.592

    def convert_value_from_standard(self, value):
        return value / 453.592

    def convert_error_to_standard(self, error):
        return error * 453.592

    def convert_error_from_standard(self, error):
        return error / 453.592


class Tonne(MassUnit):

    def convert_value_to_standard(self, value):
        return value * 1000000.

    def convert_value_from_standard(self, value):
        return value / 1000000.

    def convert_error_to_standard(self, error):
        return error * 1000000.

    def convert_error_from_standard(self, error):
        return error / 1000000.


units_dict = {R('g(ram(s)?)?', group=0): Gram, R('pound[s]?', group=0): Pound, R('lb[s]?', group=0): Pound,
R('t(onne)?', group=0): Tonne}
Mass.units_dict = units_dict
