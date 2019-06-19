# -*- coding: utf-8 -*-
"""
Units and models for temperatures.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from .quantity_model import QuantityModel, StringType
from .unit import Unit
from .dimension import Dimension
from ...parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ...parse.actions import merge, join

log = logging.getLogger(__name__)


class Temperature(Dimension):
    """
    Dimension subclass for temperatures.
    """
    pass


class TemperatureModel(QuantityModel):
    """
    Model for temperatures.
    """
    dimensions = Temperature()


class TemperatureUnit(Unit):
    """
    Base class for units with dimensions of temperature.
    The standard value for temperature is defined to be a Kelvin, implemented in the Kelvin class.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(TemperatureUnit, self).__init__(Temperature(), magnitude, powers)


class Kelvin(TemperatureUnit):
    """
    Class for Kelvins.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class Celsius(TemperatureUnit):
    """
    Class for Celsius
    """

    def convert_value_to_standard(self, value):
        return value + 273.15

    def convert_value_from_standard(self, value):
        return value - 273.15

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class Fahrenheit(TemperatureUnit):
    """
    Class for Fahrenheit.
    """

    def convert_value_to_standard(self, value):
        return (value + 459.67) * (5. / 9.)

    def convert_value_from_standard(self, value):
        return value * (9. / 5.) - 459.67

    def convert_error_to_standard(self, error):
        return error * (5. / 9.)

    def convert_error_from_standard(self, error):
        return error * (9. / 5.)


units_dict = {R('°?(((K|k)elvin(s)?)|K)\.?', group=0): Kelvin,
              R('(°C|((C|c)elsius))\.?', group=0): Celsius,
              R('(\[deg\.] C\.)|([D|d]egrees? C(entigrade(s)?)?\.?)', group=0): Celsius,
              R('°?((F|f)ahrenheit|F)\.?', group=0): Fahrenheit,
              R('°|C', group=0): None}
# The final element in units_dict is given to ensure that '°C' is parsed correctly,
# as the tokenizer splits it into two. When a parser element is assigned to None,
# this means that this element will be ignored when extracting units, but will
# be taken into account for autoparsers to extract from sentences.
Temperature.units_dict = units_dict
Temperature.standard_units = Kelvin()
