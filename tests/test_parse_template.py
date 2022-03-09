from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest
from chemdataextractor.model.model import CurieTemperature
from chemdataextractor.doc import Sentence, Document, Paragraph, Figure, Caption, Title
from chemdataextractor.parse.template import QuantityModelTemplateParser, MultiQuantityModelTemplateParser
from lxml import etree
import pprint
from chemdataextractor.reader.elsevier import ElsevierXmlReader
from chemdataextractor.parse.auto import AutoTableParser
import copy


class TestQuantityModelTemplate(unittest.TestCase):

    maxDiff = None

    def parse(self, sentence, element):
        model = copy.copy(CurieTemperature)
        parser = QuantityModelTemplateParser()
        parser.model = model
        result = etree.tostring(
            [i for i in getattr(parser, element, None).scan(sentence.tokens)][0][0])
        return result

    def interpet(self, s):
        models = copy.copy([CurieTemperature])
        d = Document(s)
        d.add_models(models)
        return d.records.serialize()

    def test_prefix(self):
        s = Sentence('Curie temperature of approximately')
        expected = b'<specifier>Curie temperature</specifier>'
        self.assertEqual(expected, self.parse(s, 'prefix'))

    def test_specifier_and_value(self):
        s = Sentence('Tc reaches a maximum value of 100 K')
        expected = b'<root_phrase><specifier>Tc</specifier><raw_value>100</raw_value><raw_units>K</raw_units></root_phrase>'
        self.assertEqual(expected, self.parse(s, 'root'))

    def test_cem_before_specifier_and_value(self):
        s = Sentence(
            'BiFeO3 with a Curie temperature of approximately 1100 K')
        expected = b'<root_phrase><cem_phrase><compound><names>BiFeO3</names></compound></cem_phrase><specifier>Curie temperature</specifier><raw_value>1100</raw_value><raw_units>K</raw_units></root_phrase>'
        self.assertEqual(expected, self.parse(
            s, 'cem_before_specifier_and_value_phrase'))

    def test_specifier_before_cem_and_value(self):
        s = Sentence('The Curie temperature of La0.7Ca0.3MnO3 is 300 K')
        expected = b'<root_phrase><specifier>Curie temperature</specifier><cem_phrase><compound><names>La0.7Ca0.3MnO3</names></compound></cem_phrase><raw_value>300</raw_value><raw_units>K</raw_units></root_phrase>'
        self.assertEqual(expected, self.parse(
            s, 'specifier_before_cem_and_value_phrase'))

    def test_cem_after_specifier_and_value(self):
        s = Sentence('Curie temperature of 1100 K in BiFeO3')
        expected = b'<root_phrase><specifier>Curie temperature</specifier><raw_value>1100</raw_value><raw_units>K</raw_units><cem_phrase><compound><names>BiFeO3</names></compound></cem_phrase></root_phrase>'
        self.assertEqual(expected, self.parse(
            s, 'cem_after_specifier_and_value_phrase'))

    def test_value_specifier_cem(self):
        s = Sentence(
            '1100 K, corresponding to the Curie temperature of BiFeO3')
        expected = b'<root_phrase><raw_value>1100</raw_value><raw_units>K</raw_units><COMMA>,</COMMA><specifier>Curie temperature</specifier><cem_phrase><compound><names>BiFeO3</names></compound></cem_phrase></root_phrase>'
        self.assertEqual(expected, self.parse(s, 'value_specifier_cem_phrase'))


