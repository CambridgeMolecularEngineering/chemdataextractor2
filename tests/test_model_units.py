# -*- coding: utf-8 -*-
"""
tests.test_model_units.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test base types for making quantity models and units.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import six
import logging
import unittest
import copy

from chemdataextractor.model.units.quantity_model import QuantityModel, DimensionlessModel
from chemdataextractor.model.units.dimension import Dimensionless, Dimension
from chemdataextractor.model.units.unit import DimensionlessUnit, Unit

from chemdataextractor.model.units.time import Second, Minute, Hour, Time, TimeModel
from chemdataextractor.model.units.length import Meter, Mile, Length, LengthModel
from chemdataextractor.model.units.temperature import Temperature, TemperatureModel, Kelvin, Celsius, Fahrenheit
from chemdataextractor.model.units.mass import Mass, Gram

from chemdataextractor.parse.elements import R


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
places = 3


class Speed(Dimension):
    constituent_dimensions = Length() / Time()


class SpeedModel(QuantityModel):
    dimensions = Length() / Time()


class SpeedUnit(QuantityModel):
    def __init__(self, magnitude=0.0, powers=None):
        super(SpeedUnit, self).__init__(Speed(), magnitude, powers)


class WeirdUnit(SpeedUnit):
    pass

weird_entry = {R('weirdunit', group=0): WeirdUnit}
Speed.units_dict.update(weird_entry)


class TestUnitClass(unittest.TestCase):

    def test_division(self):
        speed = Meter(magnitude=1.0) / Second(magnitude=1.0)
        self.assertEqual(speed.dimensions, Length() / Time())
        self.assertEqual(speed.magnitude, 0.0)
        self.assertEqual(speed.powers, {Meter(): 1.0, Second(): -1.0})

    def test_pow(self):
        meters_cubed = Meter(magnitude=2.0) ** 3.0
        self.assertEqual(meters_cubed.dimensions, Length()**3.0)
        self.assertEqual(meters_cubed.magnitude, 6.0)
        self.assertEqual(meters_cubed.powers, {Meter(): 3.0})

    def test_mul(self):
        meterseconds = Meter(magnitude=1.0) * Second(magnitude=2.0)
        self.assertEqual(meterseconds.dimensions, Length() * Time())
        self.assertEqual(meterseconds.magnitude, 3.0)
        self.assertEqual(meterseconds.powers, {Meter(): 1.0, Second(): 1.0})

    def test_convert_value_to_standard_temp(self):
        temp = Celsius()
        val = temp.convert_value_from_standard(400)
        self.assertAlmostEqual(val, 126.85, places=places)

    def test_unit_convert_value_to_standard(self):
        speed = Mile() / Hour()
        standard_val = speed.convert_value_to_standard(60.0)
        self.assertLess(abs(26.8224 - standard_val), 10**(-3.5))

    def test_unit_convert_value_from_standard(self):
        speed = Mile() / Hour()
        val = speed.convert_value_from_standard(26.8224)
        self.assertAlmostEqual(val, 60.0, places=places)

    def test_unit_convert_error_to_standard(self):
        unusual_temp_unit = Celsius() / Fahrenheit()
        standard_val = unusual_temp_unit.convert_error_to_standard(5.0)
        self.assertAlmostEqual(standard_val, 9.0, places=places)

    # Need to have the updated error functions in length and time
    def test_unit_convert_error_to_standard_2(self):
        speed = Mile() / Hour()
        standard_err = speed.convert_error_to_standard(60.0)
        self.assertAlmostEqual(standard_err, 26.8224, places=places)

    # Need to have the updated error functions in length and time
    def test_unit_convert_error_from_standard(self):
        speed = Mile() / Hour()
        standard_err = speed.convert_error_from_standard(26.8224)
        self.assertAlmostEqual(standard_err, 60., places)

    def test_dimensionless(self):
        dimensionless_div = Meter() / Meter()
        dimensionless = DimensionlessUnit()
        self.assertEqual(dimensionless, dimensionless_div)

    def test_composite_unit(self):
        class Force(Dimension):
            constituent_dimensions = Mass() * Length() * Time() ** (-2.0)

        class Newton(Unit):
            constituent_units = Gram(magnitude=3.0) * Meter() * (Second()) ** (-2.0)

        newton = Newton()
        force = Force()
        self.assertEqual(newton.magnitude, 0.0)
        self.assertEqual(newton.dimensions, force)
        self.assertEqual(newton.powers, {Second(): -2.0, Meter(): 1.0, Gram(): 1.0})
        self.assertEqual(newton.base_magnitude, 3.0)

    def test_units_hashing(self):
        unit1 = Kelvin(magnitude=2.0) * Meter(magnitude=1.0) / Second(magnitude=1.0)
        unit2 = (Second(magnitude=1.0) ** (-1.0)) * Meter(magnitude=1.0) * Kelvin(magnitude=2.0)
        self.assertEqual(unit1.__hash__(), unit2.__hash__())


class TestDimensions(unittest.TestCase):

    def test_division(self):
        speed = Length() / Time()
        self.assertEqual(speed._dimensions, {Length(): 1.0, Time(): -1.0})

    def test_pow(self):
        meters_cubed = Length() ** 3.0
        self.assertEqual(meters_cubed._dimensions, {Length(): 3.0})

    def test_mul(self):
        meterseconds = Length() * Time()
        self.assertEqual(meterseconds._dimensions, {Length(): 1.0, Time(): 1.0})

    def test_dimensionless(self):
        dimensionless_div = Length() / Length()
        dimensionless = Dimensionless()
        self.assertEqual(dimensionless, dimensionless_div)

    def test_dimensions_hashing(self):
        dimension1 = Temperature() * Length() / Time()
        dimension2 = (Time() ** (-1)) * Length() * Temperature()
        self.assertEqual(dimension1.__hash__(), dimension2.__hash__())

    def test_units_dict_composite(self):
        expected_dict = copy.copy((Length() / Time()).units_dict)
        expected_dict.update(weird_entry)
        self.assertDictEqual(Speed.units_dict, expected_dict)

    def test_units_dict_divide_composite_1(self):
        class NewDimension(Dimension):
            constituent_dimensions = Speed() / Length()
        self.assertDictEqual(NewDimension.units_dict, Speed.units_dict)

    def test_units_dict_divide_composite_2(self):
        class NewDimension(Dimension):
            constituent_dimensions = Length() / Time()
        class NewDimension2(Dimension):
            constituent_dimensions = NewDimension() / Length()
        self.assertDictEqual(NewDimension2.units_dict, Time.units_dict)


class TestQuantity(unittest.TestCase):

    def test_equality(self):
        distance1 = LengthModel()
        distance1.value = [50.0, 60.0]
        distance1.units = Meter()
        distance2 = LengthModel()
        distance2.value = [48.0]
        distance2.units = Meter()
        distance2.error = 2.1
        self.assertTrue(distance1.is_equal(distance2))

    def test_division(self):
        distance = LengthModel()
        distance.value = [60.0]
        distance.units = Meter(magnitude=3.0)
        time = TimeModel()
        time.value = [60.0]
        time.units = Minute()
        speed = distance / time
        self.assertEqual(speed.value, [1.])
        self.assertEqual(speed.units, Meter(magnitude=3.0) / Minute())
        self.assertEqual(speed.dimensions, Length() / Time())

    def test_pow(self):
        length = LengthModel()
        length.value = [10.0]
        length.units = Meter(magnitude=-2.0)
        volume = length**3.0
        self.assertEqual(volume.units, Meter(-2.0)**3.0)
        self.assertEqual(volume.dimensions, Length()**3.0)
        self.assertEqual(volume.value, [1000.0])

    def test_mul(self):
        speed = SpeedModel()
        speed.value = [100.0]
        speed.units = Meter(magnitude=3.0) / Hour()
        time = TimeModel()
        time.value = [3.0]
        time.units = Hour()
        distance = speed * time
        self.assertEqual(distance.value, [300.0])
        self.assertEqual(distance.units, (Meter(magnitude=3.0))**1.0)
        self.assertEqual(distance.dimensions, Length())

    def test_mul_range_val(self):
        speed = SpeedModel()
        speed.value = [100.0, 200.0]
        speed.units = Meter(magnitude=3.0) / Hour()
        time = TimeModel()
        time.value = [3.0]
        time.units = Hour()
        distance = speed * time
        self.assertEqual(distance.value, [300.0, 600.0])
        self.assertEqual(distance.units, (Meter(magnitude=3.0))**1.0)
        self.assertEqual(distance.dimensions, Length())

    def test_mul_range_range(self):
        speed = SpeedModel()
        speed.value = [100.0, 200.0]
        speed.units = Meter(magnitude=3.0) / Hour()
        time = TimeModel()
        time.value = [3.0, 9.0]
        time.units = Hour()
        distance = speed * time
        self.assertEqual(distance.value, [300.0, 1800.0])
        self.assertEqual(distance.units, (Meter(magnitude=3.0))**1.0)
        self.assertEqual(distance.dimensions, Length())

    def test_convert(self):
        speed = SpeedModel()
        speed.value = [100.0]
        speed.units = Meter(magnitude=3.0) / Hour()
        print(speed.units)
        for unit, power in six.iteritems(speed.units.powers):
            print(unit, power)
        speed.convert_to(Mile() / Second())
        self.assertAlmostEqual(speed.value[0], 0.0172603109, places=places)

    def test_dimensionless(self):
        speed = SpeedModel()
        speed.value = [100.0]
        speed.units = Meter() / Second()
        speed2 = SpeedModel()
        speed2.value = [10.0]
        speed2.units = Meter() / Second()
        dimensionless_div = speed / speed2
        self.assertTrue(isinstance(dimensionless_div, DimensionlessModel))
