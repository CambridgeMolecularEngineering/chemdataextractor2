# -*- coding: utf-8 -*-
"""
Base types for making quantity models.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import six
import copy
from abc import ABCMeta
from ..base import BaseModel, BaseType, FloatType, StringType, ListType, ModelMeta, InferredProperty
from .unit import Unit, UnitType
from .dimension import Dimensionless
from ...parse.elements import Any
from ...parse.auto import AutoSentenceParser, AutoTableParser, construct_unit_element, match_dimensions_of
from ...parse.quantity import magnitudes_dict, infer_unit, infer_value, infer_error, value_element
from ...parse.template import QuantityModelTemplateParser, MultiQuantityModelTemplateParser


class _QuantityModelMeta(ModelMeta):
    """"""

    def __new__(mcs, name, bases, attrs):
        cls = super(_QuantityModelMeta, mcs).__new__(mcs, name, bases, attrs)
        unit_element = construct_unit_element(cls.dimensions)
        if unit_element:
            cls.fields['raw_units'].parse_expression = unit_element(None)
        cls.fields['raw_value'].parse_expression = value_element()(None)
        return cls


class QuantityModel(six.with_metaclass(_QuantityModelMeta, BaseModel)):
    """
    Class for modelling quantities. Subclasses of this model can be used in conjunction with Autoparsers to extract properties
    with zero human intervention. However, they must be constructed in a certain way for them to work optimally with autoparsers.
    Namely, they should have:

    - A specifier field with an associated parse expression (Optional, only required if autoparsers are desired). These parse expressions will be updated automatically using forward-looking Interdependency Resolution if the updatable flag is set to True.
    - These specifiers should also have required set to True so that spurious matches are not found.
    - If applicable, a compound field, named compound.

    Any parse_expressions set in the model should have an added action to ensure that the results are a single word. An example would be to call add_action(join) on each parse expression.
    """
    raw_value = StringType(required=True, contextual=True)
    raw_units = StringType(required=True, contextual=True)
    value = InferredProperty(ListType(FloatType(), sorted_=True),
                             origin_field='raw_value', inferrer=infer_value, contextual=True)
    units = InferredProperty(UnitType(),
                             origin_field='raw_units', inferrer=infer_unit, contextual=True)
    error = InferredProperty(FloatType(),
                             origin_field='raw_value', inferrer=infer_error, contextual=True)
    dimensions = None
    specifier = StringType()
    parsers = [MultiQuantityModelTemplateParser(), QuantityModelTemplateParser(), AutoTableParser()]

    # Operators are implemented so that composite quantities can be created easily
    # on the fly, such as the following code snippet:

    # .. code-block:: python

    #     length = LengthModel()
    #     length.unit = Meter()
    #     length.value = 10
    #     time = TimeModel()
    #     time.unit = Second()
    #     time.value = [2]
    #     speed = length / time
    #     print("Speed in miles per hour is: ", speed.convert_to(Mile() / Hour()).value[0])

    # Which has an expected output of

    # Speed in miles per hour is:  11.184709259696522

    def __truediv__(self, other):

        other_inverted = other**(-1.0)
        new_model = self * other_inverted
        return new_model

    def __pow__(self, other):

        new_model = QuantityModel()
        new_model.dimensions = self.dimensions ** other
        if self.value is not None:
            new_val = []
            for val in self.value:
                new_val.append(val ** other)
            new_model.value = new_val
        if self.units is not None:
            new_model.units = self.units ** other
        # Handle case that we have a dimensionless quantity, so we don't get dimensionless units squared.
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
                # value has sorted_=True, so it should sort any values.
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

        .. note::

            This method both modifies the current model and returns the modified model.

        :param Unit unit: The Unit to convert to
        :returns: The quantity in the given units.
        :rtype: QuantityModel
        """
        if self.units:
            try:
                converted_values = self.convert_value(self.units, unit)
                if self.error:
                    converted_error = self.convert_error(self.units, unit)
                    self.error = converted_error
                self.value = converted_values
                self.units = unit
            except ZeroDivisionError:
                raise ValueError('Model not converted due to zero division error')
        else:
            raise AttributeError('Current units not set')
        return self

    def convert_to_standard(self):
        """
        Convert from current units to the standard units.
        Raises AttributeError if the current unit has not been set or the dimensions do not have standard units.

        .. note::

            This method both modifies the current model and returns the modified model.

        :returns: The quantity in the given units.
        :rtype: QuantityModel
        """
        standard_units = self.dimensions.standard_units
        if self.units and standard_units is not None:
            self.convert_to(standard_units)
        else:
            if not self.units:
                raise AttributeError('Current units not set')
            elif not self.dimensions.standard_units:
                raise AttributeError('Standard units for dimension', self.dimension, 'not set')
        return self

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

    def is_superset(self, other):
        if type(self) != type(other):
            return False
        for field_name, field in six.iteritems(self.fields):
            # Method works recursively so it works with nested models
            if hasattr(field, 'model_class'):
                if self[field_name] is None:
                    if other[field_name] is not None:
                        return False
                elif other[field_name] is None:
                    pass
                elif not self[field_name].is_superset(other[field_name]):
                    return False
            else:
                if (field_name == 'raw_value' and other[field_name] == 'NoValue'
                    and self[field_name] is not None):
                    pass
                elif other[field_name] is not None and self[field_name] != other[field_name]:
                    return False
        return True

    def _compatible(self, other):
        match = False
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            match = True
            for field_name, field in six.iteritems(self.fields):
                if (field_name == 'raw_value' and other[field_name] == 'NoValue'
                    and self[field_name] is not None):
                    pass
                elif (self[field_name] is not None
                  and other[field_name] is not None
                  and self[field_name] != other[field_name]):
                    match = False
                    break
        return match

    def __str__(self):
        string = 'Quantity with ' + self.dimensions.__str__() + ', ' + self.units.__str__()
        string += ' and a value of ' + str(self.value)
        return string


class DimensionlessModel(QuantityModel):
    """ Special case to handle dimensionless quantities"""
    dimensions = Dimensionless()
    raw_units = StringType(required=False, contextual=False)
