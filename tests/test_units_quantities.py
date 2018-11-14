# -*- coding: utf-8 -*-
"""
tests.test_units_quantities.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test base types for making quantity models and units.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest


from chemdataextractor.units.quantities import Dimensionless, DimensionlessUnit, DimensionlessModel, QuantityModel
from chemdataextractor.units.times import Second, Minute, Hour, Time, TimeModel
from chemdataextractor.units.lengths import Meter, Mile, Length, LengthModel


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class SpeedModel(QuantityModel):
    dimensions = Length() / Time()


class TestUnitClass(unittest.TestCase):

    def test_division(self):
        speed = Meter(exponent=1.0) / Second(exponent=1.0)
        self.assertEqual(speed.dimensions, Length() / Time())
        self.assertEqual(speed.exponent, 0.0)
        self.assertEqual(speed.powers, {Meter(): 1.0, Second(): -1.0})

    def test_pow(self):
        meters_cubed = Meter(exponent=2.0) ** 3.0
        self.assertEqual(meters_cubed.dimensions, Length()**3.0)
        self.assertEqual(meters_cubed.exponent, 6.0)
        self.assertEqual(meters_cubed.powers, {Meter(): 3.0})

    def test_mul(self):
        meterseconds = Meter(exponent=1.0) * Second(exponent=2.0)
        self.assertEqual(meterseconds.dimensions, Length() * Time())
        self.assertEqual(meterseconds.exponent, 3.0)
        self.assertEqual(meterseconds.powers, {Meter(): 1.0, Second(): 1.0})

    def test_convert_to_standard(self):
        speed = Mile() / Hour()
        standard_val = speed.convert_to_standard(60.0)
        self.assertLess(abs(26.8224 - standard_val), 10**(-3.5))

    def test_convert_from_standard(self):
        speed = Mile() / Hour()
        val = speed.convert_from_standard(26.8224)
        self.assertLess(abs(60.0 - val), 10**(-3.5))

    def test_dimensionless(self):
        dimensionless_div = Meter() / Meter()
        dimensionless = DimensionlessUnit()
        self.assertEqual(dimensionless, dimensionless_div)


class TestDimensions(unittest.TestCase):

    def test_division(self):
        speed = Length() / Time()
        self.assertEqual(speed.dimensions, {Length(): 1.0, Time(): -1.0})

    def test_pow(self):
        meters_cubed = Length() ** 3.0
        self.assertEqual(meters_cubed.dimensions, {Length(): 3.0})

    def test_mul(self):
        meterseconds = Length() * Time()
        self.assertEqual(meterseconds.dimensions, {Length(): 1.0, Time(): 1.0})

    def test_dimensionless(self):
        dimensionless_div = Length() / Length()
        dimensionless = Dimensionless()
        self.assertEqual(dimensionless, dimensionless_div)


class TestQuantity(unittest.TestCase):

    def test_division(self):
        distance = LengthModel()
        distance.value = 60.0
        distance.units = Meter(exponent=3.0)
        time = TimeModel()
        time.value = 60.0
        time.units = Minute()
        speed = distance / time
        self.assertEqual(speed.value, 1.)
        self.assertEqual(speed.units, Meter(exponent=3.0) / Minute())
        self.assertEqual(speed.dimensions, Length() / Time())

    def test_pow(self):
        length = LengthModel()
        length.value = 10.0
        length.units = Meter(exponent=-2.0)
        volume = length**3.0
        self.assertEqual(volume.units, Meter(-2.0)**3.0)
        self.assertEqual(volume.dimensions, Length()**3.0)
        self.assertEqual(volume.value, 1000.0)

    def test_mul(self):
        speed = SpeedModel()
        speed.value = 100.0
        speed.units = Meter(exponent=3.0) / Hour()
        time = TimeModel()
        time.value = 3.0
        time.units = Hour()
        distance = speed * time
        self.assertEqual(distance.value, 300.0)
        self.assertEqual(distance.units, (Meter(exponent=3.0))**1.0)
        self.assertEqual(distance.dimensions, Length())

    def test_mul_range_val(self):
        speed = SpeedModel()
        speed.value = [100.0, 200.0]
        speed.units = Meter(exponent=3.0) / Hour()
        time = TimeModel()
        time.value = 3.0
        time.units = Hour()
        distance = speed * time
        self.assertEqual(distance.value, [300.0, 600.0])
        self.assertEqual(distance.units, (Meter(exponent=3.0))**1.0)
        self.assertEqual(distance.dimensions, Length())

    def test_mul_range_range(self):
        speed = SpeedModel()
        speed.value = [100.0, 200.0]
        speed.units = Meter(exponent=3.0) / Hour()
        time = TimeModel()
        time.value = [3.0, 9.0]
        time.units = Hour()
        distance = speed * time
        self.assertEqual(distance.value, [300.0, 1800.0])
        self.assertEqual(distance.units, (Meter(exponent=3.0))**1.0)
        self.assertEqual(distance.dimensions, Length())

    def test_convert(self):
        speed = SpeedModel()
        speed.value = 100.0
        speed.units = Meter(exponent=3.0) / Hour()
        converted = speed.convert_to(Mile() / Second())
        self.assertLess(abs(converted - 0.0172603109), 10**(-5))

    def test_dimensionless(self):
        speed = SpeedModel()
        speed.value = 100.0
        speed.units = Meter() / Second()
        speed2 = SpeedModel()
        speed2.value = 10.0
        speed2.units = Meter() / Second()
        dimensionless_div = speed / speed2
        self.assertTrue(isinstance(dimensionless_div, DimensionlessModel))
