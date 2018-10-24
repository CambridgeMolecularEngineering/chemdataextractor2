from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
from abc import ABCMeta, ABC, abstractmethod
from collections import MutableSequence
import json
import logging

import six

from ..utils import python_2_unicode_compatible
from ..model import BaseModel, BaseType, FloatType, DictionaryType, ModelType, StringType

log = logging.getLogger(__name__)

class UnitType(BaseType):

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a Model."""
        if hasattr(value, 'quantity'):
            if value.quantity.same_type_as(instance):
                print(value.quantity.powers, instance.powers)
                instance._values[self.name] = self.process(value)
            else:
                instance._values[self.name] = None
        else:
            instance._values[self.name] = None

    def process(self, value):
        if isinstance(value, Unit):
            return value
        return None


class BaseQuantityModel(BaseModel):
    value = FloatType()
    unit = UnitType()

    @abstractmethod
    def convert_to(self, unit):
        pass

    @abstractmethod
    def __hash__(self):
        pass


class QuantityModel(BaseQuantityModel):
    powers = DictionaryType({ModelType(BaseQuantityModel): FloatType()})

    def __truediv__(self, other):

        other_inverted = other**(-1)
        new_model = self * other_inverted
        return new_model

    def __pow__(self, other):

        new_model = QuantityModel()
        if self.value is not None:
            new_model.value = self.value**other
        if self.unit is not None:
            new_model.unit = self.unit**other
        powers = {}

        if self.powers is not None:
            for key, value in six.iteritems(self.powers):
                powers[key] = value * other

        else:
            new_key = copy.deepcopy(self)
            new_key.value = None
            new_key.unit = None
            powers[new_key] = other

        new_model.powers = powers
        return new_model

    def __mul__(self, other):

        new_model = QuantityModel()
        if self.value is not None and other.value is not None:
            new_model.value = self.value * other.value
        if self.unit is not None and other.unit is not None:
            new_model.unit = self.unit * other.unit
        powers = {}

        if self.powers is not None:
            powers = copy.deepcopy(self.powers)

        else:
            new_key = copy.deepcopy(self)
            new_key.value = None
            new_key.unit = None
            powers[new_key] = 1.0

        if other.powers is not None:
            for key, value in six.iteritems(other.powers):
                if self.powers is not None:
                    if key in self.powers:
                        powers[key] += value
                else:
                    powers[key] = value

        else:
            new_key = copy.deepcopy(other)
            new_key.value = None
            new_key.unit = None
            if self.powers is not None:
                if new_key in self.powers:
                    powers[key] += value
            else:
                powers[new_key] = 1.0

        new_model.powers = powers
        return new_model

    def __eq__(self, other):

        if self.powers is not None:
            if self.powers == other.powers and self.value == other.value and self.unit == other.unit:
                return True
        else:
            if type(self) == type(other) and self.value == other.value and self.unit == other.unit:
                return True
        return False

    def same_type_as(self, other):

        if self.powers is not None:
            if self.powers == other.powers:
                return True
        else:
            if type(self) == type(other):
                return True
        return False

    def convert_to(self, unit):
        if unit.quantity == self.unit.quantity:
            standard_val = self.unit.convert_to_standard(self.value)
            return unit.convert_from_standard(standard_val)
        else:
            raise ValueError("Unit to convert to must have same dimensions as current unit")

    def __hash__(self):
        string = str(self.__class__.__name__)
        # string += str(self.serialize())
        string += str(self.unit)
        string += str(self.value)
        string += str(self.powers)
        return string.__hash__()


class Unit(object):
    # TODO: Currently exponent does nothing

    def __init__(self, quantity, exponent=1, powers=None):
        if quantity.unit is not None or quantity.value is not None:
            raise ValueError('Any quantity passed into a unit should not have any units or values.')
        self.quantity = quantity
        self.exponent = exponent
        self.powers = powers

    def convert_to_standard(self, value):
        new_value = value
        for unit, power in six.iteritems(self.powers):
            new_value = unit.convert_to_standard(new_value**(1 / power))**power
        return new_value

    def convert_from_standard(self, value):
        new_value = value
        for unit, power in six.iteritems(self.powers):
            new_value = unit.convert_from_standard(new_value**(1 / power))**power
        return new_value

    def __truediv__(self, other):
        other_inverted = other**(-1)
        new_unit = self * other_inverted
        return new_unit

    def __pow__(self, other):
        powers = {}
        if self.powers:
            for key, value in six.iteritems(self.powers):
                powers[key] = self.powers[key] * other
        else:
            new_key = copy.deepcopy(self)
            new_key.quantity = None
            powers[new_key] = other
        return Unit(self.quantity**other, powers=powers, exponent=self.exponent * other)

    def __mul__(self, other):

        quantity = self.quantity * other.quantity
        powers = {}
        normalised_values = {}
        if self.powers:
            for key, value in six.iteritems(self.powers):
                powers[key] = self.powers[key]
                normalised_key = copy.deepcopy(key)
                normalised_key.exponent = 1
                normalised_values[normalised_key] = key.exponent

        else:
            new_key = copy.deepcopy(self)
            new_key.quantity = None
            powers[new_key] = 1.0

        if other.powers:
            for key, value in six.iteritems(other.powers):
                normalised_key = copy.deepcopy(key)
                normalised_key.exponent = 1
                if normalised_key in normalised_values:
                    if key.exponent != normalised_values[normalised_key]:
                        raise NotImplementedError("The case when the two parts of a multiplication are of different magnitudes (e.g. kg/g) is currently unsupported")
                    else:
                        powers[key] += value
                else:
                    powers[key] = value

        else:
            normalised_other = copy.deepcopy(other)
            normalised_other.exponent = 1
            if normalised_other in normalised_values:
                if other.exponent != normalised_values[normalised_key]:
                    raise NotImplementedError("The case when the two parts of a multiplication are of different powers (e.g. kg/g) is currently unsupported")
                else:
                    powers[other] += 1.0
            else:
                powers[other] = 1.0
        return Unit(quantity=quantity, powers=powers, exponent=1)

    def __eq__(self, other):

        if len(self.powers) != 0:
            if self.powers == other.powers and self.exponent == other.exponent:
                return True
        else:
            if type(self) == type(other) and self.exponent == other.exponent and self.quantity == other.quantity:
                return True
        return False

    def __hash__(self):
        string = str(self.__class__.__name__)
        string += str(self.quantity)
        string += str(self.exponent)
        string += str(self.powers)
        return string.__hash__()

class DimensionlessUnit(Unit):

    def __init__(self):
        self.quantity = DimensionlessQuantity()
        self.exponent = 1
        self.powers = None

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value


class DimensionlessQuantity(QuantityModel):
    pass

