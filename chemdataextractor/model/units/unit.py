# -*- coding: utf-8 -*-
"""
Base types for making units. Refer to the example on :ref:`creating new units and dimensions<creating_units>` for more detail on how to create your own units.

.. codeauthor:: Taketomo Isazawa <ti250@cam.ac.uk>
"""

import six
import copy
from abc import abstractmethod
from .dimension import Dimensionless
from ..base import BaseModel, BaseType, FloatType, StringType, ListType


class UnitType(BaseType):
    """
    A field containing a :class:`Unit` of some type.
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

    def is_empty(self, value):
        if isinstance(value, Unit):
            return False
        return True


class MetaUnit(type):
    """
    Metaclass to ensure that all subclasses of :class:`Unit` take the magnitude into account
    when converting to standard units.
    """

    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)

        if hasattr(cls, 'convert_value_to_standard'):
            sub_convert_to_standard = getattr(cls, 'convert_value_to_standard')

            def new_convert_to_standard(self, value):
                val = value * 10 ** (self.magnitude + self.base_magnitude)
                return sub_convert_to_standard(self, val)
            setattr(cls, 'convert_value_to_standard', new_convert_to_standard)

        if hasattr(cls, 'convert_value_from_standard'):
            sub_convert_from_standard = getattr(cls, 'convert_value_from_standard')

            def new_convert_from_standard(self, value):
                val = value * 10**(-1 * (self.magnitude + self.base_magnitude))
                return sub_convert_from_standard(self, val)
            setattr(cls, 'convert_value_from_standard', new_convert_from_standard)

        if hasattr(cls, 'convert_error_to_standard'):
            sub_convert_err_to_standard = getattr(cls, 'convert_error_to_standard')

            def new_convert_err_to_standard(self, value):
                val = value * 10**(self.magnitude + self.base_magnitude)
                return sub_convert_err_to_standard(self, val)
            setattr(cls, 'convert_error_to_standard', new_convert_err_to_standard)

        if hasattr(cls, 'convert_error_from_standard'):
            sub_convert_err_from_standard = getattr(cls, 'convert_error_from_standard')

            def new_convert_err_from_standard(self, value):
                val = value * 10**(-1 * (self.magnitude + self.base_magnitude))
                return sub_convert_err_from_standard(self, val)
            setattr(cls, 'convert_error_from_standard', new_convert_err_from_standard)

        if hasattr(cls, 'constituent_units') and cls.constituent_units is not None:
            cls.base_magnitude = cls.constituent_units.magnitude

            def new_initializer(self, magnitude=0.0):
                Unit.__init__(self, cls.constituent_units.dimensions, magnitude,
                              powers=cls.constituent_units.powers)

            cls.__init__ = new_initializer

        return cls


@six.add_metaclass(MetaUnit)
class Unit(object):
    """
    Object represeting units. Implement subclasses of this for basic units.
    Units like meters, seconds, and Kelvins are already implemented in ChemDataExtractor.
    These can then be combined by simply dividing or multiplying them to create
    more complex units. Alternatively, one can create these by subclassing Unit
    and setting the powers parameter as desired. For example, a speed could be
    represented as either:

    .. code-block:: python

        speedunit = Meter() / Second()

    or

    .. code-block:: python

        class SpeedUnit(Unit):

            def __init__(self, magnitude=1.0):
                super(SpeedUnit, self).__init__(Length()/Time(),
                                                powers={Meter():1.0, Second():-1.0} )

        speedunit = SpeedUnit()

    and either method should produce the same results.

    Any subclass of Unit which represents a real unit should implement the following methods:

    - convert_value_to_standard
    - convert_value_from_standard
    - convert_error_to_standard
    - convert_error_from_standard

    These methods ensure that Units can be seamlessly converted to other ones. Any
    magnitudes placed in front of the units, e.g. kilometers, are handled automatically.
    Care must be taken that the 'standard' unit chosen is obvious, consistent, and documented,
    else another user may implement new units with the same dimensions but a different
    standard unit, resulting in unexpected errors. To ensure correct behaviour, one should also define
    the standard unit in code by setting the corresponding dimension's
    :attr:`~chemdataextractor.model.units.dimension.Dimension.standard_units`, unless the
    dimension is a composite one, in which case the standard unit can often be inferred from
    the constituent units' standard untis
    """

    base_magnitude = 0.0
    constituent_units = None
    """
    :class:`~chemdataextractor.model.units.unit.Unit` instance for showing constituent units.
    Used for creating more complex models. An example would be::

        class Newton(Unit):
            constituent_units = Gram(magnitude=3.0) * Meter() * (Second()) ** (-2.0)
    """

    def __init__(self, dimensions, magnitude=0.0, powers=None):
        """
        Creates a unit object. Subclass Unit to create concrete units. For examples,
        see lengths.py and times.py

        :param Dimension dimensions: The dimensions this unit is for, e.g. Temperature
        :param float magnitude: (Optional) The magnitude of the unit. e.g. km would be meters with an magnitude of 3
        :param powers: (Optional) For representing any more complicated units, e.g. m/s may have this parameter set to {Meter():1.0, Second():-1.0}
        :type powers: dict[Unit : float]
        """
        self.dimensions = dimensions
        self.magnitude = magnitude
        self.powers = powers

    def convert_value_to_standard(self, value):
        """
        Converts from this unit to the standard value, usually the SI unit.
        Overload this in child classes when implementing new units.

        :param float value: The value to convert to standard units
        """
        for unit, power in six.iteritems(self.powers):
            value = unit.convert_value_to_standard(value**(1 / power))**power
        return value

    def convert_value_from_standard(self, value):
        """
        Converts to this unit from the standard value, usually the SI unit.
        Overload this in child classes when implementing new units.

        :param float value: The value to convert from standard units
        """
        for unit, power in six.iteritems(self.powers):
            value = unit.convert_value_from_standard(value**(1 / power))**power
        return value

    def convert_error_to_standard(self, error):
        """
        Converts from this error to the standard value, usually the SI unit.
        Overload this in child classes when implementing new units

        :param float error: The error to convert to standard units
        :return float error: The error converted to standard units:
        """

        for unit, power in six.iteritems(self.powers):
            error = unit.convert_error_to_standard(error**(1 / power))**power
        return error

    def convert_error_from_standard(self, error):
        """
        Converts to this error from the standard value, usually the SI unit.
        Overload this in child classes when implementing new units

        :param float error: The error to convert from standard units
        :return float error: The error converted from standard units:
        """

        for unit, power in six.iteritems(self.powers):
            error = unit.convert_error_from_standard(error**(1 / power))**power
        return error


    """
    Operators are implemented for the easy creation of complicated units out of
    simpler, fundamental units. This means that every combination of magnitudes
    and units need not be accounted for.
    """

    def __truediv__(self, other):
        other_inverted = other**(-1.0)
        new_unit = self * other_inverted
        return new_unit

    def __pow__(self, other):

        # Handle dimensionless units so we don't get things like dimensionless units squared.
        if isinstance(self, DimensionlessUnit) or other == 0:
            new_unit = DimensionlessUnit(magnitude=self.magnitude * other)
            return new_unit

        powers = {}
        if self.powers:
            for key, value in six.iteritems(self.powers):
                powers[key] = self.powers[key] * other
        else:
            new_key = copy.deepcopy(self)
            new_key.magnitude = 0.0
            powers[new_key] = other
        return Unit(self.dimensions**other, powers=powers, magnitude=self.magnitude * other)

    def __mul__(self, other):

        dimensions = self.dimensions * other.dimensions
        powers = {}
        # normalised_values is created as searching for keys won't always work
        # when the different units have different magnitudes, even though
        # they are essentially the same unit and they should be unified.
        normalised_values = {}
        magnitude = self.magnitude + other.magnitude

        if self.powers:
            for key, value in six.iteritems(self.powers):
                powers[key] = self.powers[key]
                normalised_key = copy.deepcopy(key)
                normalised_key.magnitude = 0.0
                normalised_values[normalised_key] = key.magnitude

        else:
            if not isinstance(self, DimensionlessUnit):
                new_key = copy.deepcopy(self)
                new_key.magnitude = 0.0
                powers[new_key] = 1.0
                normalised_values[new_key] = self.magnitude

        if other.powers:
            for key, value in six.iteritems(other.powers):
                normalised_key = copy.deepcopy(key)
                normalised_key.magnitude = 0.0
                if normalised_key in normalised_values.keys():
                    powers[key] += value
                    if powers[key] == 0:
                        powers.pop(key)
                else:
                    powers[normalised_key] = value

        else:
            if not isinstance(other, DimensionlessUnit):
                normalised_other = copy.deepcopy(other)
                normalised_other.magnitude = 0.0
                if normalised_other in normalised_values:
                    powers[normalised_other] += 1.0
                    if powers[normalised_other] == 0:
                        powers.pop(other)
                else:
                    powers[normalised_other] = 1.0
        # powers.pop(DimensionlessUnit(), None)
        if len(powers) == 0:
            return DimensionlessUnit(magnitude=magnitude)

        return Unit(dimensions=dimensions, powers=powers, magnitude=magnitude)

    # eq and hash implemented so Units can be used as keys in dictionaries

    def __eq__(self, other):
        if not isinstance(other, Unit):
            return False
        if self.powers:
            if other.powers:
                if self.powers == other.powers and self.magnitude == other.magnitude:
                    return True
            else:
                if self.powers == (other**1.0).powers:
                    return True
        elif other.powers:
            if other.powers == (self**1.0).powers:
                return True
        else:
            if type(self) == type(other) and self.magnitude == other.magnitude and self.dimensions == other.dimensions:
                return True
        return False

    def __hash__(self):
        string = str(self.__class__.__name__)
        string += str(self.dimensions.__hash__())
        string += str(float(self.magnitude))
        # TODO: Should use the powers as part of the hash as well, but does not seem to work.
        # Can't just hash the dictionary as that would lead to two units that are actually equal hashing to different values depending on the order in which the dictionary is iterated through, which is not neccesarily deterministic. Better to have it this way, as it's okay for two hashes to clash.
        # if self.powers is not None:
        #     for key in sorted(str(six.iteritems(self.powers))):
        #         string += str(key)
        return string.__hash__()

    def __str__(self):
        string = ''
        if self.magnitude != 0:
            string += '(10^' + str(self.magnitude) + ') * '
        name_list = []
        if self.powers is not None:
            for key, value in six.iteritems(self.powers):
                name_list.append((type(key).__name__ + '^(' + str(value) + ')  '))
            for name in sorted(name_list):
                string += name
            string = string[:-2]
        else:
            string += type(self).__name__
        return string


class DimensionlessUnit(Unit):
    """Special case to handle dimensionless quantities."""

    def __init__(self, magnitude=0.0):
        """
        :param float magnitude: The magnitude of the unit.
        """
        self.dimensions = Dimensionless()
        self.magnitude = magnitude
        self.powers = None

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value
