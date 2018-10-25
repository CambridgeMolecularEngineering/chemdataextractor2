from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from .quantities import QuantityModel, Unit

log = logging.getLogger(__name__)


from .quantities import QuantityModel, Unit, UnitType


class TimeModel(QuantityModel):
    pass


class TimeUnit(Unit):

    def __init__(self, exponent=1, powers=None):
        super(TimeUnit, self).__init__(TimeModel(), exponent, powers)


class Second(TimeUnit):

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value


class Hour(TimeUnit):

    def convert_to_standard(self, value):
        return value * 60 * 60

    def convert_from_standard(self, value):
        return value / (60**2)


class Minute(TimeUnit):

    def convert_to_standard(self, value):
        return value * 60

    def convert_from_standard(self, value):
        return value / 60


class Year(TimeUnit):

    def convert_to_standard(self, value):
        return value * 60 * 60 * 24 * 365

    def convert_from_standard(self, value):
        return value / (60 * 60 * 24 * 365)


class Day(TimeUnit):

    def convert_to_standard(self, value):
        return value * 60 * 60 * 24

    def convert_from_standard(self, value):
        return value / (60 * 60 * 24)
