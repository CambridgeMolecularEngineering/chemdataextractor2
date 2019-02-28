# -*- coding: utf-8 -*-
"""
Base types for dimensions.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

import six
import copy
from abc import abstractmethod
from ..base import BaseModel, BaseType, FloatType, StringType, ListType


class Dimension(object):
    """
    Class for representing physical dimensions.
    """

    dimensions = None
    """
    Used to represent composite dimensions.
    It is of type dictionary{:class:`Dimension`: :class:`float`}.
    An example would be speed, in which case we would have::

        dimensions = {Length(): 1.0, Time(): -1.0}
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
            new_model.units_dict = copy.copy(self.units_dict)
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
            new_model.dimensions = dimensions

        new_model.units_dict = {}
        for dimension in dimensions.keys():
            new_model.units_dict.update(dimension.units_dict)
        return new_model

    def __eq__(self, other):

        if not isinstance(other, Dimension):
            return False

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
        # TODO: Should use the dimensions as part of the hash as well, but does not seem to work.
        # Can't just hash the dictionary as that would lead to two units that are actually equal hashing to different values depending on the order in which the dictionary is iterated through, which is not neccesarily deterministic. Better to have it this way, as it's okay for two hashes to clash.
        # if self.dimensions is not None:
        #     for key in sorted(str(six.iteritems(self.dimensions))):
        #         string += (str(key))
        return string.__hash__()

    def __str__(self):
        string = ''
        if self.dimensions is not None:
            for key, value in six.iteritems(self.dimensions):
                string += (type(key).__name__ + '^(' + str(value) + ')  ')
        else:
            string += type(self).__name__
        return string


class Dimensionless(Dimension):
    """Special case to handle dimensionless quantities."""
    def __bool__(self):
        return False