class TestMultiQuantityTemplate(unittest.TestCase):
    maxDiff = None

    def parse(self, sentence, element):
        model = copy.copy(CurieTemperature)
        parser = MultiQuantityModelTemplateParser()
        parser.model = model
        result = etree.tostring(
            [i for i in getattr(parser, element, None).scan(sentence.tokens)][0][0])
        return result

    def interpret(self, sentence):
        model = copy.copy(CurieTemperature)
        model.parsers = [MultiQuantityModelTemplateParser()]
        sentence.add_models([model])
        result = sentence.records.serialize()
        model.parsers = [MultiQuantityModelTemplateParser()]
        return result

    def test_prefix(self):
        s = Sentence('Curie temperature of approximately')
        expected = b'<specifier>Curie temperature</specifier>'
        self.assertEqual(expected, self.parse(s, 'prefix'))

    def test_list_of_values_1(self):
        s = Sentence('100, 200 and 300 K')
        expected = b'<value_list><raw_value>100</raw_value><raw_value>200</raw_value><raw_value>300</raw_value><raw_units>K</raw_units></value_list>'
        self.assertEqual(expected, self.parse(s, 'list_of_values'))

    def test_list_of_values_2(self):
        s = Sentence('100 K, 200 K and 300 K')
        expected = b'<value_list><raw_value>100</raw_value><raw_units>K</raw_units><raw_value>200</raw_value><raw_units>K</raw_units><raw_value>300</raw_value><raw_units>K</raw_units></value_list>'
        self.assertEqual(expected, self.parse(s, 'list_of_values'))

    def test_list_of_cems(self):
        s = Sentence('BiFeO3, MnO and Fe204')
        expected = b'<cem_list><compound><names>BiFeO3</names></compound><compound><names>MnO</names></compound><compound><names>Fe204</names></compound></cem_list>'
        self.assertEqual(expected, self.parse(s, 'list_of_cems'))

    def test_list_of_properties(self):
        s = Sentence('TC1 = 100 K and TC2 = 300 K')
        expected = b'<property_list><property><specifier>TC1</specifier><raw_value>100</raw_value><raw_units>K</raw_units></property><property><specifier>TC2</specifier><raw_value>300</raw_value><raw_units>K</raw_units></property></property_list>'
        self.assertEqual(expected, self.parse(s, 'list_of_properties'))

    def test_multi_entity_phrase_1(self):
        s = Sentence(
            'BiFeO3 exhibits two transitions at TC1 = 640 K and TC2 = 1103 K')
        expected = b'<multi_entity_phrase_1><compound><names>BiFeO3</names></compound><property_list><property><specifier>TC1</specifier><raw_value>640</raw_value><raw_units>K</raw_units></property><property><specifier>TC2</specifier><raw_value>1103</raw_value><raw_units>K</raw_units></property></property_list></multi_entity_phrase_1>'
        self.assertEqual(expected, self.parse(s, 'multi_entity_phrase_1'))

    def test_multi_entity_phrase_3a(self):
        s = Sentence(
            'In BiFeO3, LaFeO3 and MnO the Curie temperature is found to be 100, 200 and 300 K, respectively')
        expected = b'<multi_entity_phrase_3><cem_list><compound><names>BiFeO3</names></compound><compound><names>LaFeO3</names></compound><compound><names>MnO</names></compound></cem_list><specifier>Curie temperature</specifier><value_list><raw_value>100</raw_value><raw_value>200</raw_value><raw_value>300</raw_value><raw_units>K</raw_units></value_list></multi_entity_phrase_3>'
        self.assertEqual(expected, self.parse(s, 'multi_entity_phrase_3a'))

    def test_multi_entity_phrase_3b(self):
        s = Sentence(
            'Curie temperatures of 100, 200 and 300 K in BiFeO3, LaFeO3 and MnO')
        expected = b'<multi_entity_phrase_3><specifier>Curie temperatures</specifier><value_list><raw_value>100</raw_value><raw_value>200</raw_value><raw_value>300</raw_value><raw_units>K</raw_units></value_list><IN>in</IN><cem_list><compound><names>BiFeO3</names></compound><compound><names>LaFeO3</names></compound><compound><names>MnO</names></compound></cem_list></multi_entity_phrase_3>'
        self.assertEqual(expected, self.parse(s, 'multi_entity_phrase_3b'))

    def test_multi_entity_phrase_3c(self):
        s = Sentence('Curie temperature of 100 K in BiFeO3 to 300 K in LaFeO3')
        expected = b'<multi_entity_phrase_3><property><specifier>Curie temperature</specifier><raw_value>100</raw_value><raw_units>K</raw_units></property><compound><names>BiFeO3</names></compound><raw_value>300</raw_value><raw_units>K</raw_units><compound><names>LaFeO3</names></compound></multi_entity_phrase_3>'
        self.assertEqual(expected, self.parse(s, 'multi_entity_phrase_3c'))

    def test_multi_entity_phrase_4a(self):
        s = Sentence('Curie temperature of 100 K in BiFeO3, LaFeO3 and MnO')
        expected = b'<multi_entity_phrase_4><property><specifier>Curie temperature</specifier><raw_value>100</raw_value><raw_units>K</raw_units></property><cem_list><compound><names>BiFeO3</names></compound><compound><names>LaFeO3</names></compound><compound><names>MnO</names></compound></cem_list></multi_entity_phrase_4>'
        self.assertEqual(expected, self.parse(s, 'multi_entity_phrase_4a'))

    def test_multi_entity_phrase_4b(self):
        s = Sentence(
            'MnO, LiO and BiFeO3 all show ferromagnetism below the Curie temperature of ~100 K')
        expected = b'<multi_entity_phrase_4><cem_list><compound><names>MnO</names></compound><compound><names>LiO</names></compound><compound><names>BiFeO3</names></compound></cem_list><property><specifier>Curie temperature</specifier><raw_value>100</raw_value><raw_units>K</raw_units></property></multi_entity_phrase_4>'
        self.assertEqual(expected, self.parse(s, 'multi_entity_phrase_4b'))

    def test_interpret_1(self):
        s = Sentence(
            'BiFeO3 is very interesting as it exhibits two transitions at TC1 = 640 K and TC2 = 1103 K')
        expected = [{'Compound': {'names': ['BiFeO3']}},
                    {'CurieTemperature': {'compound': {'Compound': {'names': ['BiFeO3']}},
                                          'raw_units': 'K',
                                          'raw_value': '1103',
                                          'specifier': 'TC2',
                                          'units': 'Kelvin^(1.0)',
                                          'value': [1103.0]}},
                    {'CurieTemperature': {'compound': {'Compound': {'names': ['BiFeO3']}},
                                          'raw_units': 'K',
                                          'raw_value': '640',
                                          'specifier': 'TC1',
                                          'units': 'Kelvin^(1.0)',
                                          'value': [640.0]}}]
        self.assertEqual(self.interpret(s), expected)

if __name__ == '__main__':
    unittest.main()
