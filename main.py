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
curie_temp_relationship = ChemicalRelationship(curie_temp_entities, curie_temperature_phrase)


def KnuthMorrisPratt(text, pattern):

    '''Yields all starting positions of copies of the pattern in the text.
Calling conventions are similar to string.find, but its arguments can be
lists or iterators, not just strings, it returns all matches, not just
the first one, and it does not need the whole text in memory at once.
Whenever it yields, it will have read the text exactly up to and including
the match that caused the yield.'''

    # allow indexing into pattern and protect against change during yield
    pattern = list(pattern)

    # build table of shift amounts
    shifts = [1] * (len(pattern) + 1)
    shift = 1
    for pos in range(len(pattern)):
        while shift <= pos and pattern[pos] != pattern[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # do the actual search
    startPos = 0
    matchLen = 0
    for c in text:
        while matchLen == len(pattern) or \
              matchLen >= 0 and pattern[matchLen] != c:
            startPos += shifts[matchLen]
            matchLen -= shifts[matchLen]
        matchLen += 1
        if matchLen == len(pattern):
            yield startPos

if __name__ == '__main__':
    curie_temp_snowball = Snowball(curie_temp_relationship)
    curie_temp_snowball.train(corpus='//Users/cj/Desktop/Work/Cambridge/Project/magnetic_materials_discovery/case_studies_paper/data/papers/')

    # test = ['curie', 'temperature']
    # text = ['this', 'is', 'a', 'curie', 'temperature', 'test']

    # for s in KnuthMorrisPratt(text, test):
    #     print(s)

    # Test sentence
    # s = Sentence('that MnO and NiO have curie temperature Tc of 100 and 300 K respectively')
    # records = curie_temp_snowball.extract(s)