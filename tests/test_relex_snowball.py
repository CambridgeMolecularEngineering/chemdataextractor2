# -*- coding: utf-8 -*-
"""

Test relex snowball

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import io
import logging
import os
import unittest

from chemdataextractor.relex import Snowball, ChemicalRelationship, Relation, Entity
from chemdataextractor.model import BaseModel, StringType, ListType, ModelType, Compound
from chemdataextractor.parse.elements import I, R, Any, OneOrMore, Optional
from chemdataextractor.parse.common import lrb, rrb, delim
from chemdataextractor.parse.actions import join, merge
from chemdataextractor.parse.cem import chemical_name
from chemdataextractor.doc import Sentence


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# Create a new model
class CurieTemperature(BaseModel):
    specifier = StringType()
    value = StringType()
    units = StringType()

# Add to the available models
Compound.curie_temperatures = ListType(ModelType(CurieTemperature))


# Define a very basic entity tagger
specifier = (I('curie') + I('temperature') + Optional(lrb | delim) + Optional(R('^T(C|c)(urie)?')) + Optional(rrb) | R('^T(C|c)(urie)?'))('specifier').add_action(join)
units = (R('^[CFK]\.?$'))('units').add_action(merge)
value = (R('^\d+(\.\,\d+)?$'))('value')

# Let the entities be any combination of chemical names, specifier values and units
entities = (chemical_name | specifier | value + units)

# Now create a very generic parse phrase that will match any combination of these entities
curie_temperature_phrase = (entities + OneOrMore(entities | Any()))('curie_temperature')
curie_temp_entities = [chemical_name, specifier, value, units]

# Define the relationship and give it a name
curie_temp_relationship = ChemicalRelationship(curie_temp_entities, curie_temperature_phrase, name='curie_temperatures')


class TestSnowball(unittest.TestCase):

    maxDiff = None
    training_corpus = 'tests/data/relex/curie_training/'
    snowball_pkl = 'tests/data/relex/curie_temperatures.pkl'

    def test_load_snowball(self):
        sb = Snowball.load(self.snowball_pkl)
        self.assertIsInstance(sb, Snowball)
    
    def test_extract(self):
        curie_temp_snowball = Snowball.load(self.snowball_pkl)
        curie_temp_snowball.save_file_name = 'curie_test_output'
        test_sentence = Sentence('BiFeO3 is ferromagnetic with a curie temperature of 1103 K and this is very interesting')
        result = curie_temp_snowball.extract(test_sentence)
        self.assertEqual(len(result), 1)
        expected_entities = [Entity('BiFeO3', chemical_name, 0, 1), Entity('curie temperature', specifier, 0,0), Entity('1103', value, 0,0), Entity('K', units, 0,0)]
        expected_relation = Relation(expected_entities, confidence=1.0)
        self.assertEqual(result[0], expected_relation)
        self.assertEqual(result[0].confidence, expected_relation.confidence)


if __name__ == '__main__':
    unittest.main()
