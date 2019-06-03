"""Crystal Structure parameters models

- Crystal System : Hexagonal etc
- Space Group
- Cell parameters (a,b,c, alpha, )
- Volume
- R factors (Rwp, Rp)
- Density
-Formula Weight
"""
from chemdataextractor.model.base import BaseModel, StringType, ModelType
from chemdataextractor.parse.elements import I, R, W, Optional, OneOrMore, ZeroOrMore
from chemdataextractor.parse.actions import join
from chemdataextractor.model.units.quantity_model import DimensionlessModel

crystal

class CrystalSystem(DimensionlessModel):
    specifier = StringType(parse_expression=(I('Crystal') + I('system')).add_action(join), required=False)
    


class CrystalStructure(BaseModel):
