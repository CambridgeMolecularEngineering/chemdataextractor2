# -*- coding: utf-8 -*-
"""
tests.test_parse_auto.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test autoparser functionality

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import unittest


from chemdataextractor.model.units.quantity_model import QuantityModel, DimensionlessModel
from chemdataextractor.model.units.dimension import Dimensionless, Dimension
from chemdataextractor.model.units.unit import DimensionlessUnit, Unit


from chemdataextractor.model.units.time import Second, Minute, Hour, Time, TimeModel
from chemdataextractor.model.units.length import Meter, Mile, Length, LengthModel
from chemdataextractor.model.units.temperature import Temperature, TemperatureModel, Kelvin, Celsius, Fahrenheit
from chemdataextractor.model.units.mass import Mass, Gram
from chemdataextractor.model.units.energy import Energy
from chemdataextractor.parse.auto import construct_unit_element, match_dimensions_of
from chemdataextractor.parse.auto_dependency import AutoDependencyParser
from chemdataextractor.parse.quantity import value_element
from chemdataextractor.doc.text import Sentence
from chemdataextractor.parse.elements import I
from chemdataextractor.model import Compound, ModelType, StringType
from lxml import etree

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class Speed(Dimension):
    constituent_dimensions = Length() / Time()


class SpeedModel(QuantityModel):
    dimensions = Length() / Time()
    specifier = StringType(parse_expression=I('speed'))
    compound = ModelType(Compound)
    parsers = [AutoDependencyParser()]


class SpecificHeat(Dimension):
    constituent_dimensions = Energy() / (Mass() * Temperature())


class SpecificHeatModel(QuantityModel):
    dimensions = SpecificHeat()


class AreaPerTime(Dimension):
    constituent_dimensions = Length() ** 2 / Time()


class AreaPerTimeModel(QuantityModel):
    dimensions = AreaPerTime()


class TestAutoDependencySentenceParser(unittest.TestCase):

    def test_autoparser(self):
        test_sentence = Sentence('The speed of H2O (10 km/h) was higher than that of CH3 (25 km/h).')
        test_sentence.models = [SpeedModel]
        found_records = test_sentence.records.serialize()
        expected = [{'Compound': {'names': ['CH3']}},
                    {'Compound': {'names': ['H2O']}},
                    {'SpeedModel': {'raw_value': '25', 'raw_units': 'km/h', 'value': [25.0],
                                    'units': '(10^3.0) * Hour^(-1.0)  Meter^(1.0)', 'specifier': 'speed',
                                    'compound': {'Compound': {'names': ['CH3']}}}},
                    {'SpeedModel': {'raw_value': '10', 'raw_units': 'km/h', 'value': [10.0],
                                    'units': '(10^3.0) * Hour^(-1.0)  Meter^(1.0)', 'specifier': 'speed',
                                    'compound': {'Compound': {'names': ['H2O']}}}}]
        print(found_records)
        self.assertCountEqual(found_records, expected)
