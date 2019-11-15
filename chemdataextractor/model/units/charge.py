# -*- coding: utf-8 -*-
"""
Units and models for charge.

.. codeauthor:: Batuhan Yildirim (by256@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .quantity_model import QuantityModel
from .unit import Unit
from .dimension import Dimension
from.current import ElectricalCurrent
from .time import Time
from ...parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ...parse.actions import merge, join
import logging

log = logging.getLogger(__name__)


class Charge(Dimension):

    constituent_dimensions = ElectricalCurrent() * Time()


class ChargeModel(QuantityModel):

    dimensions = Charge()


class ChargeUnit(Unit):

    def __init__(self, magnitude=0.0, powers=None):
        super(ChargeUnit, self).__init__(Charge(), magnitude, powers)


class Coulomb(ChargeUnit):

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {R('(C|c)(oulomb(s)?)?', group=0): Coulomb}
Charge.units_dict.update(units_dict)
Charge.standard_units = Coulomb()
