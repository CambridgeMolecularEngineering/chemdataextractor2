# -*- coding: utf-8 -*-
"""
Base types for making quantity models.

Taketomo Isazawa (ti250@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from ..base import BaseModel, BaseType, FloatType, StringType, ListType
from .unit import Unit, UnitType
from .dimension import Dimensionless
from ...parse.elements import Any


class QuantityModel(BaseModel):
    """
    Class for quantities. All actual quantities should be subclassed from this
    instead of BaseQuantityModel. (This setup is as we otherwise wouldn't be able
    to make a list with QuantityModel-type objects as keys)
    """
    raw_value = StringType()
    raw_units = StringType()
    value = ListType(FloatType())
    units = UnitType()
    error = FloatType()
    dimensions = None
    specifier = Any()

    """
    Operators are implemented so that composite quantities can be created easily
    on the fly, such as the following code snippet:

    length = LengthModel()
    length.unit = Meter()
    length.value = 10
    time = TimeModel()
    time.unit = Second()
    time.value = 2
    speed = length / time
    print("Speed in miles per hour is: ", speed.convert_to(Mile() / Hour()))

    Which has an expected output of

    Speed in miles per hour is:  11.184709259696522
    """

    def __truediv__(self, other):

        other_inverted = other**(-1.0)
        new_model = self * other_inverted
        return new_model

    def __pow__(self, other):

        # Handle case that we have a dimensionless quantity, so we don't get dimensionless units squared.
        new_model = QuantityModel()
        new_model.dimensions = self.dimensions ** other
        if self.value is not None:
            if type(self.value) is list:
                new_val = []
                for val in self.value:
                    new_val.append(val ** other)
                new_model.value = new_val
            else:
                new_model.value = self.value ** other
        if self.units is not None:
            new_model.units = self.units ** other
        if isinstance(new_model.dimensions, Dimensionless):
            dimensionless_model = DimensionlessModel()
            dimensionless_model.value = new_model.value
            dimensionless_model.units = new_model.units
            return dimensionless_model

        return new_model

    def __mul__(self, other):

        new_model = QuantityModel()
        new_model.dimensions = self.dimensions * other.dimensions
        if self.value is not None and other.value is not None:
            if len(self.value) == 2 and len(other.value) == 2:
                # The following always encompasses the whole range because
                # OptionalRangeType tries to always sort the lists
                new_val = [self.value[0] * other.value[0],
                           self.value[1] * other.value[1]]
                new_model.value = new_val
            elif len(self.value) == 2:
                new_val = [self.value[0] * other.value[0],
                           self.value[1] * other.value[0]]
                new_model.value = new_val
            elif len(self.value) == 2 and len(other.value) == 2:
                new_val = [self.value[0] * other.value[0],
                           self.value[0] * other.value[1]]
                new_model.value = new_val
            else:
                new_model.value = [self.value[0] * other.value[0]]
        if self.units is not None and other.units is not None:
            new_model.units = self.units * other.units
        if isinstance(new_model.dimensions, Dimensionless):
            dimensionless_model = DimensionlessModel()
            dimensionless_model.value = new_model.value
            dimensionless_model.units = new_model.units
            return dimensionless_model

        return new_model

    def convert_to(self, unit):
        """
        Convert from current units to the given units.
        Raises AttributeError if the current unit is not set.

        :param Unit unit: The Unit to convert to
        :returns: The value as expressed in the new unit
        :rtype: float
        """
        if self.units:
            converted_values = self.convert_value(self.units, unit)
            self.value = converted_values
            self.units = unit
            if self.error:
                converted_error = self.convert_error(self.units, unit)
                self.error = converted_error

        return self
        #raise AttributeError("Unit to convert from not set")

    def convert_value(self, from_unit, to_unit):
        """
        Convert between the given units.
        If no units have been set for this model, assumes that it's in standard units.

        :param Unit from_unit: The Unit to convert from
        :param Unit to_unit: The Unit to convert to
        :returns: The value as expressed in the new unit
        :rtype: float
        """
        if self.value is not None:
            if to_unit.dimensions == from_unit.dimensions:
                if len(self.value) == 2:
                    standard_vals = [from_unit.convert_value_to_standard(self.value[0]),
                                     from_unit.convert_value_to_standard(self.value[1])]
                    return [to_unit.convert_value_from_standard(standard_vals[0]),
                            to_unit.convert_value_from_standard(standard_vals[1])]
                else:
                    standard_val = from_unit.convert_value_to_standard(self.value[0])
                    return [to_unit.convert_value_from_standard(standard_val)]
            else:
                raise ValueError("Unit to convert to must have same dimensions as current unit")
            raise AttributeError("Unit to convert from not set")
        else:
            raise AttributeError("Value for model not set")

    def convert_error(self, from_unit, to_unit):
        """
        Converts error between given units
        If no units have been set for this model, assumes that it's in standard units.

        :param Unit from_unit: The Unit to convert from
        :param Unit to_unit: The Unit to convert to
        :returns: The error as expressed in the new unit
        :rtype: float
        """

        if self.error is not None:
            if to_unit.dimensions == from_unit.dimensions:
                standard_error = from_unit.convert_error_to_standard(self.error)
                return to_unit.convert_error_from_standard(standard_error)
            else:
                raise ValueError("Unit to convert to must have same dimensions as current unit")
            raise AttributeError("Unit to convert from not set")
        else:
            raise AttributeError("Value for model not set")

    def is_equal(self, other):
        """
        Tests whether the two quantities are physically equal, i.e. whether they represent the same value just in different units.

        :param QuantityModel other: The quantity being compared with
        :returns: Whether the two quantities are equal
        :rtype: bool
        """
        if self.value is None or other.value is None:
            raise AttributeError("Value for model not set")
        if self.units is None or other.units is None:
            raise AttributeError("Units not set")
        converted_value = self.convert_value(self.units, other.units)

        min_converted_value = converted_value[0]
        max_converted_value = converted_value[0]
        if len(converted_value) == 2:
            max_converted_value = converted_value[1]
        if self.error is not None:
            converted_error = self.convert_error(self.units, other.units)
            min_converted_value = min_converted_value - converted_error
            max_converted_value = max_converted_value + converted_error

        min_other_value = other.value[0]
        max_other_value = other.value[0]
        if len(other.value) == 2:
            max_other_value = other.value[1]
        if other.error is not None:
            min_other_value = min_other_value - other.error
            max_other_value = max_other_value + other.error
        if min_converted_value <= max_other_value or max_converted_value >= min_other_value:
            return True
        return False



    def __str__(self):
        string = 'Quantity with ' + self.dimensions.__str__() + ', ' + self.units.__str__()
        string += ' and a value of ' + str(self.value)
        return string


class DimensionlessModel(QuantityModel):
    """ Special case to handle dimensionless quantities"""
    dimensions = Dimensionless()
