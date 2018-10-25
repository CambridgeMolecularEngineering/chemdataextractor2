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

from .quantities import QuantityModel, Unit

log = logging.getLogger(__name__)


class TemperatureModel(QuantityModel):
    pass


class TemperatureUnit(Unit):

    def __init__(self, exponent=1, powers=None):
        super(TemperatureUnit, self).__init__(TemperatureModel(), exponent, powers)


class Kelvin(TemperatureUnit):

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value


class Celsius(TemperatureUnit):

    def convert_to_standard(self, value):
        print('celsius: ', value, ' Kelvin: ', value + 273.15)
        return value + 273.15

    def convert_from_standard(self, value):
        print('kelvin: ', value, 'celsius: ', value - 273.15)
        return value - 273.15


class Fahrenheit(TemperatureUnit):

    def convert_to_standard(self, value):
        print('fahrenheit: ', value, 'Kelvin: ', value * (9. / 5.) - 459.67)
        return (value + 459.67) * (5. / 9.)

    def convert_from_standard(self, value):
        print('Kelvin: ', value, 'fahrenheit: ', (value + 459.67) * (5. / 9.))
        return value * (9. / 5.) - 459.67
