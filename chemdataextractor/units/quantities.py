# -*- coding: utf-8 -*-
"""
chemdataextractor.units.quantities.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Base types for making quantity models and units.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
from abc import abstractmethod
import logging

import six

from ..model import BaseModel, BaseType, FloatType, DictionaryType, ModelType

log = logging.getLogger(__name__)


class UnitType(BaseType):
    """
    A field representing a Unit of some type.
    """

    def __set__(self, instance, value):
        """
        Make sure that any units assigned to models have the same dimensions
        as the model.
        """

        if hasattr(value, 'dimensions'):
            if value.dimensions == instance.dimensions:
                instance._values[self.name] = self.process(value)
            else:
                instance._values[self.name] = None
        else:
            instance._values[self.name] = None

    def process(self, value):

        if isinstance(value, Unit):
            return value
        return None


class BaseDimension(BaseModel):

    @abstractmethod
    def __truediv__(self):
        pass

    @abstractmethod
    def __pow__(self):
        pass

    @abstractmethod
    def __mul__(self):
        pass

    @abstractmethod
    def __eq__(self):
        pass

    @abstractmethod
    def __hash__(self):
        pass


class Dimension(BaseDimension):
    """
    Class for dimensions. All actual quantities should be subclassed from this
    instead of BaseDimension. (This setup is as we otherwise wouldn't be able
    to make a DictionaryType with Dimension-type objects as keys)
    """

    dimensions = None
    # {ModelType(BaseDimension): FloatType()}

    """
    Operators are implemented so that composite dimensions can be created easily
    on the fly, for use in creating custom QuantityModels:

    class SpeedModel(QuantityModel):
        dimensions = Length() / Time()

    speed.value = 10
    speed.unit = Meter() / Second()
    print("Speed in miles per hour is: ", speed.convert_to(Mile() / Hour()))

    Which has an expected output of

    Speed in miles per hour is:  22.369418519393044
    """

    def __truediv__(self, other):

        other_inverted = other**(-1)
        new_model = self * other_inverted
        return new_model

    def __pow__(self, other):

        # Handle case that we have no dimensions, so we don't get things like dimensionless units squared.
        if isinstance(self, Dimensionless) or other == 0:
            new_model = Dimensionless()

        else:
            new_model = Dimension()
            dimensions = {}

            if self.dimensions is not None:
                for dimension, power in six.iteritems(self.dimensions):
                    dimensions[dimension] = power * other

            else:
                new_key = copy.deepcopy(self)
                dimensions[new_key] = other

            new_model.dimensions = dimensions

        return new_model

    def __mul__(self, other):

        new_model = Dimension()
        dimensions = {}

        if self.dimensions is not None:
            dimensions = copy.deepcopy(self.dimensions)

        else:
            new_key = copy.deepcopy(self)
            dimensions[new_key] = 1.0

        if other.dimensions is not None:
            for key, value in six.iteritems(other.dimensions):
                if self.dimensions is not None:
                    if key in self.dimensions:
                        dimensions[key] += value
                        if dimensions[key] == 0:
                            dimensions.pop(key)
                if type(self) == type(key):
                    dimensions[key] += value
                    if dimensions[key] == 0:
                        dimensions.pop(key)
                else:
                    dimensions[key] = value

        else:
            new_key = copy.deepcopy(other)
            if self.dimensions is not None:
                if new_key in self.dimensions:
                    dimensions[key] += value
                    if dimensions[key] == 0:
                        dimensions.pop(key)
            else:
                dimensions[new_key] = 1.0

        # Handle the case that we have ended up with no dimensions.
        dimensionless = Dimensionless()
        dimensions.pop(dimensionless, None)
        if len(dimensions) == 0:
            new_model = dimensionless
        else:
            new_model.dimensions = dimensions

        return new_model

    def __eq__(self, other):

        if type(self) != type(other):
            return False

        if self.dimensions is not None:
            if self.dimensions == other.dimensions:
                return True
        else:
            if type(self) == type(other):
                return True

        return False

    def __hash__(self):
        string = str(self.__class__.__name__)
        # TODO(ti250): use the serialize method instead once it's fixed in DictionaryType
        # string += str(self.serialize())
        string += str(self.dimensions)
        return string.__hash__()


class QuantityModel(BaseModel):
    """
    Class for quantities. All actual quantities should be subclassed from this
    instead of BaseQuantityModel. (This setup is as we otherwise wouldn't be able
    to make a list with QuantityModel-type objects as keys)
    """
    value = FloatType()
    unit = UnitType()
    dimensions = None

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

        other_inverted = other**(-1)
        new_model = self * other_inverted
        return new_model

    def __pow__(self, other):

        # Handle case that we have a dimensionless quantity, so we don't get dimensionless units squared.
        new_model = QuantityModel()
        new_model.dimensions = self.dimensions ** other
        if self.value is not None:
            new_model.value = self.value ** other
        if self.unit is not None:
            new_model.unit = self.unit ** other

        return new_model

    def __mul__(self, other):

        new_model = QuantityModel()
        new_model.dimensions = self.dimensions * other.dimensions
        if self.value is not None and other.value is not None:
            new_model.value = self.value * other.value
        if self.unit is not None and other.unit is not None:
            new_model.unit = self.unit * other.unit

        return new_model

    def convert_to(self, unit):
        """
        Convert from current units to the given units.
        Raises AttributeError if the current unit is not set.

        :param Unit unit: The Unit to convert to
        :returns: The value as expressed in the new unit
        :rtype: float
        """
        if self.unit:
            return self.convert(self.unit, unit)
        raise AttributeError("Unit to convert from not set")

    def convert(self, from_unit, to_unit):
        """
        Convert between the given units.
        If no units have been set for this model, assumes that it's in standard units.

        :param Unit from_unit: The Unit to convert from
        :param Unit to_unit: The Unit to convert to
        :returns: The value as expressed in the new unit
        :rtype: float
        """
        if to_unit.dimensions == from_unit.dimensions:
            standard_val = from_unit.convert_to_standard(self.value)
            return to_unit.convert_from_standard(standard_val)
        else:
            raise ValueError("Unit to convert to must have same dimensions as current unit")
        raise AttributeError("Unit to convert from not set")


class Unit(object):
    # TODO: Currently exponent does nothing
    """
    Object represeting units. Implement subclasses of this of basic units, e.g.
    units like meters, seconds, and Kelvins that are already implemented.
    These can then be combined by simply dividing or multiplying them to create
    more complex units. Alternatively, one can create these by subclassing Unit
    and setting the powers parameter as desired. For example, a speed could be
    represented as either:

    speedunit = Meter() / Second()

    or

    class SpeedUnit(Unit):

        def__init__(self, exponent=1.0):
            super(SpeedUnit, self).__init__(Length()/Time(),
                                            powers={Meter():1.0, Second():-1.0} )

    speedunit = SpeedUnit()

    and either method should produce the same results.
    """

    def __init__(self, dimensions, exponent=1.0, powers=None):
        """
        Creates a unit object. Subclass this to create concrete units. For examples,
        see lenghts.py and times.py

        .. note::
            Any quantity passed into the intialiser should not have units or values

        :param Dimension dimensions: The dimensions this unit is for, e.g. Temperature
        :param float exponent: The exponent of the unit. e.g. km would be meters with an exponent of 3
        :param Dictionary{Unit : float} powers: For representing any more complicated units, e.g. m/s may have this parameter set to {Meter():1.0, Second():-1.0}
        """
        self.dimensions = dimensions
        self.exponent = exponent
        self.powers = powers

    def convert_to_standard(self, value):
        """
        Converts from this unit to the standard value, usually the SI unit.
        Overload this in child classes when implementing new units.

        :param float value: The value to convert to standard units
        """
        new_value = value
        for unit, power in six.iteritems(self.powers):
            new_value = unit.convert_to_standard(new_value**(1 / power))**power
        return new_value

    def convert_from_standard(self, value):
        """
        Converts to this unit from the standard value, usually the SI unit.
        Overload this in child classes when implementing new units.

        :param float value: The value to convert from standard units
        """
        new_value = value
        for unit, power in six.iteritems(self.powers):
            new_value = unit.convert_from_standard(new_value**(1 / power))**power
        return new_value

    """
    Operators are implemented for the easy creation of complicated units out of
    simpler, fundamental units. This means that every combination of exponents
    and units need not be accounted for.
    """

    def __truediv__(self, other):
        other_inverted = other**(-1.0)
        new_unit = self * other_inverted
        return new_unit

    def __pow__(self, other):

        # Handle dimensionless units so we don't get things like dimensionless units squared.
        if isinstance(self, DimensionlessUnit) or other == 0:
            new_unit = DimensionlessUnit()
            return new_unit

        powers = {}
        if self.powers:
            for key, value in six.iteritems(self.powers):
                powers[key] = self.powers[key] * other
        else:
            new_key = copy.deepcopy(self)
            new_key.dimensions = None
            powers[new_key] = other
        return Unit(self.dimensions**other, powers=powers, exponent=self.exponent * other)

    def __mul__(self, other):

        dimensions = self.dimensions * other.dimensions
        powers = {}
        # normalised_values is created as searching for keys won't always work
        # when the different units have different exponents, even though
        # they are essentially the same unit and they should be unified.
        normalised_values = {}
        if self.powers:
            for key, value in six.iteritems(self.powers):
                powers[key] = self.powers[key]
                normalised_key = copy.deepcopy(key)
                normalised_key.exponent = 1.0
                normalised_values[normalised_key] = key.exponent

        else:
            new_key = copy.deepcopy(self)
            new_key.dimensions = None
            powers[new_key] = 1.0
            normalised_key = copy.deepcopy(new_key)
            normalised_key.exponent = 1.0
            normalised_values[normalised_key] = self.exponent

        if other.powers:
            for key, value in six.iteritems(other.powers):
                normalised_key = copy.deepcopy(key)
                normalised_key.exponent = 1.0
                if normalised_key in normalised_values.keys():
                    if key.exponent != normalised_values[normalised_key]:
                        raise NotImplementedError("The case when the two parts of a multiplication are of different magnitudes (e.g. kg/g) is currently unsupported")
                    else:
                        powers[key] += value
                        if powers[key] == 0:
                            powers.pop(key)
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
                    if powers[key] == 0:
                        powers.pop(key)
            else:
                powers[other] = 1.0

        powers.pop(DimensionlessUnit(), None)

        if len(powers) == 0:
            return DimensionlessUnit()

        return Unit(dimensions=dimensions, powers=powers, exponent=1)

    # eq and hash implemented so Units can be used as keys in dictionaries

    def __eq__(self, other):
        if not isinstance(other, Unit):
            return False
        if self.powers:
            if self.powers == other.powers and self.exponent == other.exponent:
                return True
        else:
            if type(self) == type(other) and self.exponent == other.exponent and self.dimensions == other.dimensions:
                return True
        return False

    def __hash__(self):
        string = str(self.__class__.__name__)
        string += str(self.dimensions)
        string += str(float(self.exponent))
        string += str(self.powers)
        return string.__hash__()


class DimensionlessUnit(Unit):
    # Special case to handle dimensionless quantities.

    def __init__(self):
        self.dimensions = Dimensionless()
        self.exponent = 1
        self.powers = None

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value


class Dimensionless(Dimension):
    # Special case to handle dimensionless quantities.
    pass


class DimensionlessModel(QuantityModel):
    # Special case to handle dimensionless quantities

    dimensions = Dimensionless()
