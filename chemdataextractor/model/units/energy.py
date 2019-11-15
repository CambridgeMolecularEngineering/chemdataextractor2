# -*- coding: utf-8 -*-
"""
chemdataextractor.units.temperatures.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Units and models for energy.

.. codeauthor:: Batuhan Yildirim (by256@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .quantity_model import QuantityModel
from .unit import Unit
from .dimension import Dimension
from.mass import Mass
from .length import Length
from .time import Time
from ...parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ...parse.actions import merge, join
import logging

log = logging.getLogger(__name__)


class Energy(Dimension):
    constituent_dimensions = Mass() * Length()**2 / Time()**2


class EnergyModel(QuantityModel):

    dimensions = Energy()


class EnergyUnit(Unit):

    def __init__(self, magnitude=0.0, powers=None):
        super(EnergyUnit, self).__init__(Energy(), magnitude, powers)


class Joule(EnergyUnit):

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class ElectronVolt(EnergyUnit):

    def convert_value_to_standard(self, value):
        return value * 1.6021766208e-19

    def convert_value_from_standard(self, value):
        return value / 1.6021766208e-19

    def convert_error_to_standard(self, error):
        return error * 1.6021766208e-19

    def convert_error_from_standard(self, error):
        return error / 1.6021766208e-19


class Erg(EnergyUnit):
    def convert_value_to_standard(self, value):
        return 1e-7 * value

    def convert_value_from_standard(self, value):
        return 1e7 * value

    def convert_error_to_standard(self, error):
        return 1e-7 * error

    def convert_error_from_standard(self, error):
        return 1e7 * error


units_dict = {R('(J|j)(oule(s)?)?', group=0): Joule,
              R('(E|e)(lectron)?( )?(V|v)(olts)?', group=0): ElectronVolt,
              R('(E|e)rg', group=0): Erg}
Energy.units_dict.update(units_dict)
Energy.standard_units = Joule()
