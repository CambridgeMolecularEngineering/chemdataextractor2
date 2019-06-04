"""Crystal Structure parameters models

- Crystal System : Hexagonal etc
- Space Group
- Cell parameters (a,b,c, alpha, )
- Volume
- R factors (Rwp, Rp)
- Density
- Formula Weight
"""
from chemdataextractor.model.base import BaseModel, StringType, ModelType, ListType
from chemdataextractor.parse.elements import I, R, W, T, Optional, OneOrMore, ZeroOrMore, Any
from chemdataextractor.parse.actions import join
from chemdataextractor.model.units.quantity_model import DimensionlessModel, QuantityModel
from chemdataextractor.model.categories import CategoryModel
from chemdataextractor.model.model import Compound
from chemdataextractor.parse.template import QuantityModelTemplateParser
from chemdataextractor.parse.auto import AutoTableParser
from chemdataextractor.model.units.length import LengthModel, Length
from chemdataextractor.model.units.mass import Mass
from chemdataextractor.parse.common import lbrct, rbrct

class Density(QuantityModel):
    dimensions = Mass() / Length()**3
    specifier = StringType(parse_expression=(R('ρ[Cc]?') | I('density')), required=True)
    compound = ModelType(Compound)

class Z(DimensionlessModel):
    specifier = StringType(parse_expression=W('Z'), required=True)
    compound = ModelType(Compound)

space_groups = (R('^[PIFABCR]\d+') + Optional(T('SYM') | W('/')) + R('[a-zA-Z]')).add_action(join)
class SpaceGroup(CategoryModel):
    specifier = StringType(parse_expression=(I('space') + I('group')).add_action(join), required=True)
    category = StringType(parse_expression=space_groups, required=True, contextual=False, updatable=False)
    compound = ModelType(Compound)
    parser = [AutoTableParser()]

class LatticeA(LengthModel):
    specifier = StringType(parse_expression=I('a'),  required=True)
    compound = ModelType(Compound)
    parser = [QuantityModelTemplateParser(), AutoTableParser()]

class RFactor(DimensionlessModel):
    specifier = StringType(parse_expression=(R('^w?R([12]|(int))')), required=True)
    compound = ModelType(Compound)

crystal_systems = (R('[Tt]riclinic') | R('[Mm]onoclinic') |  R('[Oo]rthorhombic') | R('[Tt]etragonal') | R('[Hh]exagonal') | R('[Tt]rigonal') | R('[Cc]ubic'))
class CrystalSystem(CategoryModel):
    specifier = StringType(parse_expression=(I('Crystal') + I('system')).add_action(join), required=True)
    category = StringType(parse_expression=crystal_systems, required=True, contextual=False, updatable=False)
    space_group = ModelType(SpaceGroup, required=True, contextual=True)
    z = ModelType(Z, required=True, contextual=True)
    density = ModelType(Density, required=True, contextual=True)
    r_factors = ModelType(RFactor, required=True, contextual=True)
    compound = ModelType(Compound)
    parsers = [QuantityModelTemplateParser(), AutoTableParser()]
