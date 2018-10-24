from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
from abc import ABCMeta, ABC
from collections import MutableSequence
import json
import logging

import six

from ..utils import python_2_unicode_compatible
from ..model import BaseModel, BaseType, FloatType, DictionaryType
from .units import UnitType

log = logging.getLogger(__name__)

class UnitType(BaseType):

    def process(self, value):
        if isinstance(value, BaseUnit):
            return BaseUnit
        return None

class BaseQuantityModel(BaseModel):

    value = FloatType()
    unit = UnitType()
    powers = DictionaryType(ModelType(BaseQuantityModel), FloatType())

    def __div__(self, other):
        # TODO
        pass

    def __pow__(self, other):
        # TODO
        pass

    def __mul__(self, other):
        # TODO
        pass

    def convert_to(self, unit):
        pass


class BaseUnit(ABC):

    def __init__(self, quantity, exponent=1, powers=None):
        self.quantity = quantity
        self.exponent = exponent
        self.powers = powers

    @abstractmethod
    def convert_to_standard(self):
        pass

    @abstractmethod
    def convert_from_standard(self):
        pass

    def __div__(self, other):
        # TODO
        pass

    def __pow__(self, other):
        # TODO
        pass

    def __mul__(self, other):
        # TODO
        pass
