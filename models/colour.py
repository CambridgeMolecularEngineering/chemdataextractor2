"""
Colour model
"""

from chemdataextractor.model.base import (BaseModel, FloatType, ListType,
                                          ModelType, StringType)
from chemdataextractor.model.model import Compound
from chemdataextractor.parse.actions import join
from chemdataextractor.parse.auto import AutoTableParser
from chemdataextractor.parse.elements import (Any, I, OneOrMore, Optional, R,
                                              T, W, ZeroOrMore)

colours = (
    R('^[Bb]lack(-)?(ish)?$') |
    R('^[Ww]hite(-)?(ish)?$') |
    R('^[Rr]ed(-)?(dish)?$') |
    R('^[Gg]reen(-)?(ish)?$') |
    R('^[Bb]lue(-)?(ish)?$') |
    R('^[Yy]ellow(-)?(ish)?$') |
    R('^[Bb]rown(-)?(ish)?$') |
    R('^[Cc]olo(u)?rless$') |
    R('^[Pp]ink(-)?(ish)?$') |
    R('^[Oo]range(-)?(ish)?$') |
    R('^[Cc]yan$') |
    R('^[Vv]iolet$') |
    R('^[Gg]old(-)?(ish)?(en)?$') |
    R('^[Ss]ilver(-)?(ish)?$') |
    R('^[Mm]etallic$') |
    R('^[Gg]r[ae]y(-)?(ish)?$') |
    R('^[Pp]urple(-)?(ish)?$') |
    R('^[Mm]aroon(-)?(ish)?$') |
    R('^[Aa]quamarine$') |
    R('^[Cc]rimson$') |
    R('^[Kk]haki$') |
    R('^[Ii]ndigo$') |
    R('^[Oo]live$') |
    R('^[Ss]now(-)?(ish)?$')
)

prefix = (
    R('^[Dd]ark(-)?(ish)?$') |
    R('^[Dd]eep$') |
    R('^[Dd]im$') |
    R('^[Hh]ot$') |
    R('^[Ll]ight(-)?(ish)?$') |
    R('^[Mm]edium$') |
    R('^[Mm]idnight$') |
    R('^[Pp]ale$') |
    R('^[Ss]ky$')
)

colour_expression = (Optional(prefix) + colours + Optional(colours)).add_action(join)

class Colour(BaseModel):
    specifier = StringType(parse_expression=R('^[Cc]olo(u)?r$'), required=True)
    name = StringType(parse_expression=colour_expression, required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]
