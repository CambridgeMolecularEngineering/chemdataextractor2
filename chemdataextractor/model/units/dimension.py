# -*- coding: utf-8 -*-
"""
Base types for dimensions. Refer to the example on :ref:`creating new units and dimensions<creating_units>` for more detail on how to create your own dimensions.

.. codeauthor:: Taketomo Isazawa <ti250@cam.ac.uk>
"""

import six
import copy
from abc import abstractmethod, ABCMeta
from ..base import BaseModel, BaseType, FloatType, StringType, ListType


@property
def standard_units(self):
    if self._standard_units and len(self._standard_units) == 1:
        for unit, power in six.iteritems(self._standard_units):
            if power == 1.:
                return unit
            else:
                return unit ** power
    product_unit = None
    for (unit, power) in six.iteritems(self._standard_units):
        if not product_unit:
            product_unit = unit ** power
        else:
            product_unit = product_unit * (unit ** power)
    return product_unit


@standard_units.setter
def standard_units(self, value):
    self._standard_units = {value: 1.0}


class _DimensionMeta(ABCMeta):

    def __new__(mcs, name, bases, attrs):
        cls = super(_DimensionMeta, mcs).__new__(mcs, name, bases, attrs)
        if hasattr(cls, 'constituent_dimensions') and cls.constituent_dimensions is not None:
            cls.units_dict = copy.copy(cls.constituent_dimensions.units_dict)
            cls._dimensions = cls.constituent_dimensions._dimensions
            cls._standard_units = cls.constituent_dimensions._standard_units
        cls.standard_units = standard_units
        return cls

    def __setattr__(cls, key, value):
        if key == 'standard_units' and not isinstance(value, property):
            cls._standard_units = {value: 1.0}
        else:
            return super(_DimensionMeta, cls).__setattr__(key, value)


