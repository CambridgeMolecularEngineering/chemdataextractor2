from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from chemdataextractor.model.units.quantity_model import QuantityModel
from chemdataextractor.model.units import Unit
from chemdataextractor.model.units.dimension import Dimension
from chemdataextractor.parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from chemdataextractor.parse.actions import merge, join
from chemdataextractor.model.units.mass import Mass
from chemdataextractor.model.units.time import Time
from chemdataextractor.model.units.current import ElectricalCurrent
from math import pi
log = logging.getLogger(__name__)

"""
Units
In SI units, B is measured in teslas (symbol: T) base units: kg s-2 A-1 or 
The SI unit of tesla is equivalent to (newton·second)/(coulomb·metre).

In Gaussian-cgs units, B is measured in gauss (symbol: G). 
(The conversion is 1 T = 10000 G) 
One nanotesla is equivalent to 1 gamma (symbol: γ).

The H-field is measured in amperes per metre (A/m) in SI units, and in oersteds (Oe) in cgs units.
"""

class MagneticField(Dimension):
    constituent_dimensions = Mass() / (ElectricalCurrent() * Time()**2)
    

class MagneticFieldModel(QuantityModel):
    """
    Model for temperatures.
    """
    dimensions = MagneticField()


class MagneticFieldUnit(Unit):
    """
    Base class for units with dimensions of temperature.
    The standard value for temperature is defined to be a Kelvin, implemented in the Kelvin class.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(MagneticFieldUnit, self).__init__(MagneticField(), magnitude, powers)


class Tesla(MagneticFieldUnit):
    """
    Class for Tesla.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error

class Gauss(MagneticFieldUnit):
    """Class for Gauss
    """

    def convert_value_to_standard(self, value):
        return value / 10000

    def convert_value_from_standard(self, value):
        return value * 10000

    def convert_error_to_standard(self, error):
        return error / 10000

    def convert_error_from_standard(self, error):
        return error * 10000

class Gamma(MagneticFieldUnit):
    """
    Class for Gammas.
    """

    def convert_value_to_standard(self, value):
        return value * 1e-9

    def convert_value_from_standard(self, value):
        return value * 1e9

    def convert_error_to_standard(self, error):
        return error * 1e-9

    def convert_error_from_standard(self, error):
        return error * 1e9


class Oersted(MagneticFieldUnit):
    """
    Class for Oersteds

    This is technically H-fields, B = muH, in air mu = 1
    1 Oe = 1 G = 1/10000 T
    """

    def convert_value_to_standard(self, value):
        return value / 10000

    def convert_value_from_standard(self, value):
        return value * 10000

    def convert_error_to_standard(self, error):
        return error / 10000

    def convert_error_from_standard(self, error):
        return error * 10000

units_dict = {R('T(esla)?', group=0): Tesla,
              R('Oe', group=0): Oersted,
              R('(γ|gamma)', group=0): Gamma,
              R('G(auss)?', group=0): Gauss}

MagneticField.units_dict.update(units_dict)
MagneticField.standard_units = Tesla()