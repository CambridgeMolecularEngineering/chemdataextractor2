# -*- coding: utf-8 -*-
"""

Test relex snowball

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import io
import sys
import logging
import os
import unittest

from chemdataextractor.relex import Snowball, Relation, Entity, Cluster, Pattern, Phrase
from chemdataextractor.model import TemperatureModel
from chemdataextractor.model.units.energy import EnergyModel
from chemdataextractor.model import BaseModel, StringType, ListType, ModelType, Compound
from chemdataextractor.parse.elements import I, R, Any, OneOrMore, Optional, W
from chemdataextractor.parse.common import lrb, rrb, delim
from chemdataextractor.parse.actions import join, merge
from chemdataextractor.parse.cem import chemical_name
from chemdataextractor.doc import Sentence
from chemdataextractor.parse.auto import AutoSentenceParser


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Define a test model
class CurieTemperature(TemperatureModel):
    specifier_expression = (W('Curie') + I('temperature')).add_action(join)
    specifier = StringType(parse_expression=specifier_expression, required=True, updatable=True)
    compound = ModelType(Compound, required=True)
    parsers = [AutoSentenceParser()]

sb = Snowball(CurieTemperature, tc=0.5, tsim=0.5)

class Temperature(TemperatureModel):
    specifier_expression =(I('temperature') | W('T'))
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=False, updatable=True)
    compound = ModelType(Compound, required=False, contextual=False, updatable=False)
    parsers = [AutoSentenceParser()]

class BandGap(EnergyModel):
    specifier_expression =((I('band') + I('gap')) | W('Eg')).add_action(join)
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=True, updatable=True)
    compound = ModelType(Compound, required=True, contextual=True, binding=True, updatable=False)
    temperature = ModelType(Temperature, required=False, contextual=False)
    temperature.model_class.fields['raw_value'].required = False
    temperature.model_class.fields['raw_units'].required = False
    parsers = [AutoSentenceParser()]

nested_snowball = Snowball(model=BandGap, tc=0.5, tsim=0.5, max_candidate_combinations=40)


class TestSnowball(unittest.TestCase):

    maxDiff = None
    training_corpus = 'tests/data/relex/curie_training_set/'

    def test_snowball_candidates(self):
        """Test that Candidate Relation objects are correctly created
        """
        sentence = Sentence('The Curie temperature Tc of MnO is 120 K,')
        candidates = [r.serialize() for r in sb.candidates(sentence.tokens)][0]
        expected = [{'curietemperature': {'specifier': 'Curie temperature', 'raw_value': '120', 'raw_units': 'K'}, 'compound': {'names': 'MnO'}, 'confidence': 0}]
        self.assertDictEqual(expected[0], candidates)

    def test_retrieve_entities(self):
        """Test entity retrieval from a parse result
        """
        sentence = Sentence('BiFeO3 displays a Curie temperature of 1103 K,')
        sentence_parser = [p for p in sb.model.parsers if isinstance(p, AutoSentenceParser)][0]
        detected = []
        for result in sentence_parser.root.scan(sentence.tokens):
            if result:
                for entity in sb.retrieve_entities(CurieTemperature, result[0]):
                    detected.append((entity[0], entity[1]))
        expected = [('1103', ('curietemperature', 'raw_value')), ('K', ('curietemperature', 'raw_units')), ('Curie temperature', ('curietemperature', 'specifier')), ('BiFeO3', ('compound', 'names'))]
        self.assertCountEqual(detected, expected)
    
    def test_parse_sentence(self):
        """Test Snowball Sentence Parsing
        """
        train_sentence = Sentence('The Curie temperature of BiFeO3 is 1103 K')
        candidates = sb.candidates(train_sentence.tokens)
        sb.update(train_sentence.raw_tokens, candidates)

        test_sentence = Sentence('The Curie temperature for MnO is 120 K')
        models = []
        for model in sb.parse_sentence(test_sentence):
            models.append(model.serialize())
        expected = [{'CurieTemperature': {'compound': {'Compound': {'names': ['MnO']}},
                        'confidence': 0.7333333333333333,
                        'raw_units': 'K',
                        'raw_value': '120',
                        'specifier': 'Curie temperature',
                        'units': 'Kelvin^(1.0)',
                        'value': [120.0]}}]
        self.assertDictEqual(expected[0], models[0])

    def test_parse_nested_sentence(self):
        s1 = Sentence('Si has a  band gap of 1.1 eV at an applied temperature of 300 K.')
        s2 = Sentence('MnO has a band gap of 5 eV in an applied temperature of 700 K.')
        candidates = nested_snowball.candidates(s1.tokens)
        c = [i for i in candidates if i.entities[2].tag == 'bandgap__raw_value']
        nested_snowball.update(s1.raw_tokens, c)

        models = []
        for model in nested_snowball.parse_sentence(s2):
            models.append(model.serialize())
        expected = [{'BandGap': {'compound': {'Compound': {'names': ['MnO']}},
              'confidence': 0.9555555555555555,
              'raw_units': 'eV',
              'raw_value': '5',
              'specifier': 'band gap',
              'temperature': {'Temperature': {'compound': {'Compound': {'names': ['MnO']}},
                                              'raw_units': 'K',
                                              'raw_value': '700',
                                              'specifier': 'temperature',
                                              'value': [700.0],
                                              'units': 'Kelvin^(1.0)',}},
              'units': 'ElectronVolt^(1.0)',
              'value': [5.0]}}]
        self.assertDictEqual(expected[0], models[0])




if __name__ == '__main__':
    unittest.main()
