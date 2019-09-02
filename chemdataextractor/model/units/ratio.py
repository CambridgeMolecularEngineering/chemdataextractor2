# -*- coding: utf-8 -*-
"""
Units and models for a ratio (percentage).

.. codeauthor:: Juraj Mavračić <jm2111@cam.ac.uk>

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


class Ratio(Dimension):
    pass


class RatioModel(QuantityModel):
    dimensions = Ratio()


class RatioUnit(Unit):
    def __init__(self, magnitude=0.0, powers=None):
        super(RatioUnit, self).__init__(Ratio(), magnitude, powers)


class Percent(RatioUnit):
    """
    Class for percents.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {R('%', group=0): Percent}
Ratio.units_dict = units_dict
Ratio.standard_units = Percent()

