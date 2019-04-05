# -*- coding: utf-8 -*-
"""
Units and models for times.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
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


class Time(Dimension):
    """
    Dimension subclass for times.
    """
    pass


class TimeModel(QuantityModel):
    """
    Model for times. These models should strictly be used for time intervals, never
    absolute times, as peculiarities of calendars are not supported,
    e.g. a minute is always defined as 60 seconds.
    """
    dimensions = Time()


class TimeUnit(Unit):

    def __init__(self, magnitude=0.0, powers=None):
        """
        Base class for units with dimensions of time.
        The standard value for time is defined to be a second, implemented in the Second class.
        """
        super(TimeUnit, self).__init__(Time(), magnitude, powers)


class Second(TimeUnit):
    """
    Class for seconds.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class Hour(TimeUnit):
    """
    Class for hours.
    """

    def convert_value_to_standard(self, value):
        return value * 60 * 60

    def convert_value_from_standard(self, value):
        return value / (60.0**2)

    def convert_error_to_standard(self, error):
        return error * 60 * 60

    def convert_error_from_standard(self, error):
        return error / (60.0 * 60.0)


class Minute(TimeUnit):
    """
    Class for minutes.
    """

    def convert_value_to_standard(self, value):
        return value * 60.0

    def convert_value_from_standard(self, value):
        return value / 60.0

    def convert_error_to_standard(self, error):
        return error * 60.0

    def convert_error_from_standard(self, error):
        return error / 60.0


class Year(TimeUnit):
    """
    Class for years.
    """

    def convert_to_standard(self, value):
        return value * 60 * 60 * 24 * 365

    def convert_from_standard(self, value):
        return value / (60 * 60 * 24 * 365)


class Day(TimeUnit):
    """
    Class for days.
    """

    def convert_value_to_standard(self, value):
        return value * 60 * 60 * 24

    def convert_value_from_standard(self, value):
        return value / (60 * 60 * 24)

    def convert_error_to_standard(self, error):
        return error * 60 * 60.0 * 24.0

    def convert_error_from_standard(self, error):
        return error / (60 * 60.0 * 24.0)


units_dict = {R('d(ay(s)?)?', group=0): Day, R('y(ear(s)?)?', group=0): Year,
              R('h(our(s)?)?', group=0): Hour, R('s(econd(s)?)?', group=0): Second}
Time.units_dict = units_dict
Time.standard_units = Second()