class Dimension(six.with_metaclass(_DimensionMeta)):
    """
    Class for representing physical dimensions.
    """

    constituent_dimensions = None
    """
    Used for creating composite dimensions.
    It is of type :class:`~chemdataextractor.model.units.dimension.Dimension`.
    An example would be speed, in which case we would have::

        class Speed(Dimension):
            constituent_dimensions = Length() / Time()
    """

    _dimensions = None
    """
    Used to represent composite dimensions.
    It is of type dictionary{:class:`Dimension`: :class:`float`}.
    An example would be speed, in which case we would have::

        Speed._dimensions = {Length(): 1.0, Time(): -1.0}

    Not to be set by the user.
    """

    units_dict = {}
    """
    Used for extracting units with these dimensions.
    It is of type dictionary{:class:`chemdataextractor.parse.element` : :class:`~chemdataextractor.model.units.unit.Unit` or :class:`None`}.

    An :class:`~chemdataextractor.parse.element` is the key for :class:`None` when an element is needed for autoparsing
    to work correctly, but one does not want to take account of this when extracting a unit from a merged string.

    An example of this is °C, which is always split into two tokens, so we need to be able to capture ° and C
    separately using elements from the :attr:`units_dict`, but we do not want this to affect :meth:`~chemdataextractor.parse.base.BaseParser.extract_units`,
    to which the single string '°C' is passed in. As a solution, we have the following :attr:`units_dict`::

        units_dict = {R('°?(((K|k)elvin(s)?)|K)\.?', group=0): Kelvin,
              R('(°C|((C|c)elsius))\.?', group=0): Celsius,
              R('°?((F|f)ahrenheit|F)\.?', group=0): Fahrenheit,
              R('°|C', group=0): None}

    .. note::

        The units_dict has been extensively tested using regex elements, and while in theory it may work with other parse
        elements, it is strongly recommended that you use a regex element.
        If a regex element is specified, it should

        - Not have a $ symbol at the end: the units can be passed in with numbers or other symbols after it, and these are also used in the autoparser to find candidate tokens which may contain units, and a $ symbol at the end would stop this from working
        - Have the group attribute set to 0. Unless this is set, the default behaviour of the regex element is to return the whole token in which the match was found. This is unhelpful behaviour for our logic for extracting units, as we want to extract only the exact characters that matched the unit.
    """

    _standard_units = None

    standard_units = None
    """
    The standard units for this dimension. Of type :class:`~chemdataextractor.model.units.unit.Unit`.

    Set this attribute when creating a new dimension to make converting to the standard units easy via
    :meth:`~chemdataextractor.model.units.quantity_model.QuantityModel.convert_to_standard`, and to make it clear in the code what the
    standard units are.

    The standard units when you multiply dimensions together/ have composite dimensions are automatically handled by the class.
    """

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

            if self._dimensions is not None:
                for dimension, power in six.iteritems(self._dimensions):
                    dimensions[dimension] = power * other

            else:
                new_key = copy.deepcopy(self)
                dimensions[new_key] = other

            new_model._dimensions = dimensions
            new_model.units_dict = copy.copy(self.units_dict)
            if self._standard_units is not None:
                _standard_units = {}
                for unit, power in six.iteritems(self._standard_units):
                    _standard_units[unit] = power * other
                new_model._standard_units = _standard_units
            else:
                new_model._standard_units = None
        return new_model

    def __mul__(self, other):
        new_model = Dimension()
        dimensions = {}

        if self._dimensions is not None:
            dimensions = copy.deepcopy(self._dimensions)

        else:
            new_key = copy.deepcopy(self)
            dimensions[new_key] = 1.0

        if other._dimensions is not None:
            for key, value in six.iteritems(other._dimensions):
                if self._dimensions is not None and key in self._dimensions.keys():
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
            if self._dimensions is not None:
                if new_key in self._dimensions:
                    dimensions[new_key] += 1.0
                    if dimensions[new_key] == 0:
                        dimensions.pop(new_key)
                else:
                    dimensions[new_key] = 1.0
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
            new_model._dimensions = dimensions

        new_model.units_dict = {}
        # Look at whether the units_dict for self is different from the units_dict for each of the dimensions combined.
        # If they're the same, then we can start from scratch, if they're different, that means we have some things that
        # are specific to the parent, e.g. J for energy as opposed to as a combination of SI, so we need to
        # preserve the units_dict.
        trial_units_dict = {}
        if self._dimensions:
            for dimension in self._dimensions.keys():
                trial_units_dict.update(dimension.units_dict)
        if trial_units_dict != self.units_dict:
            new_model.units_dict = copy.copy(self.units_dict)

        trial_units_dict_other = {}
        if other._dimensions:
            for dimension in other._dimensions.keys():
                trial_units_dict_other.update(dimension.units_dict)
        if trial_units_dict_other != other.units_dict:
            new_model.units_dict.update(other.units_dict)

        for dimension in dimensions.keys():
            new_model.units_dict.update(dimension.units_dict)

        if self._standard_units is not None and other._standard_units is not None:
            _standard_units = {}
            for unit, power in six.iteritems(self._standard_units):
                if unit not in _standard_units.keys():
                    _standard_units[unit] = power
                else:
                    _standard_units[unit] += power

            for unit, power in six.iteritems(other._standard_units):
                if unit not in _standard_units.keys():
                    _standard_units[unit] = power
                else:
                    _standard_units[unit] += power
            new_model._standard_units = _standard_units

        else:
            new_model._standard_units = None

        return new_model

    def __eq__(self, other):
        if not isinstance(other, Dimension):
            return False

        if self._dimensions is not None:
            if other._dimensions is not None:
                if self._dimensions == other._dimensions:
                    return True
            else:
                if (self**1.0)._dimensions == (other**1.0)._dimensions:
                    return True
        elif other._dimensions is not None:
            if other._dimensions == (self**1.0)._dimensions:
                return True
        else:
            if type(self) == type(other):
                return True

        return False

    def __hash__(self):
        string = str(self.__class__.__name__)
        # TODO: Should use the _dimensions as part of the hash as well, but does not seem to work.
        # Can't just hash the dictionary as that would lead to two units that are actually equal hashing to different values depending on the order in which the dictionary is iterated through, which is not neccesarily deterministic. Better to have it this way, as it's okay for two hashes to clash.
        # if self._dimensions is not None:
        #     for key in sorted(str(six.iteritems(self._dimensions))):
        #         string += (str(key))
        return string.__hash__()

    def __str__(self):
        string = ''
        if self._dimensions is not None:
            name_list = []
            for key, value in six.iteritems(self._dimensions):
                name_list.append((type(key).__name__ + '^(' + str(value) + ')  '))
            for name in sorted(name_list):
                string += name
            string = string[:-2]
        else:
            string += type(self).__name__
        return string


class Dimensionless(Dimension):
    """Special case to handle dimensionless quantities."""

    def __bool__(self):
        return False
