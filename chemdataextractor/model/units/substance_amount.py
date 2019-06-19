# -*- coding: utf-8 -*-
"""
Units and models for amounts of a substance.

:codeauthor: Callum Court (cc889@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from .quantity_model import QuantityModel
from .unit import Unit
from .dimension import Dimension
from ...parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ...parse.actions import merge, join

log = logging.getLogger(__name__)


class AmountOfSubstance(Dimension):
    """
    Dimension subclass for amounts of substances.
    """
    pass


class AmountOfSubstanceModel(QuantityModel):
    """
    Model for temperatures.
    """
    dimensions = AmountOfSubstance()


class AmountOfSubstanceUnit(Unit):
    """
    Base class for units with dimensions of temperature.
    The standard value for temperature is defined to be a Kelvin, implemented in the Kelvin class.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(AmountOfSubstanceUnit, self).__init__(AmountOfSubstance(), magnitude, powers)


class Mol(AmountOfSubstanceUnit):
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

units_dict = {R('[Mm](ol)(e(s)?)?', group=0): Mol}
# The final element in units_dict is given to ensure that '°C' is parsed correctly,
# as the tokenizer splits it into two. When a parser element is assigned to None,
# this means that this element will be ignored when extracting units, but will
# be taken into account for autoparsers to extract from sentences.
AmountOfSubstance.units_dict = units_dict
AmountOfSubstance.standard_units = Mol()
