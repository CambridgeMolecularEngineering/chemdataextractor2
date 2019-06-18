# -*- coding: utf-8 -*-
"""
Units and models for angles.

:codeauthor: Juraj Mavračić <jm2111@cam.ac.uk>
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


class Angle(Dimension):
    """
    Dimension subclass for angles.
    """
    pass


class AngleModel(QuantityModel):
    """
    Model for angles.
    """
    dimensions = Angle()


class AngleUnit(Unit):
    """
    Base class for units with dimensions of angle.
    The standard value for length is defined to be a degree (°), implemented in the Degree class.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(AngleUnit, self).__init__(Angle(), magnitude, powers)


class Degrees(AngleUnit):
    """
    Class for degrees.
    """
    # TODO Does not take minutes into account properly, but only decimal degrees

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {R('[°º˚̥ ⁰∘]', group=0): Degrees}
Angle.units_dict = units_dict
Angle.standard_units = Degrees()


