# -*- coding: utf-8 -*-
"""
Test the Table Document element and Table autoparsers.

"""

from chemdataextractor.model.units.quantity_model import DimensionlessModel
from chemdataextractor.parse.elements import R, I
from chemdataextractor.model.base import StringType, ModelType
from chemdataextractor.model.model import Compound
from chemdataextractor.doc.table_new import Table
from chemdataextractor.doc import Caption
from chemdataextractor.doc import Document
from chemdataextractor.reader.elsevier import ElsevierXmlReader
from chemdataextractor.reader.springer import SpringerHtmlReader
from chemdataextractor.model.units.length import LengthModel
from chemdataextractor.model.units.temperature import TemperatureModel
from chemdataextractor.parse.actions import merge

import logging
import unittest

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# Model classes used for testing
class CoordinationNumber(DimensionlessModel):
    coordination_number_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    specifier_expression = R('^(N|n|k)$')
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=True)
    cn_label = StringType(parse_expression=coordination_number_label)
    compound = ModelType(Compound)


class InteratomicDistance(LengthModel):
    specifier_expression = (R('^bond$') + R('^distance')).add_action(merge)
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=True)
    rij_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    species = StringType(parse_expression=rij_label, required=True, contextual=False)
    compound = ModelType(Compound, required=True, contextual=True)


class NeelTemperature(TemperatureModel):
    specifier_expression = (I('Néel') + I('temperature'))
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=False, mutable=True)
    compound = ModelType(Compound, required=False, contextual=True)


class CurieTemperature(TemperatureModel):
    specifier_expression = (I('Curie') + I('temperature'))
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=False, mutable=True)
    compound = ModelType(Compound, required=False, contextual=True)


