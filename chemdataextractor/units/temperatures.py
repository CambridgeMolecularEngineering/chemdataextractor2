# -*- coding: utf-8 -*-
"""
chemdataextractor.units.temperatures.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Units and models for temperatures.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from .quantities import QuantityModel, Unit, Dimension
from ..parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ..parse.actions import merge, join

log = logging.getLogger(__name__)


class Temperature(Dimension):
    pass


class TemperatureModel(QuantityModel):

    dimensions = Temperature()


class TemperatureUnit(Unit):

    def __init__(self, exponent=0.0, powers=None):
        super(TemperatureUnit, self).__init__(Temperature(), exponent, powers)


class Kelvin(TemperatureUnit):

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value


class Celsius(TemperatureUnit):

    def convert_to_standard(self, value):
        return value + 273.15

    def convert_from_standard(self, value):
        return value - 273.15


class Fahrenheit(TemperatureUnit):

    def convert_to_standard(self, value):
        return (value + 459.67) * (5. / 9.)

    def convert_from_standard(self, value):
        return value * (9. / 5.) - 459.67


units_dict = {R('(°[K]\.?)|(K\.?)$', group=0).add_action(merge): Kelvin,
              R('°?[C]\.?', group=0).add_action(merge): Celsius,
              R('°?[F]\.?', group=0).add_action(merge): Fahrenheit}
Temperature.units_dict = units_dict
