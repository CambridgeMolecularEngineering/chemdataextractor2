# -*- coding: utf-8 -*-
"""


"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re
from lxml.builder import E
from lxml import etree

from .common import delim
from ..utils import first, SplitString
from ..model import Compound, UvvisSpectrum, UvvisPeak, QuantumYield, FluorescenceLifetime, MeltingPoint, GlassTransition, CoordinationNumber
from ..model import ElectrochemicalPotential, IrSpectrum, IrPeak
from .actions import join, merge, fix_whitespace
from .base import BaseParser
from .cem import chemical_label, label_before_name, chemical_name, chemical_label_phrase, solvent_name, lenient_chemical_label, cem
from .elements import R, I, W, Optional, ZeroOrMore, And, Any, OneOrMore, Start, End, Group, Not, PreviousToken

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


delims = ZeroOrMore(delim)
minus = R('^[\-–−‒]$')


name_blacklist = R('^([\d\.]+)$')

#: Compound identifier column heading
compound_heading = R('(^|\b)(comp((oun)?d)?|molecule|ligand|oligomer|complex|dye|porphyrin|substance|sample|material|catalyst|acronym|isomer|(co)?polymer|chromophore|species|quinone|ether|diene|adduct|acid|radical|monomer|amine|analyte|product|system|(photo)?sensitiser|phthalocyanine|MPc)(e?s)?($|\b)', re.I)
solvent_heading = R('(^|\b)(solvent)s?($|\b)', re.I)
solvent_in_heading = Group(solvent_name)('cem')
solvent_cell = Group(solvent_name | chemical_name)('cem')
compound_cell = Group(
    (Start() + chemical_label + End())('cem') |
    (Start() + lenient_chemical_label + End())('cem') |
    chemical_label_phrase('cem') |
    (Not(Start() + OneOrMore(name_blacklist) + End()) + OneOrMore(Any())('name').add_action(join).add_action(fix_whitespace) + Optional(W('(').hide() + chemical_label + W(')').hide()))('cem') |
    label_before_name
)('cem_phrase')


uvvis_emi_title = (
    I('emission') + R('max(ima)?') |
    W('λ') + Optional(I('max')) + Optional(W(',')) + R('em(i(ssion)?)?', re.I) |
    R('em(i(ssion)?)?', re.I) + W('λ') + Optional(I('max')) + Optional(W(','))
)
uvvis_abs_title = (
    I('absorption') + R('max(ima)?') |
    W('λ') + OneOrMore(R('^(a|sol)?max$', re.I) | R('abs(or[bp]tion)?', re.I) | I('a') | W(',')) |
    R('uv([-/]?vis)?', re.I)
)
extinction_title = Optional(R('^10\d$') | W('10') + minus + R('^\d$')).hide() + W('ε') + Optional(I('max'))
uvvis_units = (W('nm') | R('^eV[\-–−‒]1$') | W('eV') + minus + W('1'))('uvvis_units').add_action(merge)
multiplier = Optional(I('×')) + (R('^10–?[34]$') | (W('10') + minus + R('^[345]$')))

extinction_units = (
    (Optional(multiplier + delims) + (
        I('M') + minus + I('1') + I('cm') + minus + I('1') |
        I('M') + minus + I('1') + I('cm') + minus + I('1') |
        I('dm3') + I('mol') + minus + I('1') + I('cm') + minus + I('1') |
        I('l') + I('mol') + minus + I('1') + I('cm') + minus + I('1') |
        I('l') + I('cm') + minus + I('1') + I('mol') + minus + I('1')
    )) | multiplier
)('extinction_units').add_action(join)

ir_title = (
    R('^(FT-?)?IR$') + Optional(I('absorption'))
)
ir_units = Optional(W('/')).hide() + (
    R('^\[?cm[-–−]1\]?$') |
    W('cm') + R('^[-–−]$') + W('1')
)('ir_units').add_action(merge)
ir_heading = (OneOrMore(ir_title.hide()) + ZeroOrMore(delims.hide() + ir_units))('ir_heading')
ir_value = (R('^\d{3,5}(\.\d{1,2})?$'))('value')
peak_strength = R('^(sh(oulder)?|br(oad)?)$')('strength')
ir_peak = (
    ir_value + Optional(W('(').hide()) + Optional(peak_strength) + Optional(W(')').hide())
)('ir_peak')
ir_cell = (
    ir_peak + ZeroOrMore(W(',').hide() + ir_peak)
)('ir_cell')

# TODO: (photoluminescence|fluorescence) quantum yield
quantum_yield_title = (R('^(Φ|ϕ)(fl?|pl|ze|t|l|lum)?$', re.I) + Optional(R('^(fl?|pl|ze|t|l|lum)$', re.I)))('quantum_yield_type').add_action(merge)  #  + ZeroOrMore(Any())
quantum_yield_units = W('%')('quantum_yield_units')
quantum_yield_heading = Group(Start() + quantum_yield_title + delims.hide() + Optional(quantum_yield_units) + delims.hide() + End())('quantum_yield_heading')
quantum_yield_value = (Optional(R('^[~∼\<\>]$')) + ((W('10') + minus + R('^\d$')) | R('^(100(\.0+)?|\d\d?(\.\d+)?)$')) + Optional(W('±') + R('^\d+(\.\d+)?$')))('quantum_yield_value').add_action(merge)
quantum_yield_cell = (quantum_yield_value + Optional(quantum_yield_units))('quantum_yield_cell')


def split_uvvis_shape(tokens, start, result):
    """"""
    if result[0].text.endswith('sh') or result[0].text.endswith('br'):
        result.append(E('shape', result[0].text[-2:]))
        result[0].text = result[0].text[:-2]



uvvis_emi_heading = (OneOrMore(uvvis_emi_title.hide()))('uvvis_emi_heading')
uvvis_abs_heading = (OneOrMore(uvvis_abs_title.hide()) + ZeroOrMore(delims.hide() + (uvvis_units | extinction_title.hide() | extinction_units)))('uvvis_abs_heading')
uvvis_abs_disallowed = I('emission')
extinction_heading = (extinction_title.hide() + delims.hide() + Optional(extinction_units))('extinction_heading')
uvvis_value = (R('^\d{3,4}(\.\d{1,2})?(sh|br)?$'))('value').add_action(split_uvvis_shape)
peak_shape = R('^(sh(oulder)?|br(oad)?)$')('shape')
extinction_value = (
    R('^\d+\.\d+$') + Optional(W('±') + R('^\d+\.\d+$')) + Optional(W('×') + R('10\d+')) |  # Scientific notation
    R('^\d{1,3}$') + R('^\d\d\d$') |  # RSC often inserts spaces within values instead of commas
    R('^\d{1,2},?\d{3,3}$')

)('extinction').add_action(merge)


uvvis_abs_emi_quantum_yield_heading = (
    OneOrMore(uvvis_abs_title.hide()) +
    Optional(Optional(delims.hide()) + uvvis_units('uvvis_abs_units') + Optional(delims.hide())) +
    OneOrMore(uvvis_emi_title.hide()) +
    Optional(Optional(delims.hide()) + uvvis_units + Optional(delims.hide())) +
    Optional(delims.hide()) + quantum_yield_title.hide() + Optional(delims.hide()) +
    Optional(Optional(delims.hide()) + quantum_yield_units + Optional(delims.hide()))
)('uvvis_emi_quantum_yield_heading')

uvvis_abs_emi_quantum_yield_cell = (
    uvvis_value('uvvis_abs_value') + delims.hide() + uvvis_value + delims.hide() + quantum_yield_value + Optional(quantum_yield_units)
)('uvvis_emi_quantum_yield_cell')


uvvis_emi_quantum_yield_heading = (
    OneOrMore(uvvis_emi_title.hide()) +
    Optional(Optional(delims.hide()) + uvvis_units + Optional(delims.hide())) +
    Optional(delims.hide()) + quantum_yield_title.hide() + Optional(delims.hide()) +
    Optional(Optional(delims.hide()) + quantum_yield_units + Optional(delims.hide()))
)('uvvis_emi_quantum_yield_heading')

uvvis_emi_quantum_yield_cell = (
    uvvis_value + delims.hide() + quantum_yield_value + Optional(quantum_yield_units)
)('uvvis_emi_quantum_yield_cell')

uvvis_abs_peak = (
    uvvis_value + Optional(peak_shape) + Optional(W('(').hide() + extinction_value + W(')').hide())
)('uvvis_abs_peak')

uvvis_abs_cell = (
    uvvis_abs_peak + ZeroOrMore(W(',').hide() + uvvis_abs_peak)
)('uvvis_abs_cell')

extinction_cell = (
    extinction_value + ZeroOrMore(W(',').hide() + extinction_value)
)('uvvis_abs_cell')

uvvis_emi_peak = (
    uvvis_value + Optional(peak_shape)
)('uvvis_emi_peak')

uvvis_emi_cell = (
    uvvis_emi_peak + ZeroOrMore(W(',').hide() + uvvis_emi_peak)
)('uvvis_emi_cell')


fluorescence_lifetime_title = W('τ') + R('^(e|f|ave|avg|0)$', re.I)
fluorescence_lifetime_units = (W('ns') | W('μ') + W('s'))('fluorescence_lifetime_units').add_action(merge)
fluorescence_lifetime_heading = (fluorescence_lifetime_title.hide() + delims.hide() + Optional(fluorescence_lifetime_units))('fluorescence_lifetime_heading')
fluorescence_lifetime_value = (Optional(R('^[~∼\<\>]$')) + R('^\d+(\.\d+)?$'))('fluorescence_lifetime_value').add_action(merge)
fluorescence_lifetime_cell = (
    fluorescence_lifetime_value + ZeroOrMore(W(',').hide() + fluorescence_lifetime_value)
)('fluorescence_lifetime_cell')

electrochemical_potential_title = ((R('^E(ox|red)1?$', re.I) | W('E') + R('^(ox|red)1?$')) + Optional(W('/') + W('2')))('electrochemical_potential_type').add_action(merge)
electrochemical_potential_units = (W('V'))('electrochemical_potential_units').add_action(merge)
electrochemical_potential_heading = (electrochemical_potential_title + delims.hide() + Optional(electrochemical_potential_units))('electrochemical_potential_heading')
electrochemical_potential_value = (Optional(R('^[~∼\<\>]$')) + Optional(minus) + R('^\d+(\.\d+)?$'))('electrochemical_potential_value').add_action(merge)
electrochemical_potential_cell = (
    electrochemical_potential_value + ZeroOrMore(delims.hide() + electrochemical_potential_value)
)('electrochemical_potential_cell')

subject_phrase = ((I('of') | I('for')) + chemical_name)('subject_phrase')
solvent_phrase = (I('in') + (solvent_name | chemical_name))('solvent_phrase')

temp_range = (Optional(R('^[\-–−]$')) + (R('^[\+\-–−]?\d+(\.\d+)?[\-–−]\d+(\.\d+)?$') | (R('^[\+\-–−]?\d+(\.\d+)?$') + R('^[\-–−]$') + R('^[\+\-–−]?\d+(\.\d+)?$'))))('temperature').add_action(merge)
temp_value = (Optional(R('^[\-–−]$')) + R('^[\+\-–−]?\d+(\.\d+)?$') + Optional(W('±') + R('^\d+(\.\d+)?$')))('temperature').add_action(merge)
temp_word = (I('room') + R('^temp(erature)?$') | R('^r\.?t\.?$', re.I))('temperature').add_action(merge)
temp = (temp_range | temp_value | temp_word)('value')
temp_units = (W('°') + R('[CFK]') | W('K'))('units').add_action(merge)
temp_with_units = (temp + temp_units)('temp')
temp_with_optional_units = (temp + Optional(temp_units))('temp')

temp_phrase = (I('at') + temp_with_units)('temp_phrase')

melting_point_title = R('^T(melt|m\.p|m)$', re.I) | W('T') + R('^(melt|m\.p|m)?$')
melting_point_heading = (melting_point_title.hide() + delims.hide() + Optional(temp_units))('melting_point_heading')
melting_point_cell = (
    temp_with_optional_units + ZeroOrMore(delims.hide() + temp_with_optional_units)
)('melting_point_cell')

########################################################################################################################
# COORDINATION NUMBER RULES FOR TABLES
# jm2111
# ---------------------------------------------------------------------------------------------------------------------#
# will recognize the error first if present, if the error is not recognized/present
# it might recognize several coordination numbers in one cell (which micht be desired)
# different types of errors are preserved in the output: 8.2(2) and 8.4(±0.5)
coordination_number_error = (Optional(W('(')) + Optional(W('±')) + R('^[\d.]+$') + Optional(W(')')))('cn_error')
coordination_number = (R('^[\d.]+$') + Optional(coordination_number_error))('cn_value').add_action(merge)

element_symbols = R('^(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr){1,2}$')('elements')
coordination_number_label = (element_symbols + Optional(W('-').hide() + (element_symbols)))('cn_label').add_action(merge)

# if the label is merged with the title (Ex. 'NAsAs' or 'NAs-As') the whole token will be associated with the title and interpretation will be done in the parser
coordination_number_title_alt1 = R('^(N|n|k)\s?((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))?$')
coordination_number_title_alt2 = (R('^(N|n|k)(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)$') + Optional(W('-')) + Optional(element_symbols)).add_action(merge)
coordination_number_title = (coordination_number_title_alt1 | coordination_number_title_alt2)('cn_title')

coordination_number_heading = ((coordination_number_title) + Optional(W('-').hide()) + Optional(coordination_number_label))('coordination_number_heading')
coordination_number_cell = (coordination_number)('coordination_number_cell')

# if the labels are in separate cells:
# coordination_number_label_heading = R('^Label$')('cn_label_heading')
# coordination_number_label_cell = (coordination_number_label)('cn_label_cell')
#######################################################################################################################


glass_transition_title = R('^T(g\.)$', re.I) | W('T') + R('^(g\.)?$')
glass_transition_heading = (glass_transition_title.hide() + delims.hide() + Optional(temp_units))('glass_transition_heading')
glass_transition_cell = (
    temp_with_optional_units + ZeroOrMore(delims.hide() + temp_with_optional_units)
)('glass_transition_cell')

caption_context = Group(subject_phrase | solvent_phrase | temp_phrase)('caption_context')


class CompoundHeadingParser(BaseParser):
    """"""
    root = compound_heading

    def interpret(self, result, start, end):
        """"""
        yield Compound()


class SolventHeadingParser(BaseParser):
    """"""
    root = solvent_heading

    def interpret(self, result, start, end):
        """"""
        yield Compound()


class UvvisAbsDisallowedHeadingParser(BaseParser):
    """"""
    root = uvvis_abs_disallowed

    def interpret(self, result, start, end):
        """"""
        yield Compound()


class SolventInHeadingParser(BaseParser):
    """"""
    root = solvent_in_heading

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        solvent = first(result.xpath('./name/text()'))
        if solvent is not None:
            context = {'solvent': solvent}
            c.melting_points = [MeltingPoint(**context)]
            c.glass_transitions = [GlassTransition(**context)]
            c.quantum_yields = [QuantumYield(**context)]
            c.fluorescence_lifetimes = [FluorescenceLifetime(**context)]
            c.electrochemical_potentials = [ElectrochemicalPotential(**context)]
            c.uvvis_spectra = [UvvisSpectrum(**context)]
        if c.serialize():
            yield c


class TempInHeadingParser(BaseParser):
    """"""
    root = temp_with_units

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        context = {
            'temperature': first(result.xpath('./value/text()')),
            'temperature_units': first(result.xpath('./units/text()'))
        }
        c.quantum_yields = [QuantumYield(**context)]
        c.fluorescence_lifetimes = [FluorescenceLifetime(**context)]
        c.electrochemical_potentials = [ElectrochemicalPotential(**context)]
        c.uvvis_spectra = [UvvisSpectrum(**context)]
        yield c


class SolventCellParser(BaseParser):
    """"""
    root = solvent_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        solvent = first(result.xpath('./name/text()'))
        if solvent is not None:
            context = {'solvent': solvent}
            c.melting_points = [MeltingPoint(**context)]
            c.glass_transitions = [GlassTransition(**context)]
            c.quantum_yields = [QuantumYield(**context)]
            c.fluorescence_lifetimes = [FluorescenceLifetime(**context)]
            c.electrochemical_potentials = [ElectrochemicalPotential(**context)]
            c.uvvis_spectra = [UvvisSpectrum(**context)]
        if c.serialize():
            yield c


class CompoundCellParser(BaseParser):
    """"""
    root = compound_cell

    def interpret(self, result, start, end):
        for cem_el in result.xpath('./cem'):
            c = Compound(
                names=cem_el.xpath('./name/text()'),
                labels=cem_el.xpath('./label/text()')
            )
            yield c


class UvvisEmiHeadingParser(BaseParser):
    """"""
    root = uvvis_emi_heading

    def interpret(self, result, start, end):
        """"""
        uvvis_units = first(result.xpath('./uvvis_units/text()'))
        c = Compound()
        # TODO: Emission peaks
        yield c


class UvvisAbsHeadingParser(BaseParser):
    """"""
    root = uvvis_abs_heading

    def interpret(self, result, start, end):
        """"""
        uvvis_units = first(result.xpath('./uvvis_units/text()'))
        extinction_units = first(result.xpath('./extinction_units/text()'))
        c = Compound()
        if uvvis_units or extinction_units:
            c.uvvis_spectra.append(
                UvvisSpectrum(peaks=[UvvisPeak(units=uvvis_units, extinction_units=extinction_units)])
            )
        yield c


class ExtinctionHeadingParser(BaseParser):
    """"""
    root = extinction_heading

    def interpret(self, result, start, end):
        """"""
        extinction_units = first(result.xpath('./extinction_units/text()'))
        c = Compound()
        if extinction_units:
            c.uvvis_spectra.append(
                UvvisSpectrum(peaks=[UvvisPeak(extinction_units=extinction_units)])
            )
        yield c


class IrHeadingParser(BaseParser):
    """"""
    root = ir_heading

    def interpret(self, result, start, end):
        """"""
        ir_units = first(result.xpath('./ir_units/text()'))
        c = Compound()
        if ir_units:
            c.ir_spectra.append(
                IrSpectrum(peaks=[IrPeak(units=ir_units)])
            )
        yield c


class IrCellParser(BaseParser):
    """"""
    root = ir_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        ir = IrSpectrum()
        for peak in result.xpath('./ir_peak'):
            ir.peaks.append(
                IrPeak(
                    value=first(peak.xpath('./value/text()')),
                    strength=first(peak.xpath('./strength/text()'))
                )
            )
        if ir.peaks:
            c.ir_spectra.append(ir)
            yield c


class QuantumYieldHeadingParser(BaseParser):
    """"""
    root = quantum_yield_heading

    def interpret(self, result, start, end):
        """"""
        c = Compound(
            quantum_yields=[
                QuantumYield(
                    type=first(result.xpath('./quantum_yield_type/text()')),
                    units=first(result.xpath('./quantum_yield_units/text()'))
                )
            ]
        )
        yield c


class QuantumYieldCellParser(BaseParser):
    """"""
    root = quantum_yield_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        qy = QuantumYield(
            value=first(result.xpath('./quantum_yield_value/text()')),
            units=first(result.xpath('./quantum_yield_units/text()'))
        )
        if qy.value:
            c.quantum_yields.append(qy)
            yield c


class UvvisEmiCellParser(BaseParser):
    """"""
    root = uvvis_emi_cell

    def interpret(self, result, start, end):
        """"""
        # TODO: Emission peaks
        return
        yield


class UvvisAbsCellParser(BaseParser):
    """"""
    root = uvvis_abs_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        uvvis = UvvisSpectrum()
        for peak in result.xpath('./uvvis_abs_peak'):
            uvvis.peaks.append(
                UvvisPeak(
                    value=first(peak.xpath('./value/text()')),
                    extinction=first(peak.xpath('./extinction/text()')),
                    shape=first(peak.xpath('./shape/text()'))
                )
            )
        if uvvis.peaks:
            c.uvvis_spectra.append(uvvis)
            yield c


class ExtinctionCellParser(BaseParser):
    """"""
    root = extinction_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        uvvis = UvvisSpectrum()
        for value in result.xpath('./extinction/text()'):
            uvvis.peaks.append(
                UvvisPeak(
                    extinction=value,
                )
            )
        if uvvis.peaks:
            c.uvvis_spectra.append(uvvis)
            yield c


class UvvisAbsEmiQuantumYieldHeadingParser(BaseParser):
    """"""
    root = uvvis_abs_emi_quantum_yield_heading

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        abs_units = first(result.xpath('./uvvis_abs_units/text()'))
        if abs_units:
            c.uvvis_spectra.append(
                UvvisSpectrum(peaks=[UvvisPeak(units=abs_units)])
            )
        qy_units = first(result.xpath('./quantum_yield_units/text()'))
        if qy_units:
            c.quantum_yields.append(
                QuantumYield(units=qy_units)
            )

        yield c


class UvvisAbsEmiQuantumYieldCellParser(BaseParser):
    """"""
    root = uvvis_abs_emi_quantum_yield_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        uvvis = UvvisSpectrum()
        for value in result.xpath('./uvvis_abs_value/text()'):
            uvvis.peaks.append(
                UvvisPeak(
                    value=value,
                )
            )
        if uvvis.peaks:
            c.uvvis_spectra.append(uvvis)
        qy = QuantumYield(
            value=first(result.xpath('./quantum_yield_value/text()'))
        )
        if qy.value:
            c.quantum_yields.append(qy)

        if c.quantum_yields or c.uvvis_spectra:
            yield c


class UvvisEmiQuantumYieldHeadingParser(BaseParser):
    """"""
    root = uvvis_emi_quantum_yield_heading

    def interpret(self, result, start, end):
        """"""
        # Yield an empty compound to signal that the Parser matched
        yield Compound()


class UvvisEmiQuantumYieldCellParser(BaseParser):
    """"""
    root = uvvis_emi_quantum_yield_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        qy = QuantumYield(
            value=first(result.xpath('./quantum_yield_value/text()'))
        )
        if qy.value:
            c.quantum_yields.append(qy)
            yield c


class FluorescenceLifetimeHeadingParser(BaseParser):
    """"""
    root = fluorescence_lifetime_heading

    def interpret(self, result, start, end):
        """"""
        fluorescence_lifetime_units = first(result.xpath('./fluorescence_lifetime_units/text()'))
        c = Compound()
        if fluorescence_lifetime_units:
            c.fluorescence_lifetimes.append(
                FluorescenceLifetime(units=fluorescence_lifetime_units)
            )
        yield c


class FluorescenceLifetimeCellParser(BaseParser):
    """"""
    root = fluorescence_lifetime_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        fl = FluorescenceLifetime(
            value=first(result.xpath('./fluorescence_lifetime_value/text()'))
        )
        if fl.value:
            c.fluorescence_lifetimes.append(fl)
            yield c


class MeltingPointHeadingParser(BaseParser):
    """"""
    root = melting_point_heading

    def interpret(self, result, start, end):
        """"""
        melting_point_units = first(result.xpath('./units/text()'))
        c = Compound()
        if melting_point_units:
            c.melting_points.append(
                MeltingPoint(units=melting_point_units)
            )
        yield c


class MeltingPointCellParser(BaseParser):
    """"""
    root = melting_point_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        for mp in result.xpath('./temp'):
            c.melting_points.append(
                MeltingPoint(
                    value=first(mp.xpath('./value/text()')),
                    units=first(mp.xpath('./units/text()'))
                )
            )
        if c.melting_points:
            yield c


### JURAJ ######################################################################
################################################################################
##
## -----------------------------------------------------------------------------

class CNHeadingParser(BaseParser):
    """Coordination number table parsers for default table layout.

    Recognizes::

        'NAs-As', 'NAsAs', 'N AsAs', 'N As-As', 'N-AsAs', 'N-As-As'

    and splits it into::

        cn_title = 'N'
        cn_label = 'AsAs'

    Python 3 compatible

    jm2111@cam.ac.uk
    """
    root = coordination_number_heading
    def interpret(self, result, start, end):
        """"""

        cn_title = first(result.xpath('./cn_title/text()'))
        cn_label = first(result.xpath('./cn_label/text()'))

        if not cn_label:
            cn_title, cn_label, *rest = SplitString(cn_title,coordination_number_title_alt1)
            if not cn_label:
                log.warning("Coordination number without a label was recognized.")
            else:
                cn_label = re.sub('-','',cn_label)

        log.debug("\n    "
                  "etree:    {}\n    "
                  "cn_title: {}\n    "
                  "cn_label: {}".format(etree.tostring(result),cn_title,cn_label))

        c = Compound()
        if cn_label:
            c.coordination_numbers.append(
                CoordinationNumber(
                    label = cn_label
                )
            )
        yield c

class CNCellParser(BaseParser):
    """"""
    root = coordination_number_cell
    def interpret(self, result, start, end):
        """"""
        log.debug(etree.tostring(result))
        c = Compound()
        for cn in result.xpath('text()'):
            c.coordination_numbers.append(
                CoordinationNumber(
                    value=cn
                )
            )
        if c.coordination_numbers:
            yield c

# class CNLabelHeadingParser(BaseParser):
#     """Parse the CN label heading if in separate cell"""
#     root = coordination_number_label_heading
#     def interpret(self, result, start, end):
#         """Parses the heading of the CN labels"""
#         log.debug(etree.tostring(result))
#         c = Compound()
#         yield c
#
# class CNLabelCellParser(BaseParser):
#     """Parses CN labels in separate cells"""
#     root = coordination_number_label_cell
#     def interpret(self, result, start, end):
#         c = Compound()
#         log.debug(etree.tostring(result))
#         label = result.xpath('text()')
#         if label:
#             c.coordination_numbers.append(CoordinationNumber(label=label))
#         if c.coordination_numbers:
#             yield c


################################################################################


class GlassTransitionHeadingParser(BaseParser):
    """"""
    root = glass_transition_heading

    def interpret(self, result, start, end):
        """"""
        glass_transition_units = first(result.xpath('./units/text()'))
        c = Compound()
        if glass_transition_units:
            c.glass_transitions.append(
                GlassTransition(units=glass_transition_units)
            )
        yield c

class GlassTransitionCellParser(BaseParser):
    """"""
    root = glass_transition_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        for tg in result.xpath('./temp'):
            c.glass_transitions.append(
                GlassTransition(
                    value=first(mp.xpath('./value/text()')),
                    units=first(mp.xpath('./units/text()'))
                )
            )
        if c.glass_transition:
            yield c

class ElectrochemicalPotentialHeadingParser(BaseParser):
    """"""
    root = electrochemical_potential_heading

    def interpret(self, result, start, end):
        """"""
        c = Compound(
            electrochemical_potentials=[
                ElectrochemicalPotential(
                    type=first(result.xpath('./electrochemical_potential_type/text()')),
                    units=first(result.xpath('./electrochemical_potential_units/text()'))
                )
            ]
        )
        yield c


class ElectrochemicalPotentialCellParser(BaseParser):
    """"""
    root = electrochemical_potential_cell

    def interpret(self, result, start, end):
        """"""
        c = Compound()
        for value in result.xpath('./electrochemical_potential_value/text()'):
            c.electrochemical_potentials.append(
                ElectrochemicalPotential(
                    value=value
                )
            )
        if c.electrochemical_potentials:
            yield c


class CaptionContextParser(BaseParser):
    """"""
    root = caption_context

    def __init__(self):
        pass

    def interpret(self, result, start, end):
        name = first(result.xpath('./subject_phrase/name/text()'))
        c = Compound(names=[name]) if name else Compound()
        context = {}
        # print(etree.tostring(result[0]))
        solvent = first(result.xpath('./solvent_phrase/name/text()'))
        if solvent is not None:
            context['solvent'] = solvent
        # Melting point shouldn't have contextual temperature
        if context:
            c.melting_points = [MeltingPoint(**context)]
        temp = first(result.xpath('./temp_phrase'))
        if temp is not None:
            context['temperature'] = first(temp.xpath('./temp/value/text()'))
            context['temperature_units'] = first(temp.xpath('./temp/units/text()'))
        # Glass transition temperature shouldn't have contextual temperature
        if context:
            c.glass_transitions = [GlassTransition(**context)]
        temp = first(result.xpath('./temp_phrase'))
        if temp is not None:
            context['temperature'] = first(temp.xpath('./temp/value/text()'))
            context['temperature_units'] = first(temp.xpath('./temp/units/text()'))
        if context:
            c.quantum_yields = [QuantumYield(**context)]
            c.fluorescence_lifetimes = [FluorescenceLifetime(**context)]
            c.electrochemical_potentials = [ElectrochemicalPotential(**context)]
            c.uvvis_spectra = [UvvisSpectrum(**context)]
        if c.serialize():
            # print(c.to_primitive())
            yield c