class TestTable(unittest.TestCase):
    """Tests for automated parsing of tables"""

    maxDiff = None

    def do_table_1(self, expected):
        table = Table(caption=Caption("This is my table."),
                      table_data="tests/data/tables/table_example_1.csv",
                      models=[CoordinationNumber])
        result = []
        for record in table.records:
            result.append(record.serialize())
        self.assertCountEqual(expected, result)

    def test_contextual_required_combinations(self):
        """
        Tests various combinations of merging in-table records based on the 'required' and 'contextual' flags
        in the model fields.
        """

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = True
        # no result, because we don't have the specifier
        expected = []
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = False
        # no result, because we don't have the specifier
        expected = []
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = False
        # no result, because we don't have the specifier
        expected = []
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = True
        # no result, because we don't have the specifier
        expected = []
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = True
        # everything but 'cn_label' is contextual:
        expected = [{'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676], 'specifier': 'k'}},
                    {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676], 'specifier': 'k'}},
                    {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676], 'specifier': 'k'}},
                    {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676], 'specifier': 'k'}},
                    {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676], 'specifier': 'k'}},
                    {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676], 'specifier': 'k'}},
                    {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO3']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO4']}}}},
                    {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO5']}}}},
                    {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO6']}}}},
                    {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO7']}}}},
                    {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'specifier': 'k', 'cn_label': 'Ti-O', 'compound': {'Compound': {'names': ['TiO8']}}}},
                    {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'specifier': 'k', 'cn_label': 'O-O', 'compound': {'Compound': {'names': ['TiO9']}}}},
                    {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'specifier': 'k', 'cn_label': 'Ti-Ti', 'compound': {'Compound': {'names': ['TiO10']}}}}]
        self.do_table_1(expected)

    def test_caption_compound(self):
        """
        Tests the addition of the caption compound to table records without a compound
        """
        f = open('tests/data/tables/j.commatsci.2018.02.056.xml', 'rb')
        doc = Document.from_file(f, readers=[ElsevierXmlReader()])
        f.close()
        table = doc.tables[0]
        table.models = [InteratomicDistance]
        result = []
        for record in table.records:
            result.append(record.serialize())
        expected = [{'InteratomicDistance': {'raw_value': '3.1814', 'raw_units': 'Å', 'value': [3.1814], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Mg-Mg', 'compound': {'Compound': {'names': ['Mg2Si']}}}},
                    {'InteratomicDistance': {'raw_value': '2.7552', 'raw_units': 'Å', 'value': [2.7552], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Mg-Si', 'compound': {'Compound': {'names': ['Mg2Si']}}}},
                    {'InteratomicDistance': {'raw_value': '4.4992', 'raw_units': 'Å', 'value': [4.4992], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Si-Si', 'compound': {'Compound': {'names': ['Mg2Si']}}}},
                    {'Compound': {'names': ['Mg2Si']}}]
        self.assertCountEqual(expected, result)

    def test_unidentified_records_1(self):
        """
        Tests the retrieval of 'unidentified' records (records that need to have a compound but the compound is the
        only missing field.
        """
        f = open('tests/data/tables/j.commatsci.2018.02.056_2.xml', 'rb')
        doc = Document.from_file(f, readers=[ElsevierXmlReader()])
        f.close()
        table = doc.tables[0]
        table.models = [InteratomicDistance]
        result = []
        for record in table.records:
            if not record.is_unidentified:
                result.append(record.serialize())
            elif record.is_unidentified:
                result.append(["unidentified", record.serialize()])

        expected = [['unidentified', {'InteratomicDistance': {'raw_value': '3.1814', 'raw_units': 'Å', 'value': [3.1814], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Mg-Mg'}}],
                    ['unidentified', {'InteratomicDistance': {'raw_value': '2.7552', 'raw_units': 'Å', 'value': [2.7552], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Mg-Si'}}],
                    ['unidentified', {'InteratomicDistance': {'raw_value': '4.4992', 'raw_units': 'Å', 'value': [4.4992], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Si-Si'}}]]
        self.assertCountEqual(expected, result)

    def test_unidentified_records_2(self):
        """
        Tests the retrieval of 'unidentified' records (records that need to have a compound but the compound is the
        only missing field. This should return no unidentified records
        """
        f = open('tests/data/tables/j.commatsci.2018.02.056.xml', 'rb')
        doc = Document.from_file(f, readers=[ElsevierXmlReader()])
        f.close()
        table = doc.tables[0]
        table.models = [InteratomicDistance]
        result = []
        for record in table.records:
            if not record.is_unidentified:
                result.append(record.serialize())
            elif record.is_unidentified:
                result.append(["unidentified", record.serialize()])

        expected = [{'InteratomicDistance': {'raw_value': '3.1814', 'raw_units': 'Å', 'value': [3.1814], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Mg-Mg', 'compound': {'Compound': {'names': ['Mg2Si']}}}},
                    {'InteratomicDistance': {'raw_value': '2.7552', 'raw_units': 'Å', 'value': [2.7552], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Mg-Si', 'compound': {'Compound': {'names': ['Mg2Si']}}}},
                    {'InteratomicDistance': {'raw_value': '4.4992', 'raw_units': 'Å', 'value': [4.4992], 'units': 'Angstrom^(1.0)', 'specifier': 'bonddistances', 'species': 'Si-Si', 'compound': {'Compound': {'names': ['Mg2Si']}}}},
                    {'Compound': {'names': ['Mg2Si']}}]
        self.assertCountEqual(expected, result)

    def test_model_updating_from_caption_1(self):
        f = open('tests/data/tables/table_test.html', 'rb')
        d = Document.from_file(f, readers=[SpringerHtmlReader()])
        d.models = [CurieTemperature, NeelTemperature]
        results = d.records.serialize()
        expected = [
            {'CurieTemperature': {'raw_value': '122.0', 'raw_units': 'K', 'value': [122.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TD', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'CurieTemperature': {'raw_value': '143.5', 'raw_units': 'K', 'value': [143.5], 'units': 'Kelvin^(1.0)', 'specifier': 'TD', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'CurieTemperature': {'raw_value': '0.4', 'raw_units': 'K', 'value': [0.4], 'units': 'Kelvin^(1.0)', 'specifier': 'TD', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'CurieTemperature': {'raw_value': '0.6', 'raw_units': 'K', 'value': [0.6], 'units': 'Kelvin^(1.0)', 'specifier': 'TD', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'CurieTemperature': {'raw_value': '0.8', 'raw_units': 'K', 'value': [0.8], 'units': 'Kelvin^(1.0)', 'specifier': 'TD', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'CurieTemperature': {'raw_value': '116.5', 'raw_units': 'K', 'value': [116.5], 'units': 'Kelvin^(1.0)', 'specifier': 'TD', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'NeelTemperature': {'raw_value': '0.0', 'raw_units': 'K', 'value': [0.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TN', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'NeelTemperature': {'raw_value': '0.2', 'raw_units': 'K', 'value': [0.2], 'units': 'Kelvin^(1.0)', 'specifier': 'TN', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'NeelTemperature': {'raw_value': '167.6', 'raw_units': 'K', 'value': [167.6], 'units': 'Kelvin^(1.0)', 'specifier': 'TN', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'NeelTemperature': {'raw_value': '278.0', 'raw_units': 'K', 'value': [278.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TN', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'NeelTemperature': {'raw_value': '181.9', 'raw_units': 'K', 'value': [181.9], 'units': 'Kelvin^(1.0)', 'specifier': 'TN', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            {'NeelTemperature': {'raw_value': '1.0', 'raw_units': 'K', 'value': [1.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TN', 'compound': {'Compound': {'names': ['PrMnO3']}}}},
            ]
        log.debug(expected)
        log.debug(results)
        self.assertCountEqual(results, expected)



if __name__ == '__main__':
    unittest.main()
