# -*- coding: utf-8 -*-
"""
Units and models for electrical current.

.. codeauthor:: Batuhan Yildirim (by256@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .quantity_model import QuantityModel
from .unit import Unit
from .dimension import Dimension
from ...parse.elements import R
import logging

log = logging.getLogger(__name__)


class ElectricalCurrent(Dimension):
    """
    Dimension subclass for electrical current.
    """
    pass


class ElectricalCurrentModel(QuantityModel):
    """
    Model for electrical current.
    """
    dimensions = ElectricalCurrent()


class ElectricalCurrentUnit(Unit):
    """
    Base class for units with dimensions of electrical current.
    The standard value for current is defined to be an ampere, implemented in the Ampere class.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(ElectricalCurrentUnit, self).__init__(ElectricalCurrent(), magnitude, powers)


class Ampere(ElectricalCurrentUnit):
    """
    class for amps.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {R('A(mp(ere)?(s)?)?|amp(ere)?(s)?', group=0): Ampere}
ElectricalCurrent.units_dict = units_dict
ElectricalCurrent.standard_units = Ampere()
