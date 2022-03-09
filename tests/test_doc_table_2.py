# -*- coding: utf-8 -*-
"""
Test the Table Document element and complex Table autoparsers.

"""

from chemdataextractor.doc import Caption, Document
from chemdataextractor.doc.table import Table
from chemdataextractor.model import TemperatureModel, StringType, Compound, ModelType, DimensionlessModel
from chemdataextractor.parse.cem import CompoundParser, CompoundHeadingParser, ChemicalLabelParser, CompoundTableParser
from chemdataextractor.model.units.energy import EnergyModel
from chemdataextractor.parse import W, R
from chemdataextractor.parse.auto import AutoTableParser

import logging
import unittest

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# 1.MODEL CLASSES USED FOR TESTING OF THE TABLE
class AbsentModel(TemperatureModel):
    specifier = StringType(parse_expression=W('Nothing'), required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=True, contextual=True, updatable=False, binding=True)
    parser = [AutoTableParser()]


class Enthalpy(EnergyModel):
    compound = ModelType(Compound, required=False, binding=True)
    specifier = StringType(parse_expression=R('^Enthalpy$'), required=True, contextual=False, updatable=True)
    absent = ModelType(AbsentModel, required=True, contextual=True, updatable=False)
    parsers = [AutoTableParser()]


class Reference(DimensionlessModel):
    specifier = StringType(parse_expression=R('Ref'), required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=True, contextual=True, updatable=False, binding=True)
    enthalpy = ModelType(Enthalpy, required=True, contextual=True, updatable=False)
    parsers = [AutoTableParser()]


class CurieTemperature(TemperatureModel):
    specifier = StringType(parse_expression=R(r'^\[?T(C|c)(urie)?[1-2]?\]?$'), required=True, contextual=False, updatable=True)
    compound = ModelType(Compound, required=True, contextual=True, updatable=False, binding=True)
    reference = ModelType(Reference, required=True, contextual=True, updatable=False)
    parsers = [AutoTableParser()]


def _get_serialised_records(records, models=None):
    serialized_list = []
    for record in records:
        if models is None or type(record) in models:
            serialized_list.append(record.serialize())
    return serialized_list


# 2. TESTS
class TestNestedTable(unittest.TestCase):
    """
    Tests for automated parsing of tables with complex structure, which involves parsing of the table
    row header region, as well as a complex nested model hierarchy with different combinations of `required`
    submodels.
    """

    maxDiff = None

    def do_table(self, expected):
        Compound.parsers = [CompoundParser(), CompoundHeadingParser(), ChemicalLabelParser()]
        table = Table(caption=Caption(""),
                      table_data="tests/data/tables/table_example_3.csv",
                      models=[CurieTemperature])
        result = _get_serialised_records(table.records, models=[CurieTemperature])
        self.assertCountEqual(expected, result)
        Compound.parsers = [CompoundParser(), CompoundHeadingParser(), ChemicalLabelParser(), CompoundTableParser()]
        Enthalpy.absent.required = True
        Enthalpy.absent.contextual = True
        Reference.enthalpy.required = True
        Reference.enthalpy.contextual = True
        CurieTemperature.reference.required = True
        CurieTemperature.reference.contextual = True

    def test_required_submodels_1(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        Enthalpy.absent.required = True
        Enthalpy.absent.contextual = False
        Reference.enthalpy.required = True
        Reference.enthalpy.contextual = False
        CurieTemperature.reference.required = True
        CurieTemperature.reference.contextual = False
        expected = []
        self.do_table(expected)

    def test_required_submodels_2(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        Enthalpy.absent.required = False
        Reference.enthalpy.required = True
        CurieTemperature.reference.required = True
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['MnO2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['MnO2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': '(K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': '(K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': '(K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': '(K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1.5', 'raw_units': '(kJ)', 'value': [1.5], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': '(K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1.5', 'raw_units': '(kJ)', 'value': [1.5], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_3(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        Enthalpy.absent.required = True
        Enthalpy.absent.contextual = False
        Reference.enthalpy.required = False
        CurieTemperature.reference.required = True
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': '(K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': '(K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': '(K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': '(K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': '(K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_4(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        Enthalpy.absent.required = False
        Reference.enthalpy.required = False
        CurieTemperature.reference.required = True
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['MnO2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['MnO2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': '(K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': '(K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': '(K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': '(K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1.5', 'raw_units': '(kJ)', 'value': [1.5], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': '(K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1.5', 'raw_units': '(kJ)', 'value': [1.5], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_5(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        Enthalpy.absent.required = True
        Enthalpy.absent.contextual = False
        Reference.enthalpy.required = True
        Reference.enthalpy.contextual = False
        CurieTemperature.reference.required = False
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': '(K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': '(K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': '(K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': '(K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': '(K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_6(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        Enthalpy.absent.required = False
        Reference.enthalpy.required = True
        CurieTemperature.reference.required = False
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['MnO2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['MnO2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': '(K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': '(K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': '(K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': '(K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1.5', 'raw_units': '(kJ)', 'value': [1.5], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': '(K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1.5', 'raw_units': '(kJ)', 'value': [1.5], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_7(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        Enthalpy.absent.required = True
        Enthalpy.absent.contextual = False
        Reference.enthalpy.required = False
        CurieTemperature.reference.required = False
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': '(K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': '(K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': '(K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': '(K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': '(K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}
        ]
        self.do_table(expected)

    def test_required_submodels_8(self):
        """
        Tests a combination of `required` parameters for submodels.
        """
        Enthalpy.absent.required = False
        Reference.enthalpy.required = False
        CurieTemperature.reference.required = False
        expected = [
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '52–55', 'value': [52.0, 55.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['MnO2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '293', 'raw_units': '(K)', 'value': [293.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['MnO2']}}, 'reference': {'Reference': {'raw_value': '56', 'value': [56.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['MnO2']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['MnO2']}}}}}}}},
            {'CurieTemperature': {'raw_value': '337', 'raw_units': '(K)', 'value': [337.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'reference': {'Reference': {'raw_value': '57', 'value': [57.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La2/3Ba1/3MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '292', 'raw_units': '(K)', 'value': [292.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Ba0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '252', 'raw_units': '(K)', 'value': [252.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'reference': {'Reference': {'raw_value': '26', 'value': [26.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Ca0.33']}}}}}}}},
            {'CurieTemperature': {'raw_value': '312', 'raw_units': '(K)', 'value': [312.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1.5', 'raw_units': '(kJ)', 'value': [1.5], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '321', 'raw_units': '(K)', 'value': [321.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'reference': {'Reference': {'raw_value': '58', 'value': [58.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1.5', 'raw_units': '(kJ)', 'value': [1.5], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['La0.67Sr0.33MnO3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '309', 'raw_units': '(K)', 'value': [309.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '39', 'value': [39.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '5', 'raw_units': '(kJ)', 'value': [5.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}},
            {'CurieTemperature': {'raw_value': '286', 'raw_units': '(K)', 'value': [286.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TC', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'reference': {'Reference': {'raw_value': '286', 'value': [286.0], 'specifier': 'Ref', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}, 'enthalpy': {'Enthalpy': {'raw_value': '1', 'raw_units': '(kJ)', 'value': [1.0], 'units': '(10^3.0) * Joule^(1.0)', 'specifier': 'Enthalpy', 'compound': {'Compound': {'names': ['Ba0.33Mn0.98Ti0.02O3']}}}}}}}}
        ]
        self.do_table(expected)


if __name__ == '__main__':
    unittest.main()
