"""Crystal Structure parameters models

- Crystal System : Hexagonal etc
- Space Group
- Cell parameters (a,b,c)
- Volume
- R factors (Rwp, Rp)
- Density
- Formula Weight
"""

from chemdataextractor.model.base import BaseModel, StringType, ModelType, ListType, FloatType
from chemdataextractor.parse.elements import I, R, W, T, Optional, OneOrMore, ZeroOrMore, Any
from chemdataextractor.parse.actions import join
from chemdataextractor.model.units.quantity_model import DimensionlessModel, QuantityModel
from chemdataextractor.model.categories import CategoryModel
from chemdataextractor.model.model import Compound
from chemdataextractor.parse.template import QuantityModelTemplateParser
from chemdataextractor.parse.auto import AutoTableParser
from chemdataextractor.model.units.length import LengthModel, Length
from chemdataextractor.model.units.temperature import TemperatureModel
from chemdataextractor.model.units.mass import Mass
from chemdataextractor.model.units.substance_amount import AmountOfSubstance
from chemdataextractor.model.units.angle import AngleModel
from chemdataextractor.parse.common import lbrct, rbrct
from .colour import Colour


class FormulaWeight(QuantityModel):
    dimensions = Mass() / AmountOfSubstance()
    specifier = StringType(parse_expression=((I('formula') | I('molecular')) + I('weight')).add_action(join), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class AppliedTemperature(TemperatureModel):
    specifier = StringType(parse_expression=((I('Temperature') | R('^T$')).add_action(join)), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class Density(QuantityModel):
    dimensions = Mass() / Length()**3
    specifier = StringType(parse_expression=(R('ρ[Cc]?(alc)?(d)?') | I('density') | R('D(x)?')).add_action(join), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class Z(DimensionlessModel):
    specifier = StringType(parse_expression=R('Z'), required=True, contextual=False)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


space_groups = (R('^[PIFABCR](\d|\d̄)+$') + Optional((T('SYM') | W('/')) + R('[a-zA-Z]+'))).add_action(join)


class SpaceGroup(CategoryModel):
    specifier = StringType(parse_expression=(I('space') + I('group')).add_action(join), required=True)
    category = StringType(parse_expression=space_groups, required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, contextual=True)
    parsers = [AutoTableParser()]


class CellLengthA(LengthModel):
    specifier = StringType(parse_expression=R('^a$'),  required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class CellLengthB(LengthModel):
    specifier = StringType(parse_expression=R('b$'),  required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class CellLengthC(LengthModel):
    specifier = StringType(parse_expression=R('^c$'),  required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class CellAngleAlpha(AngleModel):
    specifier = StringType(parse_expression=R('^[αα⍺𝛂𝛼𝜶𝝰𝞪]$'), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class CellAngleBeta(AngleModel):
    specifier = StringType(parse_expression=R('^[βᵝᵦꞵ𝛃𝛽𝜷𝝱𝞫]$'), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class CellAngleGamma(AngleModel):
    specifier = StringType(parse_expression=R('^[γᵞᵧƔɣˠɤℽ𝛄𝛾𝜸𝝲𝞬]$'), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class CellVolume(QuantityModel):
    dimensions = Length()**3
    specifier = StringType(parse_expression=(Optional(I('cell')) + (I('Volume') | W('V'))).add_action(join),  required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class RFactor(DimensionlessModel):
    specifier = StringType(parse_expression=(R('^w?R([12]|(int))$')), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class Wavelength(LengthModel):
    specifier = StringType(parse_expression=(R('^Wavelength') | R('[λⲗ𝛌𝜆𝝀𝝺𝞴]')).add_action(join), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


class AbsorptionCoefficient(QuantityModel):
    dimensions = Length()**(-1)
    specifier = StringType(parse_expression=((R('[Aa]bsorption') + I('coefficient')) | R('[μµ𝛍𝜇𝝁𝝻𝞵]')).add_action(join), required=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]


crystal_systems = (R('[Tt]riclinic') | R('[Mm]onoclinic') |  R('[Oo]rthorhombic') | R('[Tt]etragonal') | R('[Hh]exagonal') | R('[Tt]rigonal') | R('[Cc]ubic'))


class CrystalCell(CategoryModel):
    specifier = StringType(parse_expression=((I('Crystal') + I('system')) | (I('Symmetry'))).add_action(join), required=True)
    category = StringType(parse_expression=crystal_systems, required=True, contextual=False, updatable=False)
    space_group = ModelType(SpaceGroup, required=True, contextual=True)
    z = ModelType(Z, required=False, contextual=True)
    density = ModelType(Density, required=False, contextual=True)
    r_factors = ModelType(RFactor, required=False, contextual=True)
    lattice_param_c = ModelType(CellLengthC, required=False, contextual=True)
    lattice_param_b = ModelType(CellLengthB, required=False, contextual=True)
    lattice_param_a = ModelType(CellLengthA, required=False, contextual=True)
    lattice_param_alpha = ModelType(CellAngleAlpha, required=False, contextual=True)
    lattice_param_beta = ModelType(CellAngleBeta, required=False, contextual=True)
    lattice_param_gamma = ModelType(CellAngleGamma, required=False, contextual=True)
    applied_temperature = ModelType(AppliedTemperature, required=False, contextual=True)
    cell_volume = ModelType(CellVolume, required=False, contextual=True)
    formula_weight = ModelType(FormulaWeight, required=False, contextual=True)
    wavelength = ModelType(Wavelength, required=False, contextual=True)
    colour = ModelType(Colour, required=False, contextual=True)
    absorption_coefficient = ModelType(AbsorptionCoefficient, required=False, contextual=True)
    compound = ModelType(Compound)
    parsers = [AutoTableParser()]





