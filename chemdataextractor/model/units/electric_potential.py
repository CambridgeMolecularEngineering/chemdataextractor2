# -*- coding: utf-8 -*-
"""
Units and models for electric potential

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
from ...parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ...parse.actions import merge, join
import logging

log = logging.getLogger(__name__)


class ElectricPotential(Dimension):
    constituent_dimensions = Energy() / Charge()


class ElectricPotentialModel(QuantityModel):
    dimensions = ElectricPotential()


class ElectricPotentialUnit(Unit):

    def __init__(self, magnitude=0.0, powers=None):
        super(ElectricPotentialUnit, self).__init__(ElectricPotential(), magnitude, powers)


class Volt(ElectricPotentialUnit):

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {R('(V|v)(olt(s)?)?', group=0): Volt}
ElectricPotential.units_dict.update(units_dict)
ElectricPotential.standard_units = Volt()
