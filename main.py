from chemdataextractor.relex import Snowball, ChemicalRelationship

from chemdataextractor.model import BaseModel, StringType, ListType, ModelType, Compound
import re
from chemdataextractor.parse import R, I, W, Optional, merge, join, OneOrMore, Any, ZeroOrMore, Start
from chemdataextractor.parse.cem import chemical_name, chemical_label
from chemdataextractor.parse.base import BaseParser
from chemdataextractor.parse.common import lrb, rrb, delim
from chemdataextractor.utils import first
from chemdataextractor.doc import Paragraph, Heading, Sentence
from lxml import etree

class CurieTemperature(BaseModel):
    specifier = StringType()
    value = StringType()
    units = StringType()

Compound.curie_temperatures = ListType(ModelType(CurieTemperature))

curie_words = I('curie') + I('temperature')
curie_symbols = Optional(lrb | delim) + R('^T(C|c)(urie)?') + Optional(rrb)
curie_combined = ((curie_words + curie_symbols).add_action(join) | (curie_symbols + curie_words).add_action(join))
specifier = (curie_combined | curie_words | curie_symbols)('specifier').add_action(join)
units = (R('^[CFK]\.?$'))('units').add_action(merge)
value = (R('^\d+(\.\,\d+)?$'))('value')

entities = (chemical_name | specifier | value + units)
curie_temperature_phrase = (entities + OneOrMore(entities | Any()))('curie_temperature')

curie_temp_entities = [chemical_name, specifier, value, units]
curie_temp_relationship = ChemicalRelationship(curie_temp_entities, curie_temperature_phrase, name='curie_temperatures')


if __name__ == '__main__':
    curie_temp_snowball = Snowball(curie_temp_relationship)
    curie_temp_snowball.train(corpus='tests/data/relex/curie_training_set/')

    # Once trained, extract from a new sentence
    # curie_temp_snowball = Snowball.load('chemdataextractor/relex/data/curie.pkl')
    # curie_temp_snowball.model = CurieTemperature
    curie_temp_snowball.save_file_name = 'curie_2'
    test_sentence = Sentence('BiFeO3 is ferromagnetic with a curie temperature of 1103 K and')
    rels = curie_temp_snowball.extract(test_sentence)

    # print("found:", rels)
    # # or get CDE records using a specific model
    # cde_records = curie_temp_snowball.records(test_sentence)
