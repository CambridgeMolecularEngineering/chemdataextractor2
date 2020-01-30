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


from chemdataextractor.parse.base import BaseParser
from chemdataextractor.model.units import QuantityModel
from chemdataextractor.model.units.temperature import Temperature, Celsius, Kelvin
from chemdataextractor.model.units.length import Length, Meter, Mile
from chemdataextractor.model.units.time import Time, Second, Hour
from chemdataextractor.model.units.energy import Joule, Energy
from chemdataextractor.model.units.mass import Mass, Gram
from chemdataextractor.model.units.current import ElectricalCurrent, Ampere


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
        test_string = '1600.4±2.4'
        extracted_value = self.qp.extract_value(test_string)
        extracted_error = self.qp.extract_error(test_string)
        expected_value, expected_error = 1600.4, 2.4
        self.assertAlmostEqual(extracted_value[0], expected_value)
        self.assertAlmostEqual(extracted_error, expected_error)

    def test_err_brackets_1(self):
        test_string = '1600.4(2)'
        extracted_value = self.qp.extract_value(test_string)
        extracted_error = self.qp.extract_error(test_string)
        expected_value, expected_error = 1600.4, 0.2
        self.assertAlmostEqual(extracted_value[0], expected_value)
        self.assertAlmostEqual(extracted_error, expected_error)

    def test_err_brackets_2(self):
        test_string = '1600(2)'
        extracted_value = self.qp.extract_value(test_string)
        extracted_error = self.qp.extract_error(test_string)
        expected_value, expected_error = 1600., 2.
        self.assertAlmostEqual(extracted_value[0], expected_value)
        self.assertAlmostEqual(extracted_error, expected_error)

    def test_err_brackets_3(self):
        test_string = '0.0002(2)'
        extracted_value = self.qp.extract_value(test_string)
        extracted_error = self.qp.extract_error(test_string)
        expected_value, expected_error = 0.0002, 0.0002
        self.assertAlmostEqual(extracted_value[0], expected_value)
        self.assertAlmostEqual(extracted_error, expected_error)

    def test_single_value(self):
        test_string = '500.8'
        extracted = self.qp.extract_value(test_string)
        self.assertEqual(extracted[0], 500.8)

    def test_comma_value(self):
        test_string = '600,000.8'
        extracted = self.qp.extract_value(test_string)
        self.assertEqual(extracted[0], 600000.8)

    def test_european_value(self):
        test_string = '500,8'
        extracted = self.qp.extract_value(test_string)
        self.assertEqual(extracted[0], 500.8)

    def test_fraction_value(self):
        test_string = '3/4'
        extracted = self.qp.extract_value(test_string)
        print(extracted)
        self.assertEqual(extracted[0], 0.75)

    def test_fraction_zero(self):
        test_string = '3/0'
        extracted = self.qp.extract_value(test_string)
        self.assertEqual(extracted, [])

    def test_unit_mm(self):
        self.qp.model.dimensions = Length()**2 / Time()
        test_string = 'mm2/s'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = (Meter(magnitude=-3.0) ** 2.) / Second()
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_unit_miles(self):
        self.qp.model.dimensions = Length()
        test_string = 'miles'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = Mile()
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

        self.qp.model.dimensions = Length()
        test_string = 'meters'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = Meter()
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

    def test_unit_with_duplicate_definition_of_magnitude_and_unit(self):
        self.qp.model.dimensions = ElectricalCurrent() / Length()**2
        test_string = 'mAcm-2'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = (Ampere(magnitude=1.0) * Meter()**(-2.0))
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_complicated_division_1(self):
        self.qp.model.dimensions = Temperature() * Length()**(-2.) * Time() ** (-1.)
        test_string = 'K/km2s'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = (Kelvin() / ((Meter(magnitude=3.0) ** 2.) * Second()))
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_complicated_division_2(self):
        self.qp.model.dimensions = Temperature() * Length()**(-2.) * Time() ** (-1.)
        test_string = 'K/km2/s'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = (Kelvin() / ((Meter(magnitude=3.0) ** 2.) * Second()))
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_complicated_division_3(self):
        self.qp.model.dimensions = Temperature() * Length()**(-6.) * Time() ** (1.)
        test_string = 'K/(km2)3s'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = (Kelvin() / ((Meter(magnitude=3.0) ** 6.)) * Second())
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)

    def test_complicated_division_4(self):
        self.qp.model.dimensions = Energy() / Mass()
        test_string = 'Jkg−1'
        extracted = self.qp.extract_units(test_string, strict=True)
        expected = Joule() / Gram(magnitude=3.0)
        log.debug(extracted, expected)
        self.assertEqual(extracted, expected)
