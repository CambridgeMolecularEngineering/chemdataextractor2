# -*- coding: utf-8 -*-
"""
tests.test_units_quantities.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test QuantityParser's funcitonality to parse units/values.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest
import numpy as np


from chemdataextractor.parse.base import BaseParser
from chemdataextractor.model.units import QuantityModel
from chemdataextractor.model.units.temperature import Temperature, Celsius, Kelvin
from chemdataextractor.model.units.length import Length, Meter, Mile
from chemdataextractor.model.units.time import Time, Second, Hour


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestUnitClass(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.qp = BaseParser()
        self.qp.model = QuantityModel()

    def test_to_range(self):
        test_string = '1500.3 to 1600.2'
        extracted = self.qp.extract_value(test_string)
        self.assertAlmostEqual(extracted[0], 1500.3)
        self.assertAlmostEqual(extracted[1], 1600.2)

    def test_err_range(self):
        test_string = '1600.4± 2.4'
        extracted_value = self.qp.extract_value(test_string)
        extracted_error = self.qp.extract_error(test_string)
        expected_value, expected_error = 1600.4, 2.4
        self.assertAlmostEqual(extracted_value[0], expected_value)
        self.assertAlmostEqual(extracted_error, expected_error)

    def test_single_value(self):
        test_string = '500.8'
        extracted = self.qp.extract_value(test_string)
        self.assertEqual(extracted[0], 500.8)

    def test_unit_mm(self):
        self.qp.model.dimensions = Length()**2 / Time()
        test_string = 'mm2/s'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = (Meter(magnitude=-3.0) ** 2.) / Second()
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_unit_multiplication(self):
        self.qp.model.dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
        test_string = '(km/s)1/2Kh2'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = ((Meter(magnitude=3.0) / Second()) ** 0.5) * (Kelvin() * Hour()**2)
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_unit_division(self):
        self.qp.model.dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
        test_string = 'Kh2/(km/s)-1/2'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = ((Meter(magnitude=3.0) / Second()) ** 0.5) * (Kelvin() * Hour()**2)
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)
