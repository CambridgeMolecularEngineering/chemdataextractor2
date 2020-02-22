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



class TestSnowball(unittest.TestCase):

    maxDiff = None
    training_corpus = 'tests/data/relex/curie_training_set/'

    def test_snowball_candidates(self):
        """Test that Candidate Relation objects are correctly created
        """
        sentence = Sentence('The Curie temperature Tc of MnO is 120 K,')
        candidates = [r.serialize() for r in sb.candidates(sentence.tagged_tokens)]
        expected = [{'specifier': 'Curie temperature', 'compound': {'names': 'MnO'}, 'raw_value': '120', 'raw_units': 'K', 'confidence': 0}]
        self.assertEqual(expected, candidates)

    def test_retrieve_entities(self):
        """Test entity retrieval from a parse result
        """
        sentence = Sentence('BiFeO3 displays a Curie temperature of 1103 K,')
        sentence_parser = [p for p in sb.model.parsers if isinstance(p, AutoSentenceParser)][0]
        detected = []
        for result in sentence_parser.root.scan(sentence.tagged_tokens):
            if result:
                for entity in sb.retrieve_entities(CurieTemperature, result[0]):
                    detected.append((entity[0], entity[1]))
        expected = [('1103', 'raw_value'), ('K', 'raw_units'), ('Curie temperature', 'specifier'), ('BiFeO3', ('compound', 'names'))]
        self.assertCountEqual(detected, expected)

    def test_parse_sentence(self):
        """Test Snowball Sentence Parsing
        """
        train_sentence = Sentence('The Curie temperature of BiFeO3 is 1103 K')
        candidates = sb.candidates(train_sentence.tagged_tokens)
        sb.update(train_sentence.raw_tokens, candidates)

        test_sentence = Sentence('The Curie temperature for MnO is 120 K')
        models = []
        for model in sb.parse_sentence(test_sentence.tagged_tokens):
            models.append(model.serialize())
        expected = [{'CurieTemperature': {'compound': {'Compound': {'names': {'MnO'}}},
                        'confidence': 0.7333333333333333,
                        'raw_units': 'K',
                        'raw_value': '120',
                        'specifier': 'Curie temperature',
                        'units': 'Kelvin^(1.0)',
                        'value': [120.0]}}]
        self.assertEqual(expected, models)



if __name__ == '__main__':
    unittest.main()
