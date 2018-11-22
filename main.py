from chemdataextractor.relex import Snowball, ChemicalRelationship

from chemdataextractor.model import BaseModel, StringType, ListType, ModelType, Compound
import re
from chemdataextractor.parse import R, I, W, Optional, merge, join, OneOrMore, Any, ZeroOrMore
from chemdataextractor.parse.cem import cem, chemical_label
from chemdataextractor.parse.base import BaseParser
from chemdataextractor.utils import first
from chemdataextractor.doc import Paragraph, Heading
from lxml import etree

class CurieTemperature(BaseModel):
    specifier = StringType()
    value = StringType()
    units = StringType()

Compound.curie_temperatures = ListType(ModelType(CurieTemperature))


specifier = ((I('Curie') + I('temperature')) | R('^T(C|c)(urie)?'))('specifier').add_action(join)
units = (R('^[CFK]\.?$'))('units').add_action(merge)
value = (R('^\d+(\.\,\d+)?$'))('value')
entities = (cem |chemical_label('label') | specifier | value + units)

curie_temperature_phrase = (entities + OneOrMore(entities | Any()))('curie_temperature')

curie_temp_entities = ['label', 'specifier', 'value', 'units']
curie_temp_relationship = ChemicalRelationship(curie_temp_entities, curie_temperature_phrase)

if __name__ == '__main__':
    curie_temp_snowball = Snowball(curie_temp_relationship)
    test_sentence = 'For instance, for 3a the Curie temperature (Tc) has been increased from 313 K (H phase) to 360 K (ZB phase). '
    curie_temp_snowball.parse_string(test_sentence)
    #curie_temp_snowball.train(corpus='/home/edward/Documents/snowball/training_set/tiny_set/')


