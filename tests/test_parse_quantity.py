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


from chemdataextractor.parse.quantity import QuantityParser
from chemdataextractor.units.temperatures import Temperature, Celsius, Kelvin
from chemdataextractor.units.lengths import Length, Meter, Mile
from chemdataextractor.units.times import Time, Second, Hour


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestUnitClass(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.qp = QuantityParser()

    def test_to_range(self):
        test_string = '1500.3 to 1600.2'
        extracted = self.qp.extract_value(test_string)
        self.assertLess(abs(extracted[0] - 1500.3), 10**(-6.0))
        self.assertLess(abs(extracted[1] - 1600.2), 10**(-6.0))

    def test_err_range(self):
        test_string = '1600.4±2.4'
        extracted = self.qp.extract_value(test_string)
        self.assertLess(abs(extracted[0] - 1598.0), 10**(-6.0))
        self.assertLess(abs(extracted[1] - 1602.8), 10**(-6.0))

    def test_single_value(self):
        test_string = '500.8'
        extracted = self.qp.extract_value(test_string)
        self.assertEqual(extracted, 500.8)

    def test_unit_mm(self):
        self.qp.dimensions = Length()**2 / Time()
        test_string = 'mm2/s'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = (Meter(exponent=-3.0) ** 2.) / Second()
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_unit_multiplication(self):
        self.qp.dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
        test_string = '(km/s)1/2Kh2'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = ((Meter(exponent=3.0) / Second()) ** 0.5) * (Kelvin() * Hour()**2)
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_unit_division(self):
        self.qp.dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
        test_string = 'Kh2/(km/s)-1/2'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = ((Meter(exponent=3.0) / Second()) ** 0.5) * (Kelvin() * Hour()**2)
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)
