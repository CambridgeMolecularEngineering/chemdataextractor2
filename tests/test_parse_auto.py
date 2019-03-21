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
import six
import logging
import unittest


from chemdataextractor.model.units.quantity_model import QuantityModel, DimensionlessModel
from chemdataextractor.model.units.dimension import Dimensionless, Dimension
from chemdataextractor.model.units.unit import DimensionlessUnit, Unit


from chemdataextractor.model.units.time import Second, Minute, Hour, Time, TimeModel
from chemdataextractor.model.units.length import Meter, Mile, Length, LengthModel
from chemdataextractor.model.units.temperature import Temperature, TemperatureModel, Kelvin, Celsius, Fahrenheit
from chemdataextractor.model.units.mass import Mass, Gram
from chemdataextractor.parse.auto import construct_unit_element, match_dimensions_of, AutoSentenceParser
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


class AreaPerTime(Dimension):
    constituent_dimensions = Length() ** 2 / Time()


class AreaPerTimeModel(QuantityModel):
    dimensions = AreaPerTime()


class TestAutoRules(unittest.TestCase):

    def test_unit_element(self):
        test_sentence = Sentence('The speed was 31 m/s and')
        units_expression = construct_unit_element(Speed()).with_condition(match_dimensions_of(SpeedModel))('raw_units')
        results = units_expression.scan(test_sentence.tagged_tokens)
        results_list = []
        for result in results:
            results_list.append(etree.tostring(result[0]))
        expected = [b'<raw_units>m/s</raw_units>']
        self.assertEqual(expected, results_list)

    def test_unit_element_nospace(self):
        test_sentence = Sentence('Area was increasing at 31 m2/s and')
        units_expression = construct_unit_element(AreaPerTime()).with_condition(match_dimensions_of(AreaPerTimeModel))('raw_units')
        results = units_expression.scan(test_sentence.tagged_tokens)
        results_list = []
        for result in results:
            results_list.append(etree.tostring(result[0]))
        expected = [b'<raw_units>m2/s</raw_units>']
        self.assertEqual(expected, results_list)

class TestAutoSentenceParser(unittest.TestCase):

    def test_autoparser(self):
        test_sentence = Sentence('CH3 was found to have a speed of approximately 25 km/h at a temperature of 283 K')
        test_sentence.models = [SpeedModel]
        found_records = test_sentence.records.serialize()
        expected = [{'Compound': {'names': ['CH3']}},
                    {'SpeedModel': {'raw_value': '25', 'raw_units': 'km/h', 'value': [25.0],
                                    'units': '(10^3.0) * Hour^(-1.0)  Meter^(1.0)', 'specifier': 'speed',
                                    'compound': {'Compound': {'names': ['CH3']}}}}]
        self.assertEqual(found_records, expected)
