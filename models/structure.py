"""Crystal Model"""

from chemdataextractor.model.base import BaseModel, StringType, ModelType
from chemdataextractor.parse.elements import I, R, W, T, Optional
from chemdataextractor.parse.actions import join
from chemdataextractor.model.units.quantity_model import DimensionlessModel, QuantityModel
from chemdataextractor.model.model import Compound
from chemdataextractor.model.units.length import LengthModel, Length
from chemdataextractor.model.units.temperature import TemperatureModel
from chemdataextractor.model.units.mass import Mass
from chemdataextractor.model.units.substance_amount import AmountOfSubstance
from chemdataextractor.model.units.angle import AngleModel
from chemdataextractor.parse.auto import AutoTableParser
from .colour import Colour


class FormulaWeight(QuantityModel):
    dimensions = Mass() / AmountOfSubstance()
    specifier = StringType(parse_expression=(((I('Formula') | I('molecular')) + (I('weight') | I('mass'))) | (R('^Mr?$')) | (W('Mass')) | (I('FW')) | (I('MW'))).add_action(join), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class FormulaWeightNoDim(DimensionlessModel):
    specifier = StringType(parse_expression=(((I('Formula') | I('molecular')) + (I('weight') | I('mass'))) | (R('^Mr?$')) | (W('Mass')) | (I('FW')) | (I('MW'))).add_action(join), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class AppliedTemperature(TemperatureModel):
    specifier = StringType(parse_expression=((I('Temperature') | R('^T$')).add_action(join)), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class Density(QuantityModel):
    dimensions = Mass() / Length()**3
    specifier = StringType(parse_expression=(R('[ρD][Cc]?(alc)?(d)?') | I('density') | R('D(x)?')).add_action(join), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class Z(DimensionlessModel):
    specifier = StringType(parse_expression=R('^Z$'), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


space_groups = ((R('^[PIFABCR]([mcanbed]+)?(\d|\d̄|\d-|-\d)*([mcanbed]+)?(\d|\d̄|\d-|-\d)*$') +
                 Optional(R('^([mcanbed]+)?(\d|\d̄|\d-|-\d)*([mcanbed]+)?(\d|\d̄|\d-|-\d)*$')) +
                 Optional((T('SYM') | W('/')) + R('[a-zA-Z]+'))) | (R('^\d{1,3}$'))).add_action(join)


class SpaceGroup(BaseModel):
    specifier = StringType(parse_expression=(I('space') + I('group')).add_action(join), required=True)
    symbol = StringType(parse_expression=space_groups, required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class CellLengthA(LengthModel):
    specifier = StringType(parse_expression=R('^a$'),  required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class CellLengthB(LengthModel):
    specifier = StringType(parse_expression=R('b$'),  required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class CellLengthC(LengthModel):
    specifier = StringType(parse_expression=R('^c$'),  required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class CellAngleAlpha(AngleModel):
    specifier = StringType(parse_expression=R('^[αα⍺𝛂𝛼𝜶𝝰𝞪]$'), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class CellAngleBeta(AngleModel):
    specifier = StringType(parse_expression=R('^[βᵝᵦꞵ𝛃𝛽𝜷𝝱𝞫]$'), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class CellAngleGamma(AngleModel):
    specifier = StringType(parse_expression=R('^[γᵞᵧƔɣˠɤℽ𝛄𝛾𝜸𝝲𝞬ν]$'), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class CellVolume(QuantityModel):
    dimensions = Length()**3
    specifier = StringType(parse_expression=(Optional(I('cell')) + (I('Volume') | W('V') | W('U'))).add_action(join),  required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class Wavelength(LengthModel):
    specifier = StringType(parse_expression=(R('^Wavelength') | R('^Radiation') | R('[λⲗ𝛌𝜆𝝀𝝺𝞴]')).add_action(join), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class F(DimensionlessModel):
    specifier = StringType(parse_expression=R('^F\(?000\)?$'), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


class AbsorptionCoefficient(QuantityModel):
    dimensions = Length()**(-1)
    specifier = StringType(parse_expression=((R('[Aa]bsorption') + I('coefficient')) | R('[μµ𝛍𝜇𝝁𝝻𝞵]')).add_action(join), required=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [AutoTableParser()]


crystal_systems = (R('[Tt]riclinic') |
                   R('[Mm]onoclinic') |
                   R('[Oo]rthorhombic') |
                   R('[Tt]etragonal') |
                   R('[Hh]exagonal') |
                   R('[Tt]rigonal') |
                   R('[Cc]ubic') |
                   R('[Rr]hombohedral'))


class UnitCell(BaseModel):
    specifier = StringType(parse_expression=((I('Crystal') + I('system')) | (I('Symmetry'))).add_action(join), required=True)
    system = StringType(parse_expression=crystal_systems, required=True)

    space_group = ModelType(SpaceGroup, contextual=True)
    lattice_param_c = ModelType(CellLengthC, contextual=True)
    lattice_param_b = ModelType(CellLengthB, contextual=True)
    lattice_param_a = ModelType(CellLengthA, contextual=True)
    lattice_param_alpha = ModelType(CellAngleAlpha, contextual=True)
    lattice_param_beta = ModelType(CellAngleBeta, contextual=True)
    lattice_param_gamma = ModelType(CellAngleGamma, contextual=True)
    cell_volume = ModelType(CellVolume, contextual=True)

    compound = ModelType(Compound, required=True, contextual=True, binding=True)
    parsers = [AutoTableParser()]


class DiffractionParams(BaseModel):
    specifier = StringType(parse_expression=((I('Crystal') + I('system')) | (I('Symmetry'))).add_action(join), required=True)

    z = ModelType(Z, contextual=True)
    structure_factor = ModelType(F, contextual=True)
    applied_temperature = ModelType(AppliedTemperature, contextual=True)
    wavelength = ModelType(Wavelength, contextual=True)
    absorption_coefficient = ModelType(AbsorptionCoefficient, contextual=True)

    compound = ModelType(Compound, required=True, contextual=True, binding=True)
    parsers = [AutoTableParser()]


class Crystal(BaseModel):
    specifier = StringType(parse_expression=((I('Crystal') + I('system')) | (I('Symmetry'))).add_action(join), required=True)
    system = StringType(parse_expression=crystal_systems, required=True)

    formula_weight = ModelType(FormulaWeight, contextual=True)
    formula_weight_no_dim = ModelType(FormulaWeightNoDim, contextual=True)
    density = ModelType(Density, contextual=True)
    colour = ModelType(Colour, contextual=True)

    cell_params = ModelType(UnitCell, contextual=True)
    diffraction_params = ModelType(DiffractionParams, contextual=True)

    compound = ModelType(Compound, required=True, contextual=True, binding=True)
    parsers = [AutoTableParser()]



