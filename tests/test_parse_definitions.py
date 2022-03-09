# -*- coding: utf-8 -*-
"""

Test definition parsers

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import unittest

from lxml import etree
from chemdataextractor import Document
from chemdataextractor.doc.text import Sentence, Paragraph
from chemdataextractor.parse.definitions import specifier_definition, greek_symbols, definition_phrase_1
from chemdataextractor.model import TemperatureModel, StringType, ModelType, Compound
from chemdataextractor.parse.elements import R, W
from chemdataextractor.parse.actions import join


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class CurieTemperature(TemperatureModel):
    specifier_expr = ((R('Curie') + R('Temperature')) | W('Tk')).add_action(join)
    specifier = StringType(parse_expression=specifier_expr, required=True, contextual=True, updatable=True)
    compound = ModelType(Compound, required=True, contextual=True)


class TestParseDefinitions(unittest.TestCase):

    maxDiff = None

    def do_parse(self, phrase, input, expected):
        s = Sentence(input)
        log.debug(s)
        log.debug(s.tokens)
        result = next(phrase.scan(s.tokens))[0]
        log.debug(etree.tostring(result, pretty_print=True, encoding='unicode'))
        self.assertEqual(expected, etree.tostring(result, encoding='unicode'))

    def do_parse_record(self, input, expected, updated):
        doc = Document(Paragraph(input))
        doc.models = [CurieTemperature]
        for i, result in enumerate(doc.records):
            self.assertEqual(result.updated, updated)
            self.assertCountEqual(result.serialize(), expected[i])

    def test_greek_symbols(self):
        symbol_list = ['Ͱ',
                        'ͱ',
                        'Ͳ',
                        'ͳ',
                        'ʹ',
                        '͵',
                        'Ͷ',
                        'ͷ',
                        'ͺ',
                        'ͻ',
                        'ͼ',
                        'ͽ',
                        ';',
                        'Ϳ',
                        '΄',
                        '΅',
                        'Ά',
                        '·',
                        'Έ',
                        'Ή',
                        'Ί',
                        'Ό',
                        'Ύ',
                        'Ώ',
                        'ΐ',
                        'Α',
                        'Β',
                        'Γ',
                        'Δ',
                        'Ε',
                        'Ζ',
                        'Η',
                        'Θ',
                        'Ι',
                        'Κ',
                        'Λ',
                        'Μ',
                        'Ν',
                        'Ξ',
                        'Ο',
                        'Π',
                        'Ρ',
                        'Σ',
                        'Τ',
                        'Υ',
                        'Φ',
                        'Χ',
                        'Ψ',
                        'Ω',
                        'Ϊ',
                        'Ϋ',
                        'ά',
                        'έ',
                        'ή',
                        'ί',
                        'ΰ',
                        'α',
                        'β',
                        'γ',
                        'δ',
                        'ε',
                        'ζ',
                        'η',
                        'θ',
                        'ι',
                        'κ',
                        'λ',
                        'μ',
                        'ν',
                        'ξ',
                        'ο',
                        'π',
                        'ρ',
                        'ς',
                        'σ',
                        'τ',
                        'υ',
                        'φ',
                        'χ',
                        'ψ',
                        'ω',
                        'ϊ',
                        'ϋ',
                        'ό',
                        'ύ',
                        'ώ',
                        'Ϗ',
                        'ϐ',
                        'ϑ',
                        'ϒ',
                        'ϓ',
                        'ϔ',
                        'ϕ',
                        'ϖ',
                        'ϗ',
                        'Ϙ',
                        'ϙ',
                        'Ϛ',
                        'ϛ',
                        'Ϝ',
                        'ϝ',
                        'Ϟ',
                        'ϟ',
                        'Ϡ',
                        'ϡ',
                        'Ϣ',
                        'ϣ',
                        'Ϥ',
                        'ϥ',
                        'Ϧ',
                        'ϧ',
                        'Ϩ',
                        'ϩ',
                        'Ϫ',
                        'ϫ',
                        'Ϭ',
                        'ϭ',
                        'Ϯ',
                        'ϯ',
                        'ϰ',
                        'ϱ',
                        'ϲ',
                        'ϳ',
                        'ϴ',
                        'ϵ',
                        '϶',
                        'Ϸ',
                        'ϸ',
                        'Ϲ',
                        'Ϻ',
                        'ϻ',
                        'ϼ',
                        'Ͻ',
                        'Ͼ',
                        'Ͽ']
        expected = '<ct><definition><phrase>Curie temperature</phrase><COMMA>,</COMMA><specifier>TC1</specifier></definition></ct>'
        for symbol in symbol_list:
            expected = '<specifier>' + symbol + '</specifier>'
            self.do_parse(greek_symbols, symbol, expected)

    def test_curie_definition(self):
        s = 'the Curie Temperature, TC,'
        expected = '<definition><phrase>Curie Temperature</phrase><COMMA>,</COMMA><specifier>TC</specifier></definition>'
        self.do_parse(specifier_definition, s, expected)
    
    def test_curie_definition_brackets(self):
        s = 'Curie temperature (TC)'
        expected = '<definition><phrase>Curie temperature</phrase><LRB>(</LRB><specifier>TC</specifier></definition>'
        self.do_parse(specifier_definition, s, expected)
    
    def test_uv_vis_definition(self):
        s = 'uv-vis absorption peak, λmax'
        expected = '<definition><phrase>uv - vis absorption peak</phrase><COMMA>,</COMMA><specifier>λmax</specifier></definition>'
        self.do_parse(specifier_definition, s, expected)

    def test_full_sentence(self):
        p_with_def = 'We will look at the Curie Temperature, Tc. Tc for TiO2 is 450 K.'
        p_no_def = 'Tk for TiO2 is 450 K.'
        expected_with_def = [{'CurieTemperature': {'raw_value': '450', 'value': [450.000], 'specifier': 'Tc', 'compound': {'Compound': {'names': ['TiO2']}}}}]
        expected_no_def = [{'CurieTemperature': {'raw_value': '450', 'value': [450.000], 'specifier': 'Tk', 'compound': {'Compound': {'names': ['TiO2']}}}}]
        self.do_parse_record(p_with_def, expected_with_def, updated=True)
        self.do_parse_record(p_no_def, expected_no_def, updated=False)


if __name__ == '__main__':
    unittest.main()
