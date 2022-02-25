# -*- coding: utf-8 -*-
"""
test_parse_mp
~~~~~~~~~~~~~

Test melting point parser.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest

from lxml import etree

from chemdataextractor.doc.text import Sentence, Paragraph
from chemdataextractor.parse.mp_new import mp_phrase
from chemdataextractor.model.model import MeltingPoint
from chemdataextractor.nlp.tokenize import ChemWordTokenizer


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestParseMp(unittest.TestCase):

    maxDiff = None

    def do_parse(self, input, expected):
        s = Sentence(input)
        log.debug(s)
        log.debug(s.tokens)
        result = next(mp_phrase.scan(s.tokens))[0]
        log.debug(etree.tostring(result, pretty_print=True, encoding='unicode'))
        print(etree.tostring(result, pretty_print=True, encoding='unicode'))
        self.assertEqual(expected, etree.tostring(result, encoding='unicode'))

    def test_mp1(self):
        s = 'Colorless solid (81% yield, 74.8 mg, 0.22 mmol); mp 77.2–77.5 °C.'
        expected = '<mp_phrase><mp><raw_value>77.2–77.5</raw_value><raw_units>°C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_mp2(self):
        s = 'Mp > 280 °C.'
        expected = '<mp_phrase><mp><raw_value>&gt;280</raw_value><raw_units>°C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_mp3(self):
        s = 'Mp: 105-110 °C'
        expected = '<mp_phrase><mp><raw_value>105-110</raw_value><raw_units>°C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_mp4(self):
        s = '4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid (Compound 67): mp 163-164 °C.'
        expected = '<mp_phrase><compound><names>4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid</names><labels>67</labels></compound><mp><raw_value>163-164</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_mp5(self):
        s = '4-Amino-3-chloro-6-[2,4-dichloro-3-(1-fluoro-1-methylethylphenyl)pyridine-3-carboxylic acid (Compound 127): mp >250 °C.'
        expected = '<mp_phrase><compound><names>4-Amino-3-chloro-6-[2,4-dichloro-3-(1-fluoro-1-methylethylphenyl)pyridine-3-carboxylic acid</names><labels>127</labels></compound><mp><raw_value>&gt;250</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_mp6(self):
        s = '4-Acetylamino-3-chloro-6-(4-cyano-2,6-difluoro-3-methoxyphenyl)pyridine-2-carboxylic acid, methyl ester: mp 146-147 °C.'
        expected = '<mp_phrase><compound><names>4-Acetylamino-3-chloro-6-(4-cyano-2,6-difluoro-3-methoxyphenyl)pyridine-2-carboxylic acid, methyl ester</names></compound><mp><raw_value>146-147</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_mp7(self):
        s = '3-Bromo-2,6-dichloroaniline: mp 71-72 °C.'
        expected = '<mp_phrase><compound><names>3-Bromo-2,6-dichloroaniline</names></compound><mp><raw_value>71-72</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_mp8(self):
        s = '4-Acetylamino-3-chloro-6-(4-chloro-2-fluoro-3-methoxymethoxy-phenyl)pyridine-2-carboxylic acid, methyl ester (Compound 34) mp 122-123 °C.'
        expected = '<mp_phrase><compound><names>4-Acetylamino-3-chloro-6-(4-chloro-2-fluoro-3-methoxymethoxy-phenyl)pyridine-2-carboxylic acid, methyl ester</names><labels>34</labels></compound><mp><raw_value>122-123</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_mp9(self):
        s = 'to give 4-acetylamino-3-chloro-6-(4-chloro-2-fluoro-5-methoxyphenyl)pyridine-2-carboxylic acid methyl ester (4.5 g, 0.012 mol): mp 180-182 °C.'
        expected = '<mp_phrase><compound><roles>to give</roles><names>4-acetylamino-3-chloro-6-(4-chloro-2-fluoro-5-methoxyphenyl)pyridine-2-carboxylic acid methyl ester</names></compound><mp><raw_value>180-182</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_degrees_only(self):
        s = 'm.p. 91 ° - 109 °'
        expected = '<mp_phrase><mp><raw_value>91-109</raw_value><raw_units>\xb0</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_afforded(self):
        s = 'afforded bissulfonic acid (102 mg, 41%) as a green solid m.p.>300 °C.'
        expected = '<mp_phrase><compound><names>bissulfonic acid</names></compound><mp><raw_value>&gt;300</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_melting_point_of(self):
        s = 'the product had a melting point of 62-68 °C.'
        expected = '<mp_phrase><mp><raw_value>62-68</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_melting_point_was(self):
        s = 'the melting point was 62-68 °C.'
        expected = '<mp_phrase><mp><raw_value>62-68</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_melting_point(self):
        s = 'melting point 62-68 °C.'
        expected = '<mp_phrase><mp><raw_value>62-68</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_melting_point_colon(self):
        s = 'Melting point: 82-83 °C.'
        expected = '<mp_phrase><mp><raw_value>82-83</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_melting_point_range(self):
        s = 'having a melting point in the range of 125-130 °C.'
        expected = '<mp_phrase><mp><raw_value>125-130</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_m_pt(self):
        s = 'M. pt. 156-158 °C.;'
        expected = '<mp_phrase><mp><raw_value>156-158</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_of_about(self):
        s = '300 g of carboxyethylmethylphosphinic acid are obtained as a white solid having a melting point of about 95 °C'
        expected = '<mp_phrase><compound><names>carboxyethylmethylphosphinic acid</names></compound><mp><raw_value>95</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_gave(self):
        s = 'under the conditions noted in example 1, gave 1-(3,4-dimethoxyphenyl)-2-(3,4,5-trimethoxyphenyl) ethylene, m.p. 150–152 °C'
        expected = '<mp_phrase><compound><names>1-(3,4-dimethoxyphenyl)-2-(3,4,5-trimethoxyphenyl)ethylene</names></compound><mp><raw_value>150\u2013152</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_gave_label(self):
        s = 'gave 2, m.p. 148 °C.;'
        expected = '<mp_phrase><labels>2</labels><mp><raw_value>148</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_give_label(self):
        s = 'to give 3, m.p. 242–244 °C.;'
        expected = '<mp_phrase><labels>3</labels><mp><raw_value>242\u2013244</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_bracket_obtained(self):
        s = '(2S,3S)-3-(t-butoxycarbonyl)amino-1,2-epoxy-4-phenylbutane was obtained (mp: 125.6 °C.).'
        expected = '<mp_phrase><compound><names>(2S,3S)-3-(t-butoxycarbonyl)amino-1,2-epoxy-4-phenylbutane</names></compound><mp><raw_value>125.6</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_bracket(self):
        s = '(2S,3S)-3-(t-butoxycarbonyl)amino-1,2-epoxy-4-phenylbutane (mp: 125.6 °C.).'
        expected = '<mp_phrase><compound><names>(2S,3S)-3-(t-butoxycarbonyl)amino-1,2-epoxy-4-phenylbutane</names></compound><mp><raw_value>125.6</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_tilde(self):
        s = 'Melting point: 96.8 ˜ 101.8 °C.'
        expected = '<mp_phrase><mp><raw_value>96.8\u02dc101.8</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_range_to(self):
        s = 'melting temperature of 203.0 to 207.0 °C.'
        expected = '<mp_phrase><mp><raw_value>203.0 to 207.0</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_melting_at(self):
        s = 'melting at 149-150 °C.'
        expected = '<mp_phrase><mp><raw_value>149-150</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_melting_range(self):
        s = 'Melting Range: 116-118 °C.'
        expected = '<mp_phrase><mp><raw_value>116-118</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_cem_yield(self):
        s = '3-Ethoxymethyl-2-(4-chlorophenyl)imino-2H-chromene (E4): (1.00 g, 64%); m.p.: 84˜86 °C., Rf=0.564'
        expected = '<mp_phrase><compound><names>3-Ethoxymethyl-2-(4-chlorophenyl)imino-2H-chromene</names><labels>E4</labels></compound><mp><raw_value>84\u02dc86</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_having(self):
        s = 'to obtain 5 parts of 1-phenyl-3-(4-phenylethynylstyryl)-5-(4-phenylethynylphenyl)pyrazoline having a melting point of 212-214 °C.'
        expected = '<mp_phrase><compound><names>1-phenyl-3-(4-phenylethynylstyryl)-5-(4-phenylethynylphenyl)pyrazoline</names></compound><mp><raw_value>212-214</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_solvent(self):
        s = 'which was crystallised from chloroform-methanol, m.p. 254–256 °C.'
        expected = '<mp_phrase><mp><raw_value>254\u2013256</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_solvent2(self):
        s = 'prepared by recrystallization from hexanes, m.p. 127-129 °C.'
        expected = '<mp_phrase><mp><raw_value>127-129</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_solvent3(self):
        s = 'residual solids in hexanes, m.p. 126-128 °C.'
        expected = '<mp_phrase><mp><raw_value>126-128</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_colon(self):
        s = '3-Cyano-2H-chromene (B1): (2.51 g, 80%); m.p.: 44-45 °C.;'
        expected = '<mp_phrase><compound><names>3-Cyano-2H-chromene</names><labels>B1</labels></compound><mp><raw_value>44-45</raw_value><raw_units>\xb0C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)

    def test_tm0(self):
        s = 'A copolymer with 8% mole percent of MeDX units exhibits a Tm of 95.5 °C, which is about 15° lower than PDX homopolymer.'
        expected = '<mp_phrase><mp><raw_value>95.5</raw_value><raw_units>°C</raw_units></mp></mp_phrase>'
        self.do_parse(s, expected)


# Edited by ti250 (8/11/2018)
# Changed format of the expected results for new-style models.
class TestParseMpCompound(unittest.TestCase):

    maxDiff = None

    def do_parse(self, input, expected):
        p = Paragraph(input)
        p.models = [MeltingPoint]
        log.debug(p)
        log.debug([r.serialize() for r in p.records])
        print([r.serialize() for r in p.records])
        self.assertEqual(expected, [r.serialize() for r in p.records])

    def test_mpc1(self):
        s = '4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid (Compound 67): mp 163-164 °C.'
        expected = [
            {'Compound': {'labels': [u'67'], 'names': [u'4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid'], 'roles': ['compound']}},
            {'MeltingPoint': {'raw_value': '163-164', 'raw_units': '°C', 'units': u'Celsius^(1.0)', 'value': [163.0, 164.0],
                             'compound': {'Compound': {'labels': [u'67'], 'names': [u'4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid']}}}}
        ]
        self.do_parse(s, expected)

    def test_mpc2(self):
        s = '3-Bromo-2,6-dichloroaniline: mp 71-72 °C.'
        expected = [
            {'Compound': {'names': [u'3-Bromo-2,6-dichloroaniline']}},
            {'MeltingPoint': {'raw_value': '71-72', 'raw_units': '°C', 'units': 'Celsius^(1.0)', 'value': [71.0, 72.0], 'compound': {'Compound': {'names': ['3-Bromo-2,6-dichloroaniline']}}}}
        ]
        self.do_parse(s, expected)



if __name__ == '__main__':
    unittest.main()
