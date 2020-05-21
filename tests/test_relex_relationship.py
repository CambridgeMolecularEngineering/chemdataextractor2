# -*- coding: utf-8 -*-
"""

Test relex RelationShip

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

from chemdataextractor.relex import Snowball, Relation, Entity
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


class TestRelation(unittest.TestCase):

    maxDiff = None
    training_corpus = 'tests/data/relex/curie_training_set/'

    def test_relation_serialize(self):
        """Test relation serialization
        """
        entities = [
            Entity('e1', 'model__cem', I('e1'), 0, 2), 
            Entity('e2', 'model__specifier', I('e2'), 2, 4), 
            Entity('e3', 'model__value', I('e3'), 4, 6), 
            Entity('e4', 'model__unit', I('e4'), 6, 7)]
        relation = Relation(entities, confidence=0)
        expected = {'model': {'specifier': 'e2', 'value': 'e3', 'unit': 'e4', 'cem': 'e1'}, 'confidence': 0}
        self.assertDictEqual(relation.serialize(), expected)
    
    def test_relation_not_eq(self):
        entities = [
            Entity('e1', 'cem', I('e1'), 0, 2), 
            Entity('e2', 'specifier', I('e2'), 2, 4), 
            Entity('e3', 'value', I('e3'), 4, 6), 
            Entity('e4', 'unit', I('e4'), 6, 7)]
        entities2 = [
            Entity('e4', 'cem', I('e1'), 0, 2), 
            Entity('e2', 'specifier', I('e2'), 2, 4), 
            Entity('e3', 'value', I('e3'), 4, 6), 
            Entity('e4', 'unit', I('e4'), 6, 7)]
        relation1 = Relation(entities, confidence=0)
        relation2 = Relation(entities2, confidence=0)
        self.assertNotEqual(relation1, relation2)
    
    def test_relation_eq(self):
        entities = [
            Entity('e1', 'cem', I('e1'), 0, 2), 
            Entity('e2', 'specifier', I('e2'), 2, 4), 
            Entity('e3', 'value', I('e3'), 4, 6), 
            Entity('e4', 'unit', I('e4'), 6, 7)]
        entities2 = [
            Entity('e1', 'cem', I('e1'), 0, 2), 
            Entity('e2', 'specifier', I('e2'), 2, 4), 
            Entity('e3', 'value', I('e3'), 4, 6), 
            Entity('e4', 'unit', I('e4'), 6, 7)]
        relation1 = Relation(entities, confidence=0)
        relation2 = Relation(entities2, confidence=0)
        self.assertEqual(relation1, relation2)










if __name__ == '__main__':
    unittest.main()
