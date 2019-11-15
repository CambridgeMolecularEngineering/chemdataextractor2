# -*- coding: utf-8 -*-
"""
Units and models for power

.. codeauthor:: Juraj Mavračić <jm2111@cam.ac.uk>

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .quantity_model import QuantityModel
from .unit import Unit
from .dimension import Dimension
from .charge import Charge
from .energy import Energy
from .electric_potential import ElectricPotential
from .current import ElectricalCurrent
from ...parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ...parse.actions import merge, join
import logging

log = logging.getLogger(__name__)


class Power(Dimension):
    constituent_dimensions = ElectricPotential() * ElectricalCurrent()


class PowerModel(QuantityModel):
    dimensions = Power()


class PowerUnit(Unit):

    def __init__(self, magnitude=0.0, powers=None):
        super(PowerUnit, self).__init__(Power(), magnitude, powers)


class Watt(PowerUnit):

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {R('(W|w)(att(s)?)?', group=0): Watt}
Power.units_dict.update(units_dict)
Power.standard_units = Watt()

