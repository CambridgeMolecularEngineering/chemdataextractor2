# -*- coding: utf-8 -*-
"""
Test the Table Document element and complex Table autoparsers.

"""

from chemdataextractor.doc import Caption
from chemdataextractor.doc.table_new import Table
from chemdataextractor.model import TemperatureModel, StringType, Compound, ModelType, DimensionlessModel
from chemdataextractor.model.units.magnetic_field import MagneticFieldModel
from chemdataextractor.parse import W, R, Optional, I, ZeroOrMore
from chemdataextractor.parse.common import lbrct, rbrct
from chemdataextractor.parse.actions import join
from chemdataextractor.parse.auto import AutoTableParser

import logging
import unittest

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# 1.MODEL CLASSES USED FOR TESTING OF THE TABLE
class AbsentModel(TemperatureModel):
    specifier = StringType(parse_expression=W('Nothing'), required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=True, contextual=True, updatable=False)
    parser = [AutoTableParser()]


delim = R(r'^[:;\.,]$')
magnetic_field_specifier = (
    (R('μ0H(app)?') | (R('μ0') + W('H')) | (R('μ') + R('0') + W('H')) | R('μ0?[∆Δ]H(app)?') | (R('μ0') +
     R('[∆Δ]H(app)?')) | R('[∆Δ]H(app)?') | ((I('magnetic') | I('applied')) + I('field') + Optional(I('change'))))
    + ZeroOrMore(delim | lbrct).hide()
    + Optional(I('at') | I('with')).hide()
    + Optional(R('μ0H') | (R('μ0') + W('H')) | (R('μ') + R('0') + W('H')) | R('μ0[∆Δ]H(app)?') |
               (R('μ0') + R('[∆Δ]H(app)?')))
    + ZeroOrMore(delim | rbrct).hide()).add_action(join)


class MagneticField(MagneticFieldModel):
    compound = ModelType(Compound, required=False)
    specifier = StringType(parse_expression=magnetic_field_specifier, required=True, contextual=False, updatable=True)
    absent = ModelType(AbsentModel, required=True, contextual=True, updatable=False)
    parsers = [AutoTableParser()]


class Reference(DimensionlessModel):
    specifier = StringType(parse_expression=R('Ref'), required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=True, contextual=True, updatable=False)
    magnetic_field = ModelType(MagneticField, required=True, contextual=True, updatable=False)
    parsers = [AutoTableParser()]


# All unambiguous Curie phase transition specifiers
curie_transition_specifier = ((R(r'^\[?T(C|c)(urie)?[1-2]?\]?$') | R(r'^(C|c)urie$') |
                               R(r'^(F|f)erromagnet(ic|ism|ically)?$') | I('FM') | I('ferroelectric') |
                               W(r'(PM)-ferromagnetic'))
                              + Optional(lbrct + I('FM') + rbrct).hide()
                              + Optional(I('ordering') | I('ordered') | I('order-disorder') | I('behavior') | I('behaviour') | I('order'))
                              + Optional(I('phase'))
                              + Optional(R(r'^transition(s)?$'))
                              + Optional(R(r'^temperature[s]?$') | R(r'^temp[\.]?$') | I('point') | I('value'))
                              + ZeroOrMore(delim | lbrct).hide()
                              + Optional(I('at') | I('with')).hide()
                              + Optional(R(r'^\[?T(C|c)(urie)?[1-2]?\]?$') | I('TM'))
                              + ZeroOrMore(delim | rbrct).hide()).add_action(join)


class CurieTemperature(TemperatureModel):
    specifier = StringType(parse_expression=curie_transition_specifier, required=True, contextual=False, updatable=True)
    compound = ModelType(Compound, required=True, contextual=True, updatable=False)
    reference = ModelType(Reference, required=True, contextual=True, updatable=False)
    parsers = [AutoTableParser()]


# 2. TESTS
class TestNestedTable(unittest.TestCase):
    """
    Tests for automated parsing of tables with complex structure, which involves parsing of the table
    row header region, as well as a complex nested model hierarchy with different combinations of `required`
    submodels.
    """

    maxDiff = None

    def do_table(self, expected):
        table = Table(caption=Caption(""),
                      table_data="tests/data/tables/table_example_3.csv",
                      models=[CurieTemperature])
        result = []
        for record in table.records:
            result.append(record.serialize())
        self.assertCountEqual(expected, result)

    def test_required_submodels_1(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        MagneticField.absent.required = True
        Reference.magnetic_field.required = True
        CurieTemperature.reference.required = True
        expected = []
        self.do_table(expected)

    def test_required_submodels_2(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        MagneticField.absent.required = False
        Reference.magnetic_field.required = True
        CurieTemperature.reference.required = True
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Gd']}}}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Gd']}}}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': 'K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': 'K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': 'K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': 'K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1.5', 'raw_units': 'T)', 'value': [1.5], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': 'K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1.5', 'raw_units': 'T)', 'value': [1.5], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_3(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        MagneticField.absent.required = True
        Reference.magnetic_field.required = False
        CurieTemperature.reference.required = True
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': 'K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2']}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': 'K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': 'K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': 'K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': 'K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_4(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        MagneticField.absent.required = False
        Reference.magnetic_field.required = False
        CurieTemperature.reference.required = True
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Gd']}}}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Gd']}}}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': 'K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': 'K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': 'K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': 'K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1.5', 'raw_units': 'T)', 'value': [1.5], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': 'K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1.5', 'raw_units': 'T)', 'value': [1.5], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_5(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        MagneticField.absent.required = True
        Reference.magnetic_field.required = True
        CurieTemperature.reference.required = False
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': 'K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2']}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': 'K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': 'K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': 'K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': 'K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_6(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        MagneticField.absent.required = False
        Reference.magnetic_field.required = True
        CurieTemperature.reference.required = False
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Gd']}}}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Gd']}}}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': 'K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': 'K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': 'K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': 'K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1.5', 'raw_units': 'T)', 'value': [1.5], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': 'K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1.5', 'raw_units': 'T)', 'value': [1.5], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_7(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        MagneticField.absent.required = True
        Reference.magnetic_field.required = False
        CurieTemperature.reference.required = False
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': 'K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2']}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': 'K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': 'K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': 'K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': 'K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_8(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        MagneticField.absent.required = False
        Reference.magnetic_field.required = False
        CurieTemperature.reference.required = False
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Gd']}}}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': 'K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Gd']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Gd']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Gd']}}}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': 'K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': 'K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': 'K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': 'K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1.5', 'raw_units': 'T)', 'value': [1.5], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': 'K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1.5', 'raw_units': 'T)', 'value': [1.5], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': 'K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '5', 'raw_units': 'T)', 'value': [5.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': 'K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'magnetic_field': {'MagneticField': {'raw_value': '1', 'raw_units': 'T)', 'value': [1.0], 'units': 'Tesla^(1.0)', 'specifier': 'ΔH', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}}
        ]
        self.do_table(expected)


if __name__ == '__main__':
    unittest.main()
