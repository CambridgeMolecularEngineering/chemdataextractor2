"""
Model classes for physical properties.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import six

from .base import BaseModel, StringType, ListType, ModelType
from .units.temperature import TemperatureModel
from .units.length import LengthModel
from ..parse.cem import CompoundParser, CompoundHeadingParser, ChemicalLabelParser, names_only, labels_only, roles_only
from ..parse.ir import IrParser
from ..parse.mp_new import MpParser
from ..parse.nmr import NmrParser
from ..parse.tg import TgParser
from ..parse.uvvis import UvvisParser
from ..parse.elements import R, I, Optional, W
from ..parse.actions import merge
from ..model.units.quantity_model import QuantityModel, DimensionlessModel
from ..parse.auto import AutoTableParser, AutoSentenceParser
from ..parse.apparatus import ApparatusParser

log = logging.getLogger(__name__)


class Compound(BaseModel):
    names = ListType(StringType(), parse_expression=names_only)
    labels = ListType(StringType(), parse_expression=labels_only)
    roles = ListType(StringType(), parse_expression=roles_only)
    parsers = [CompoundParser(), CompoundHeadingParser(), ChemicalLabelParser()]

    def merge(self, other):
        """Merge data from another Compound into this Compound."""
        log.debug('Merging: %s and %s' % (self.serialize(), other.serialize()))
        for k in self.keys():
            for new_item in other[k]:
                if new_item not in self[k]:
                    self[k].append(new_item)
        log.debug('Result: %s' % self.serialize())
        return self

    # def merge_contextual(self, other):
    #     """Merge in contextual info from a template Compound."""
    #     # TODO: This is currently dependent on our data model? Make more robust to schema changes
    #     # Currently we assume all lists at Compound level, with 1 further potential nested level of lists
    #     for k in self.keys():
    #         # print('key: %s' % k)
    #         for item in self[k]:
    #             # print('item: %s' % item)
    #             for other_item in other.get(k, []):
    #                 # Skip text properties (don't merge names, labels, roles)
    #                 if isinstance(other_item, six.text_type):
    #                     continue
    #                 for otherk in other_item.keys():
    #                     if isinstance(other_item[otherk], list):
    #                         if len(other_item[otherk]) > 0 and len(item[otherk]) > 0:
    #                             other_nested_item = other_item[otherk][0]
    #                             for othernestedk in other_nested_item.keys():
    #                                 for nested_item in item[otherk]:
    #                                     if not nested_item[othernestedk]:
    #                                         nested_item[othernestedk] = other_nested_item[othernestedk]
    #                     elif not item[otherk]:
    #                         item[otherk] = other_item[otherk]
    #     log.debug('Result: %s' % self.serialize())
    #     return self

    @property
    def is_unidentified(self):
        if not self.names and not self.labels:
            return True
        return False

    # @property
    # def is_contextual(self):
    #     for k in self:
    #         # Not contextual if we have any names or labels
    #         if k in {'names', 'labels'}:
    #             return False
    #     return super(Compound, self).is_contextual

    @property
    def is_id_only(self):
        """Return True if identifier information only."""
        for key, value in self.items():
            if key not in {'names', 'labels', 'roles'} and value:
                return False
        if self.names or self.labels:
            return True
        return False


class Apparatus(BaseModel):
    name = StringType()
    parsers = [ApparatusParser()]


class UvvisPeak(BaseModel):
    #: Peak value, i.e. wavelength
    value = StringType()
    #: Peak value units
    units = StringType(contextual=True)
    # Extinction value
    extinction = StringType()
    # Extinction units
    extinction_units = StringType(contextual=True)
    # Peak shape information (e.g. shoulder, broad)
    shape = StringType()


class UvvisSpectrum(BaseModel):
    solvent = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(UvvisPeak))
    compound = ModelType(Compound)
    parsers = [UvvisParser()]


class IrPeak(BaseModel):
    value = StringType()
    units = StringType(contextual=True)
    strength = StringType()
    bond = StringType()


class IrSpectrum(BaseModel):
    solvent = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(IrPeak))
    compound = ModelType(Compound)
    parsers = [IrParser()]


class NmrPeak(BaseModel):
    shift = StringType()
    intensity = StringType()
    multiplicity = StringType()
    coupling = StringType()
    coupling_units = StringType(contextual=True)
    number = StringType()
    assignment = StringType()


class NmrSpectrum(BaseModel):
    nucleus = StringType(contextual=True)
    solvent = StringType(contextual=True)
    frequency = StringType(contextual=True)
    frequency_units = StringType(contextual=True)
    standard = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(NmrPeak))
    compound = ModelType(Compound)
    parsers = [NmrParser()]

# class MeltingPoint(BaseModel):
#     """A melting point measurement."""
#     value = StringType()
#     units = StringType(contextual=True)
#     solvent = StringType(contextual=True)
#     concentration = StringType(contextual=True)
#     concentration_units = StringType(contextual=True)
#     apparatus = StringType(contextual=True)


class MeltingPoint(TemperatureModel):
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    compound = ModelType(Compound, contextual=True)
    parsers = [MpParser()]


class GlassTransition(BaseModel):
    """A glass transition temperature."""
    value = StringType()
    units = StringType(contextual=True)
    method = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    compound = ModelType(Compound)
    parsers = [TgParser()]


class QuantumYield(BaseModel):
    """A quantum yield measurement."""
    value = StringType()
    units = StringType(contextual=True)
    solvent = StringType(contextual=True)
    type = StringType(contextual=True)
    standard = StringType(contextual=True)
    standard_value = StringType(contextual=True)
    standard_solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class FluorescenceLifetime(BaseModel):
    """A fluorescence lifetime measurement."""
    value = StringType()
    units = StringType(contextual=True)
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class ElectrochemicalPotential(BaseModel):
    """An oxidation or reduction potential, from cyclic voltammetry."""
    value = StringType()
    units = StringType(contextual=True)
    type = StringType(contextual=True)
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


# TEST MODELS

class NeelTemperature(TemperatureModel):
    # expression = (I('T')+I('N')).add_action(merge)
    expression = I('TN')
    # specifier = I('TN')
    # specifier = MutableAttribute(I('TN'))
    specifier = StringType(parse_expression=expression, required=True, contextual=False, mutable=False)
    compound = ModelType(Compound, required=False, contextual=False)


class CurieTemperature(TemperatureModel):
    # expression = (I('T') + I('C')).add_action(merge)
    expression = I('TC')
    specifier = StringType(parse_expression=expression, required=True, contextual=False, mutable=False)
    compound = ModelType(Compound, required=False, contextual=False)


class InteratomicDistance(LengthModel):
    specifier_expression = (R('^bond$') + R('^distance')).add_action(merge)
    specifier = StringType(parse_expression=specifier_expression, required=False, contextual=True)
    rij_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    species = StringType(parse_expression=rij_label, required=True, contextual=False)
    compound = ModelType(Compound, required=True, contextual=True)
    another_label = StringType(parse_expression=R('^adgahg$'), required=False, contextual=False)


class CoordinationNumber(DimensionlessModel):
    # something like NTi-O will not work with this, only work if there is space between the label and specifier
    coordination_number_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    # specifier = (R('^(N|n|k)$') | (I('Pair') + I('ij')).add_action(merge)
    specifier_expression = R('^(N|n|k)$')
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=True)

    cn_label = StringType(parse_expression=coordination_number_label, required=True, contextual=True)
    compound = ModelType(Compound, required=True, contextual=True)


class CNLabel(BaseModel):
    # separate model to test automated parsing for stuff that are not quantities
    coordination_number_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    specifier = (I('Pair') + I('ij')).add_action(merge)
    label_Juraj = StringType(parse_expression=coordination_number_label)
    compound = ModelType(Compound, required=False)
    parsers = [AutoSentenceParser(), AutoTableParser()]

