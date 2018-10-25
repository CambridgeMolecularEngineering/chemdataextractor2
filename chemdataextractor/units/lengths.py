from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
from abc import ABCMeta, ABC
from collections import MutableSequence
import json
import logging

import six

from .quantities import QuantityModel, Unit, UnitType


class LengthModel(QuantityModel):
    pass


class LengthUnit(Unit):

    def __init__(self, exponent=1, powers=None):
        super(LengthUnit, self).__init__(LengthModel(), exponent, powers)


class Meter(LengthUnit):

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value


class Mile(LengthUnit):

    def convert_to_standard(self, value):
        return value * 1609.34

    def convert_from_standard(self, value):
        return value / 1609.34
