# -*- coding: utf-8 -*-
"""
chemdataextractor.units.quantities.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Base types for making quantity models, dimensions, and units.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractmethod
from ...base_model import BaseModel, BaseType, FloatType, StringType

import copy
import logging
import six



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

    def serialize(self, value, primitive=False):
        return str(value**1.0)


class OptionalRangeType(BaseType):
    """
    Values stored in QuantityModels can be a single value or a
    range. e.g. an IR peak could be written as either a single value or a range
    of values, between two values. This is a field to allow for either.
    """

    def __init__(self, value_type, **kwargs):
        """
        :param BaseType value_type: The type of the value that may have a range. This type's process function is also called.
        :param default: (Optional) The default value for this field if none is set.
        :param bool null: (Optional) Include in serialized output even if value is None. Default False.
        :param bool required: (Optional) Whether a value is required. Default False.
        :param bool contextual: (Optional) Whether this value is contextual. Default False.
        """
        super(OptionalRangeType, self).__init__(**kwargs)
        self.value_type = value_type

    def process(self, value):
        if hasattr(value, '__len__'):
            if len(value) == 2:
                result = []
                for val in value:
                    result.append(self.value_type.process(val))
                try:
                    # Try to sort the values if possible
                    if result[0] > result[1]:
                        result = [result[1], result[0]]
                except NotImplementedError:
                    pass
                return result
        else:
            return self.value_type.process(value)


class BaseDimension(BaseModel):

    @abstractmethod
    def __truediv__(self, a):
        pass

    @abstractmethod
    def __pow__(self):
        pass

    @abstractmethod
    def __mul__(self, a):
        pass

    @abstractmethod
    def __eq__(self, a):
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

    units_dict = {}

    """
    Set up units_dict with {element : Unit}, where element is an element from parse.elements.
    Examples can be seen in temperatures.py
    """

    @classmethod
    def composite_dimension(cls, with_dimensions):
        """
        Creates a new Dimension subclass composed of the dimensions given.
        .. note::
            This returns a subclass of Dimension, not an instance of a subclass of Dimension.
        :param Dimension with_dimensions: The dimensions for the new unit subclass to be created
        :returns: The new composite dimension
        :rtype: subclass of Dimension
        """
        new_dimension = type(str(with_dimensions), (cls, ), {})
        new_dimension.dimensions = with_dimensions.dimensions
        new_dimension.units_dict = copy.copy(with_dimensions.units_dict)
        return new_dimension

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

        other_inverted = other**(-1.0)
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
                if self.dimensions is not None and key in self.dimensions.keys():
                    dimensions[key] += value
                    if dimensions[key] == 0:
                        dimensions.pop(key)
                elif type(self) == type(key):
                    dimensions[key] += value
                    if dimensions[key] == 0:
                        dimensions.pop(key)
                else:
                    dimensions[key] = value

        else:
            new_key = copy.deepcopy(other)
            if self.dimensions is not None:
                if new_key in self.dimensions:
                    dimensions[new_key] += 1.0
                    if dimensions[new_key] == 0:
                        dimensions.pop(new_key)
            elif self == new_key:
                dimensions[new_key] += 1.0
                if dimensions[new_key] == 0:
                    dimensions.pop(new_key)
            else:
                dimensions[new_key] = 1.0
        # Handle the case that we have ended up with no dimensions.
        dimensionless = Dimensionless()
        dimensions.pop(dimensionless, None)
        if len(dimensions) == 0:
            new_model = dimensionless
        else:
            new_model.dimensions = dimensions

        new_model.units_dict = {}
        for dimension in dimensions.keys():
            new_model.units_dict.update(dimension.units_dict)

        return new_model

    def __eq__(self, other):

        if self.dimensions is not None:
            if other.dimensions is not None:
                if self.dimensions == other.dimensions:
                    return True
            else:
                if self.dimensions == (other**1.0).dimensions:
                    return True
        elif other.dimensions is not None:
            if other.dimensions == (self**1.0).dimensions:
                return True
        else:
            if type(self) == type(other):
                return True

        return False

    def __hash__(self):
        string = str(self.__class__.__name__)
        string += str(self.dimensions)
        return string.__hash__()

    def __str__(self):
        string = ''
        if self.dimensions is not None:
            for key, value in six.iteritems(self.dimensions):
                string += (type(key).__name__ + '^(' + str(value) + ')  ')
        else:
            string += type(self).__name__
        return string


class QuantityModel(BaseModel):
    """
    Class for quantities. All actual quantities should be subclassed from this
    instead of BaseQuantityModel. (This setup is as we otherwise wouldn't be able
    to make a list with QuantityModel-type objects as keys)
    """
    raw_value = StringType()
    raw_units = StringType()
    value = OptionalRangeType(FloatType())
    units = UnitType()
    error = FloatType()
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
            if type(self.value) is list and type(other.value) is list:
                # The following always encompasses the whole range because
                # OptionalRangeType tries to always sort the lists
                new_val = [self.value[0] * other.value[0],
                           self.value[1] * other.value[1]]
                new_model.value = new_val
            elif type(self.value) is list:
                new_val = [self.value[0] * other.value,
                           self.value[1] * other.value]
                new_model.value = new_val
            elif type(self.value) is not list and type(other.value) is list:
                new_val = [self.value * other.value[0],
                           self.value * other.value[1]]
                new_model.value = new_val
            else:
                new_model.value = self.value * other.value
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
            return self.convert(self.units, unit)
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
        if self.value is not None:
            if to_unit.dimensions == from_unit.dimensions:
                if type(self.value) is list:
                    standard_vals = [from_unit.convert_to_standard(self.value[0]),
                                     from_unit.convert_to_standard(self.value[1])]
                    return [to_unit.convert_from_standard(standard_vals[0]),
                            to_unit.convert_from_standard(standard_vals[1])]
                else:
                    standard_val = from_unit.convert_to_standard(self.value)
                    return to_unit.convert_from_standard(standard_val)
            else:
                raise ValueError("Unit to convert to must have same dimensions as current unit")
            raise AttributeError("Unit to convert from not set")
        else:
            raise AttributeError("Value for model not set")

    def __str__(self):
        string = 'Quantity with ' + self.dimensions.__str__() + ', ' + self.units.__str__()
        string += ' and a value of ' + str(self.value)
        return string


class MetaUnit(type):
    """
    Metaclass to ensure that all subclasses of Unit take the exponent into account
    when converting to standard units.
    """

    def __new__(cls, name, bases, attrs):
        instance = type.__new__(cls, name, bases, attrs)

        if hasattr(instance, 'convert_to_standard'):
            sub_convert_to_standard = getattr(instance, 'convert_to_standard')

            def new_convert_to_standard(self, value):
                val = value * 10**self.exponent
                return sub_convert_to_standard(self, val)
            setattr(instance, 'convert_to_standard', new_convert_to_standard)

        if hasattr(instance, 'convert_from_standard'):
            sub_convert_from_standard = getattr(instance, 'convert_from_standard')

            def new_convert_from_standard(self, value):
                val = value * 10**(-1 * self.exponent)
                return sub_convert_from_standard(self, val)
            setattr(instance, 'convert_from_standard', new_convert_from_standard)

        return instance


@six.add_metaclass(MetaUnit)
class Unit(object):
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

    @classmethod
    def composite_unit(cls, with_units):
        """
        Creates a new Unit subclass composed of the units given.
        .. note::
            This returns a subclass of Unit, not an instance of a subclass of Unit.
        :param Unit with_units: The units for the new unit subclass to be created
        :returns: The new composite unit
        :rtype: subclass of Unit
        """
        new_unit = type(str(with_units), (cls, ), {})

        def new_initializer(self, exponent=with_units.exponent):
            Unit.__init__(with_units.dimensions, exponent, powers=with_units.powers)

        new_unit.__init__ = new_initializer
        return new_unit

    def __init__(self, dimensions, exponent=0.0, powers=None):
        """
        Creates a unit object. Subclass this to create concrete units. For examples,
        see lenghts.py and times.py

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
            new_unit = DimensionlessUnit(exponent=self.exponent * other)
            return new_unit

        powers = {}
        if self.powers:
            for key, value in six.iteritems(self.powers):
                powers[key] = self.powers[key] * other
        else:
            new_key = copy.deepcopy(self)
            new_key.exponent = 0.0
            powers[new_key] = other
        return Unit(self.dimensions**other, powers=powers, exponent=self.exponent * other)

    def __mul__(self, other):

        dimensions = self.dimensions * other.dimensions
        powers = {}
        # normalised_values is created as searching for keys won't always work
        # when the different units have different exponents, even though
        # they are essentially the same unit and they should be unified.
        normalised_values = {}
        exponent = self.exponent + other.exponent

        if self.powers:
            for key, value in six.iteritems(self.powers):
                powers[key] = self.powers[key]
                normalised_key = copy.deepcopy(key)
                normalised_key.exponent = 0.0
                normalised_values[normalised_key] = key.exponent

        else:
            if not isinstance(self, DimensionlessUnit):
                new_key = copy.deepcopy(self)
                new_key.exponent = 0.0
                powers[new_key] = 1.0
                normalised_values[new_key] = self.exponent

        if other.powers:
            for key, value in six.iteritems(other.powers):
                normalised_key = copy.deepcopy(key)
                normalised_key.exponent = 0.0
                if normalised_key in normalised_values.keys():
                    powers[key] += value
                    if powers[key] == 0:
                        powers.pop(key)
                else:
                    powers[normalised_key] = value

        else:
            if not isinstance(other, DimensionlessUnit):
                normalised_other = copy.deepcopy(other)
                normalised_other.exponent = 0.0
                if normalised_other in normalised_values:
                    powers[normalised_other] += 1.0
                    if powers[normalised_other] == 0:
                        powers.pop(other)
                else:
                    powers[normalised_other] = 1.0
        # powers.pop(DimensionlessUnit(), None)
        if len(powers) == 0:
            return DimensionlessUnit(exponent=exponent)

        return Unit(dimensions=dimensions, powers=powers, exponent=exponent)

    # eq and hash implemented so Units can be used as keys in dictionaries

    def __eq__(self, other):
        if not isinstance(other, Unit):
            return False
        if self.powers:
            if other.powers:
                if self.powers == other.powers and self.exponent == other.exponent:
                    return True
            else:
                if self.powers == (other**1.0).powers:
                    return True
        elif other.powers:
            if other.powers == (self**1.0).dimensions:
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

    def __str__(self):
        string = ''
        if self.exponent != 0:
            string += '(10^' + str(self.exponent) + ') * '
        if self.powers is not None:
            for key, value in six.iteritems(self.powers):
                string += (type(key).__name__ + '^(' + str(value) + ')  ')
            string = string[:-2]
        else:
            string += type(self).__name__
        return string


class DimensionlessUnit(Unit):
    # Special case to handle dimensionless quantities.

    def __init__(self, exponent = 0.0):
        self.dimensions = Dimensionless()
        self.exponent = exponent
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
