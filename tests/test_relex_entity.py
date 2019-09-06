# -*- coding: utf-8 -*-
"""

Test relex Entity

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
from chemdataextractor.relex.entity import Entity

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Define a test model
class CurieTemperature(TemperatureModel):
    specifier_expression = (W('Curie') + I('temperature')).add_action(join)
    specifier = StringType(parse_expression=specifier_expression, required=True, updatable=True)
    compound = ModelType(Compound, required=True)


class TestEntity(unittest.TestCase):

    maxDiff = None
    training_corpus = 'tests/data/relex/curie_training_set/'

    def test_entity_serialize_1(self):
        """Test that Entity objects are correctly serialized
        """
        entity = Entity('test_entity', 'test_tag', I('test'), 0, 10)
        expected = {'test_tag': 'test_entity'}
        self.assertEqual(entity.serialize(), expected)
    
    def test_entity_serialize_2(self):
        """Test that nested Entity objects are correctly serialized
        """
        entity = Entity('test_entity', 'test_tag__test_sub_tag', I('test'), 0, 10)
        expected = {'test_tag': {'test_sub_tag': 'test_entity'}}
        self.assertEqual(entity.serialize(), expected)
    
    def test_not_eq(self):
        e1 = Entity('e1', 'test', I('e1'), 0, 2)
        e2 = Entity('e2', 'test', I('e2'), 0,2)
        self.assertNotEqual(e1, e2)
    
    def test_eq(self):
        e1 = Entity('e1', 'test', I('e1'), 0, 2)
        e2 = Entity('e1', 'test', I('e1'), 0,2)
        self.assertEqual(e1, e1)
    








if __name__ == '__main__':
    unittest.main()
