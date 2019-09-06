# -*- coding: utf-8 -*-
"""
Units and models for lengths.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
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
    """
    Dimension subclass for lengths.
    """
    pass


class LengthModel(QuantityModel):
    """
    Model for lengths.
    """
    dimensions = Length()


class LengthUnit(Unit):
    """
    Base class for units with dimensions of length.
    The standard value for length is defined to be a meter, implemented in the Meter class.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(LengthUnit, self).__init__(Length(), magnitude, powers)


class Meter(LengthUnit):
    """
    Class for meters.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class Mile(LengthUnit):
    """
    Class for miles.
    """

    def convert_value_to_standard(self, value):
        return value * 1609.34

    def convert_value_from_standard(self, value):
        return value * 0.000621371

    def convert_error_to_standard(self, error):
        return error * 1609.34

    def convert_error_from_standard(self, error):
        return error * 0.000621371


class Angstrom(LengthUnit):
    """
    Class for Angstroms.
    """

    def convert_value_to_standard(self, value):
        return value * 10**(-10)

    def convert_value_from_standard(self, value):
        return value / 10**(-10)

    def convert_error_to_standard(self, error):
        return error * 10**(-10)

    def convert_error_from_standard(self, error):
        return error / 10**(-10)


class Micron(LengthUnit):
    def convert_value_to_standard(self, value):
        return value / 1000000.

    def convert_value_from_standard(self, value):
        return value * 1000000.

    def convert_error_to_standard(self, error):
        return error / 1000000.

    def convert_error_from_standard(self, error):
        return error * 1000000.


units_dict = {R('(m(eter(s)?)?(?!ile(s)?))|(Meter(s)?(?!ile(s)?))', group=0): Meter,
              R('[Mm]ile[s]?', group=0): Mile,
              R('[ÅÅ]', group=0): Angstrom,
              R('[M|m]icron', group=0): Micron}
Length.units_dict = units_dict
Length.standard_units = Meter()
