# -*- coding: utf-8 -*-
"""

Test relex Cluster

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

from chemdataextractor.relex import Snowball, Relation, Entity, Phrase, Cluster
from chemdataextractor.model import TemperatureModel
from chemdataextractor.model import BaseModel, StringType, ListType, ModelType, Compound
from chemdataextractor.parse.elements import I, R, Any, OneOrMore, Optional, W
from chemdataextractor.parse.common import lrb, rrb, delim
from chemdataextractor.parse.actions import join, merge
from chemdataextractor.parse.cem import chemical_name, names_only
from chemdataextractor.doc import Sentence
from collections import OrderedDict


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Define a test model
class CurieTemperature(TemperatureModel):
    specifier_expression = (W('Curie') + I('temperature')).add_action(join)
    specifier = StringType(parse_expression=specifier_expression, required=True, updatable=True)
    compound = ModelType(Compound, required=True)


tokens = ['the', 'curie', 'temperature', 'of', 'BiFeO3', 'is', '1103', 'K', '.']
entities = [
            Entity('curie temperature', 'curietemperature__specifier', (I('curie') + I('temperature')).add_action(join), 1, 3),
            Entity('BiFeO3', 'compound__names', names_only, 4, 5),
            Entity('1103', 'curietemperature__raw_value', R(r'\d+(\.\d+)?'), 6, 7),
            Entity('K', 'curietemperature__raw_units', I('K'), 7, 8)]

relations = [Relation(entities, confidence=1.0)]

phrase = Phrase(tokens, relations, 1, 1)
test_cluster = Cluster(label='0')
test_cluster.add_phrase(phrase)

class TestCluster(unittest.TestCase):

    maxDiff = None
    training_corpus = 'tests/data/relex/curie_training_set/'

    def test_cluster_dictionaries(self):
        expected = {'middle_1': {'token dict': OrderedDict([('of', [1.0, 1.0])]),
        'total recurring words': 0,
        'total words': 1,
        'unique words': []},
        'middle_2': {'token dict': OrderedDict([('is', [1.0, 1.0])]),
                    'total recurring words': 0,
                    'total words': 1,
                    'unique words': []},
        'middle_3': {'token dict': OrderedDict([('<Blank>', [1.0, 1.0])]),
                    'total recurring words': 0,
                    'total words': 1,
                    'unique words': []},
        'prefix': {'token dict': OrderedDict([('the', [1.0, 1.0])]),
                'total recurring words': 0,
                'total words': 1,
                'unique words': []},
        'suffix': {'token dict': OrderedDict([('.', [1.0, 1.0])]),
                'total recurring words': 0,
                'total words': 1,
                'unique words': []}}
        self.assertEqual(expected, test_cluster.dictionaries)

    def test_cluster_pattern(self):
        expected = 'the (curietemperature__specifier) of (compound__names) is (curietemperature__raw_value) <Blank> (curietemperature__raw_units) .'
        self.assertEqual(expected, test_cluster.pattern.to_string())

    def test_cluster_pattern_confidence(self):
        expected = 1.0
        self.assertEqual(expected, test_cluster.pattern.confidence)

    def test_get_relations(self):
        """Test relation retrieval using Pattern object
        """

        s = Sentence('the curie temperature of MnO is 100 K.')
        result = [r.serialize() for r in test_cluster.get_relations(s.tokens)]
        expected = [{
            'compound': {'names': 'MnO'},
            'curietemperature': {'specifier': 'curie temperature',
            'raw_value': '100',
            'raw_units': 'K'},
            'confidence': 0}]
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
