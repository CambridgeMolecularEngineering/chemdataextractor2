# -*- coding: utf-8 -*-
"""

Test relex Phrase

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

from chemdataextractor.relex import Snowball, Relation, Entity, Phrase
from chemdataextractor.model import TemperatureModel
from chemdataextractor.model import BaseModel, StringType, ListType, ModelType, Compound
from chemdataextractor.parse.elements import I, R, Any, OneOrMore, Optional, W
from chemdataextractor.parse.common import lrb, rrb, delim
from chemdataextractor.parse.actions import join, merge
from chemdataextractor.parse.cem import chemical_name
from chemdataextractor.doc import Sentence


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Define a test model
class CurieTemperature(TemperatureModel):
    specifier_expression = (W('Curie') + I('temperature')).add_action(join)
    specifier = StringType(parse_expression=specifier_expression, required=True, updatable=True)
    compound = ModelType(Compound, required=True)


class TestPhrase(unittest.TestCase):

    maxDiff = None
    training_corpus = 'tests/data/relex/curie_training_set/'

    def test_phrase_create(self):
        """Test that Candidate Relation objects are correctly created
        """
        tokens = ['this', 'is', 'a', 'test', 'phrase']
        entities = [
            Entity('this', 'who', I('this'), 0, 1),
            Entity('phrase', 'what', I('phrase'), 4, 5)]
        relations = [Relation(entities, confidence=1.0)]
        phrase = Phrase(tokens, relations, 1, 1)
        expected = '<Blank> (who) is a test (what) <Blank>'
        self.assertEqual(phrase.to_string(), expected)
    
    def test_phrase_order(self):
        tokens = ['this', 'is', 'a', 'test', 'phrase']
        entities = [
            Entity('this', 'who', I('this'), 0, 1),
            Entity('phrase', 'what', I('phrase'), 4, 5)]
        relations = [Relation(entities, confidence=1.0)]
        phrase = Phrase(tokens, relations, 1, 1)
        expected = ['who', 'what']
        self.assertEqual(phrase.order, expected)
        self.assertEqual(phrase.number_of_entities, 2)
    
    def test_phrase_multiple_relations(self):
        tokens = ['this', 'is', 'a', 'test', 'phrase', 'that', 'sentence', 'is', 'not']
        entities = [
            Entity('this', 'who', I('this'), 0, 1),
            Entity('phrase', 'what', I('phrase'), 4, 5),
            Entity('that', 'who', I('that'), 5, 6),
            Entity('sentence', 'what', I('sentence'), 6, 7)]
        relations = [Relation(entities[0:2], confidence=1.0), Relation(entities[2:], confidence=1.0)]

        phrase = Phrase(tokens, relations, 1, 1)
        expected = ['who', 'what', 'who', 'what']
        self.assertEqual(phrase.order, expected)
        self.assertEqual(phrase.number_of_entities, 4)

    def test_phrase_multiple_relations_2(self):
        tokens = ['this', 'is', 'a', 'test', 'phrase', 'but', 'that', 'sentence', 'is', 'not']
        entities = [
            Entity('this', 'who', I('this'), 0, 1),
            Entity('phrase', 'what', I('phrase'), 4, 5),
            Entity('that', 'who', I('that'), 6, 7),
            Entity('sentence', 'what', I('sentence'), 7, 8)]
        relations = [Relation(entities[0:2], confidence=1.0), Relation(entities[2:], confidence=1.0)]

        phrase = Phrase(tokens, relations, 1, 1)
        expected = '<Blank> (who) is a test (what) but (who) <Blank> (what) is'
        self.assertEqual(phrase.to_string(), expected)

    def test_phrase_elements(self):
        tokens = ['this', 'is', 'a', 'test', 'phrase', 'but', 'that', 'sentence', 'is', 'not']
        entities = [
            Entity('this', 'who', I('this'), 0, 1),
            Entity('phrase', 'what', I('phrase'), 4, 5),
            Entity('that', 'who', I('that'), 6, 7),
            Entity('sentence', 'what', I('sentence'), 7, 8)]
        relations = [Relation(entities[0:2], confidence=1.0), Relation(entities[2:], confidence=1.0)]

        phrase = Phrase(tokens, relations, 1, 1)
        expected = {
            'prefix': {'tokens': ['<Blank>']},
            'middle_1': {'tokens': ['is', 'a', 'test']},
            'middle_2': {'tokens': ['but']},
            'middle_3': {'tokens': ['<Blank>']},
            'suffix': {'tokens': ['is']}}
        self.assertEqual(phrase.elements, expected)







if __name__ == '__main__':
    unittest.main()
