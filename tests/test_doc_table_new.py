# -*- coding: utf-8 -*-
"""
Test the Table Document element and Table autoparsers.

"""

from chemdataextractor.model.units.quantity_model import DimensionlessModel
from chemdataextractor.parse.elements import R
from chemdataextractor.model.base import StringType, ModelType
from chemdataextractor.model.model import Compound
from chemdataextractor.doc.table_new import Table
from chemdataextractor.doc import Caption
from chemdataextractor.doc import Document
from chemdataextractor.reader.elsevier import ElsevierXmlReader
from chemdataextractor.model.units.length import LengthModel
from chemdataextractor.parse.actions import merge

import logging
import unittest

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# Model classes used for testing
class CoordinationNumber(DimensionlessModel):
    coordination_number_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    specifier = R('^(N|n|k)$')
    cn_label = StringType(parse_expression=coordination_number_label)
    compound = ModelType(Compound)


class InteratomicDistance(LengthModel):
    specifier = (R('^bond$') + R('^distance')).add_action(merge)
    rij_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    species = StringType(parse_expression=rij_label, required=True, contextual=False)
    compound = ModelType(Compound, required=True, contextual=True)


class TestTable(unittest.TestCase):
    """Tests for automated parsing of tables"""

    maxDiff = None

    def do_table_1(self, expected):
        table = Table(caption=Caption("This is my table."),
                      table_data="./data/tables/table_example_1.csv",
                      models=[CoordinationNumber, Compound])
        result = table.records
        self.assertListEqual(expected, result)

    def test_contextual_required_combinations(self):
        """
        Tests various combinations of merging in-table records based on the 'required' and 'contextual' flags
        in the model fields.
        """

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = True
        expected = [['unidentified', {'CoordinationNumber': {'cn_label': 'Ti-O'}}], {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'cn_label': 'Ti-O'}}, {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'cn_label': 'Ti-O'}}, {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = True
        expected = [['unidentified', {'CoordinationNumber': {'cn_label': 'Ti-O'}}], {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'cn_label': 'Ti-O'}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = True
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'cn_label': 'Ti-O'}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = True
        expected = [['unidentified', {'CoordinationNumber': {'cn_label': 'Ti-O'}}], ['unidentified', {'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676]}}], {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'cn_label': 'Ti-O'}}, {'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676]}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = False
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'cn_label': 'Ti-O'}}, {'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676]}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = True
        expected = [['unidentified', {'CoordinationNumber': {'cn_label': 'Ti-O'}}], ['unidentified', {'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676]}}], {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = True
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = False
        expected = [{'CoordinationNumber': {'cn_label': 'Ti-O'}}, {'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676]}}, {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

        CoordinationNumber.cn_label.required = False
        CoordinationNumber.cn_label.contextual = True
        CoordinationNumber.compound.required = False
        CoordinationNumber.compound.contextual = True
        expected = [{'CoordinationNumber': {'cn_label': 'Ti-O'}}, {'CoordinationNumber': {'raw_value': '78.31676', 'value': [78.31676]}}, {'CoordinationNumber': {'raw_value': '1319.193', 'value': [1319.193], 'cn_label': 'O-O', 'compound': {'names': ['TiO3']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO4']}}}, {'CoordinationNumber': {'raw_value': '1844.746', 'value': [1844.746], 'cn_label': 'O-O', 'compound': {'names': ['TiO5']}}}, {'CoordinationNumber': {'raw_value': '23707.91', 'value': [23707.91], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO6']}}}, {'CoordinationNumber': {'raw_value': '1881.641', 'value': [1881.641], 'cn_label': 'O-O', 'compound': {'names': ['TiO7']}}}, {'CoordinationNumber': {'raw_value': '2963.489', 'value': [2963.489], 'cn_label': 'Ti-O', 'compound': {'names': ['TiO8']}}}, {'CoordinationNumber': {'raw_value': '2213.910', 'value': [2213.91], 'cn_label': 'O-O', 'compound': {'names': ['TiO9']}}}, {'CoordinationNumber': {'raw_value': '18000.00', 'value': [18000.0], 'cn_label': 'Ti-Ti', 'compound': {'names': ['TiO10']}}}]
        self.do_table_1(expected)

    def test_caption_compound(self):
        """
        Tests the addition of the caption compound to table records without a compound
        """
        f = open('./data/tables/j.commatsci.2018.02.056.xml', 'rb')
        doc = Document.from_file(f, readers=[ElsevierXmlReader()])
        f.close()
        table = doc.tables[0]
        table.models = [InteratomicDistance]
        result = table.records
        expected = [{'InteratomicDistance': {'raw_value': '3.1814', 'raw_units': 'Å', 'value': [3.1814], 'units': 'Angstrom^(1.0)', 'species': 'Mg-Mg', 'compound': {'names': ['Mg2Si']}}}, {'InteratomicDistance': {'raw_value': '2.7552', 'raw_units': 'Å', 'value': [2.7552], 'units': 'Angstrom^(1.0)', 'species': 'Mg-Si', 'compound': {'names': ['Mg2Si']}}}, {'InteratomicDistance': {'raw_value': '4.4992', 'raw_units': 'Å', 'value': [4.4992], 'units': 'Angstrom^(1.0)', 'species': 'Si-Si', 'compound': {'names': ['Mg2Si']}}}, {'Compound': {'names': ['Mg2Si']}}]
        self.assertListEqual(expected, result)

    def test_unidentified_records(self):
        """
        Tests the retrieval of 'unidentified' records (records that need to have a compound but the compound is the
        only missing field.
        """
        f = open('./data/tables/j.commatsci.2018.02.056_2.xml', 'rb')
        doc = Document.from_file(f, readers=[ElsevierXmlReader()])
        f.close()
        table = doc.tables[0]
        table.models = [InteratomicDistance]
        result = table.records
        expected = [['unidentified', {'InteratomicDistance': {'raw_value': '3.1814', 'raw_units': 'Å', 'value': [3.1814], 'units': 'Angstrom^(1.0)', 'species': 'Mg-Mg'}}], ['unidentified', {'InteratomicDistance': {'raw_value': '2.7552', 'raw_units': 'Å', 'value': [2.7552], 'units': 'Angstrom^(1.0)', 'species': 'Mg-Si'}}], ['unidentified', {'InteratomicDistance': {'raw_value': '4.4992', 'raw_units': 'Å', 'value': [4.4992], 'units': 'Angstrom^(1.0)', 'species': 'Si-Si'}}]]
        self.assertListEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
