# -*- coding: utf-8 -*-
"""
Chemical entity mention parser elements.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re
from lxml import etree

from ..model import Compound
from .actions import join, fix_whitespace
from .common import roman_numeral, cc, nnp, hyph, nns, nn, cd, ls, optdelim, bcm, icm, rbrct, lbrct, sym, jj, hyphen, quote, \
    dt, delim, sym
from .base import BaseParser
from .elements import I, R, W, T, ZeroOrMore, Optional, Not, Group, End, Start, OneOrMore, Any
from ..utils import first, flatten
from lxml import etree

log = logging.getLogger(__name__)

# Added cc889
element_number_regex = r'(\(|\)|\[|\]|\-|\+|\-|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr|\d)'
doping_regex = r'((?:\d\.?)+[\+\-](?:\d\.?)+)'

alphanumeric = R('^(d-)?(\d{1,2}[A-Za-z]{1,2}[′″‴‶‷⁗]?)(-d)?$')

numeric = R('^\d{1,3}$')

letter_number = R('^(H\d)?[LSNM]{1,2}\d\d?$')

# Blacklist to truncate chemical mentions where tags continue on incorrectly
cm_blacklist = (I('and') | W('×') | W('→') | W('+') | W('in') | W(':') + R('^m\.?p\.?$', re.I) | W(':') + Any() + R('^N\.?M\.?R\.?\(?$', re.I))

exclude_prefix = Start() + (lbrct + roman_numeral + rbrct + Not(hyphen) | (R('^\d{1,3}(\.\d{1,3}(\.\d{1,3}(\.\d{1,3})?)?)?$') + Not(hyphen)) | (I('stage') | I('step') | I('section') | I('part')) + (alphanumeric | numeric | roman_numeral | R('^[A-Z]$')))
# Tagged chemical mentions - One B-CM tag followed by zero or more I-CM tags.
cm = (exclude_prefix.hide() + OneOrMore(Not(cm_blacklist) + icm)) | (bcm + ZeroOrMore(Not(cm_blacklist) + icm))

comma = (W(',') | T(',')).hide()
colon = (W(':') | T(':')).hide()

# Prefixes to include in the name
include_prefix = Not(bcm) + R('^(deuterated|triflated|butylated|brominated|acetylated|twisted)$', re.I)

label_type = (Optional(I('reference') | I('comparative')) + R('^(compound|ligand|chemical|dye|derivative|complex|example|intermediate|product|formulae?|preparation)s?$', re.I))('role').add_action(join) + Optional(colon).hide()

synthesis_of = ((I('synthesis') | I('preparation') | I('production') | I('data') | I('spectrum')) + (I('of') | I('for')) | I('product') + Any().hide() + I('of'))('role').add_action(join)

to_give = (I('to') + (I('give') | I('yield') | I('afford')) | I('afforded') | I('affording') | I('yielded'))('role').add_action(join)

label_blacklist = (R('^(31P|[12]H|[23]D|15N|14C[4567890]|MCIF\d+)$'))

prefixed_label = R('^(cis|trans)-((d-)?(\d{1,2}[A-Za-z]{0,2}[′″‴‶‷⁗]?)(-d)?|[LS]\d\d?)$')

#: Chemical label. Very permissive - must be used in context to avoid false positives.
strict_chemical_label = Not(label_blacklist) + (alphanumeric | roman_numeral | letter_number | prefixed_label)('label')

lenient_chemical_label = Not(R('\d{3}')) + (numeric('label') | R('^([A-Z]\d{1,4})$')('label') | strict_chemical_label)

chemical_label = ((label_type + lenient_chemical_label + ZeroOrMore((T('CC') | comma) + lenient_chemical_label)) | (Optional(label_type.hide()) + strict_chemical_label + ZeroOrMore((T('CC') | comma) + strict_chemical_label)))

#: Chemical label with a label type before
chemical_label_phrase1 = (Optional(synthesis_of) + label_type + lenient_chemical_label + ZeroOrMore((T('CC') | comma) + lenient_chemical_label))
#: Chemical label with synthesis of before
chemical_label_phrase2 = (synthesis_of + Optional(label_type) + lenient_chemical_label + ZeroOrMore((T('CC') | comma) + lenient_chemical_label))
# Chemical label with to give/afforded etc. before, and some restriction after.
chemical_label_phrase3 = (to_give + Optional(dt) + Optional(label_type) + lenient_chemical_label + Optional(lbrct + OneOrMore(Not(rbrct) + Any()) + rbrct).hide() + (End() | I('as') | colon | comma).hide())
# Chemical label with a number in round brackets - ADDED BY CC889
label_prefix_blacklist = ((I('equation') | R('^eqn\.?$') | I('figure') | R('^fig\.?$')) + lbrct + R('^\d$') + rbrct)
chemical_label_phrase4 = (Not(label_prefix_blacklist) + lbrct + lenient_chemical_label + rbrct)


element_name = R('^(actinium|aluminium|aluminum|americium|antimony|argon|arsenic|astatine|barium|berkelium|beryllium|bismuth|bohrium|boron|bromine|cadmium|caesium|calcium|californium|carbon|cerium|cesium|chlorine|chromium|cobalt|copernicium|copper|curium|darmstadtium|dubnium|dysprosium|einsteinium|erbium|europium|fermium|flerovium|fluorine|francium|gadolinium|gallium|germanium|hafnium|hassium|helium|holmium|hydrargyrum|hydrogen|indium|iodine|iridium|iron|kalium|krypton|lanthanum|laIrencium|lithium|livermorium|lutetium|magnesium|manganese|meitnerium|mendelevium|mercury|molybdenum|natrium|neodymium|neon|neptunium|nickel|niobium|nitrogen|nobelium|osmium|oxygen|palladium|phosphorus|platinum|plumbum|plutonium|polonium|potassium|praseodymium|promethium|protactinium|radium|radon|rhenium|rhodium|roentgenium|rubidium|ruthenium|rutherfordium|samarium|scandium|seaborgium|selenium|silicon|silver|sodium|stannum|stibium|strontium|sulfur|tantalum|technetium|tellurium|terbium|thallium|thorium|thulium|tin|titanium|tungsten|ununoctium|ununpentium|ununseptium|ununtrium|uranium|vanadium|Iolfram|xenon|ytterbium|yttrium|zinc|zirconium)$', re.I)

#: Mostly unambiguous element symbols
element_symbol = R('^(Ag|Au|Br|Cd|Cl|Cu|Fe|Gd|Ge|Hg|Mg|Pb|Pd|Pt|Ru|Sb|Si|Sn|Ti|Xe|Zn|Zr)$')

#: Registry number patterns
registry_number = R('^BRN-?\d+$') | R('^CHEMBL-?\d+$') | R('^GSK-?\d{3-7}$') | R('^\[?(([1-9]\d{2,7})|([5-9]\d))-\d\d-\d\]?$')

#: Amino acid abbreviations. His removed, too ambiguous
amino_acid = R('^((Ala|Arg|Asn|Asp|Cys|Glu|Gln|Gly|Ile|Leu|Lys|Met|Phe|Pro|Ser|Thr|Trp|Tyr|Val)-?)+$')

amino_acid_name = (
    R('^(histidine|isoleucine|leucine|lysine|methionine|phenylalanine|threonine|tryptophan|valine|selenocysteine|serine|tyrosine|alanine|arginine|asparagine|cysteine|glutamine|glycine|proline)$', re.I) |
    I('aspartic') + I('acid') | I('glutamic') + I('acid')
)

#: Chemical formula patterns - updated cc889 to include element symbols - updated by jm2111 to include complicated compounds
#  like: 0.9(Ge5As55Te40)-0.1Cu
formula = (
    R('^C\(?\d{1,3}\)?(([HNOP]|Cl)\(?\d\d?\)?)+(\(?\d?[\+\-]\d?\)?)?$') |
    R('^(([\d.]+)?(\(|A[glmrsu]|B[ahikr]|C[adeflmnorsu]|D[bsy]|E[rsu]|F[elmr]|G[ade]|H[efgos]|I[r][1-9]?|KL[airuv]|M[dgnot]|N[abdeip]|O[s\d]|P[abdmotu]|R[abefghnu]|S[bcegimnr]|T[abehil]|U(u[opst])|Xe|Yb?|Z[nr]|\))[+-]?([\d.]+)?)+$') |
    R('^((\(?\d{2,3}\)?)?(Fe|Ti|Mg|Ru|Cd|Se)\(?(\d\d?|[IV]+)?\)?((O|Hg)\(?\d?\d?\)?)?)+(\(?\d?[\+\-]\d?\)?)?$') |
    R('(NaOH|CaCl\d?\d?|EtOH|EtAc|MeOH|CF\d|C\d?\d?H\d\d?)+$') |
    R('(NO\d|BH4|Ca\(2\+\)|Ti\(0\)2|\(CH3\)2CHOH|\(CH3\)2CO|\(CH3\)2NCOH|C2H5CN|CH2ClCH2Cl|CH3C6H5|CH3CN|CH3CO2H|CH3COCH3|CH3COOH|CH3NHCOH|CH3Ph|CH3SOCH3|Cl2CH2|ClCH2CH2Cl)') |
    R('^(\(CD3\)2CO|\(CDCl2\)2|C6D6|C2D5CN|CD2Cl2|CD3CN|CD3COCD3|CD3OD|CD3SOCD3|CDCl3|CH3OD|D2O|EtOD|MeOD)$') |
    R('^[\[\{\(].*(NH\d|H2O|NO\d|C\d?H\d|C–H|NBu4|CF3|CD3|CO2|[bp]i?py|\(CO\)|\d,\d[\'′]?-|BF4|PF6|Cl\d|Fe\d|Ph\d).*[\]\}\)].*$') |
    R('^[\[\{\(]{1,2}(Ru|Ph|Py|Cu|Ir|Pt|Et\d).*[\]\}\)]$') |
    R('^(GABA|NO|\(\d\)H|KCl)$'))

# jm2111, don't recognize parentheses alone
# the right parentheses ')' alone cannot start and, the left parentheses alone '(' cannot conclude a token that will be used within a chemical formula
# changing this can affect complicated formulae recognition, such as '0.9(Ge5As55Te40)-0.1Cu (GATC)'
formula_blacklist = (R('^[\u0029\u207E\u208E\u2769\u276B\u2773\u27EF\u2986\u2998\uFE5A\uFF09]+') | R('[\u0028\u207D\u208D\u2768\u276A\u2772\u27EE\u2985\u2997\uFE59\uFF08]+$'))


solvent_formula = (
    W('CCl4') | W('(CH3)2CHOH') | W('(CH3)2CO') | W('(CH3)2NCOH') | W('C2H4Cl2') | W('C2H5CN') | W('C2H5OH') |
    W('C5H5N') | W('C6H12') | W('C6H14') | W('C6H5CH3') | W('C6H5Cl') | W('C6H6') | W('C7H8') | W('CH2Cl2') |
    W('CH2ClCH2Cl') | W('CH3C6H5') | W('CH3Cl') | W('CH3CN') | W('CH3CO2H') | W('CH3COCH3') | W('CH3COOH') |
    W('CH3NHCOH') | W('CH3NO2') | W('CH3OH') | W('CH3Ph') | W('CH3SOCH3') | W('CHCl2') | W('CHCl3') | W('Cl2CH2') |
    W('ClCH2CH2Cl')
)

# Over-tokenized variants first, useful for matching in tables with fine tokenizer
nmr_solvent = (
    I('THF') + W('-') + I('d8') | I('d8') + W('-') + I('THF') | I('acetone') + W('-') + I('d6') |
    I('d6') + W('-') + I('acetone') | I('chloroform') + W('-') + I('d') | I('d') + W('-') + I('chloroform') |
    I('methanol') + W('-') + I('d4') | I('d4') + W('-') + I('methanol') | I('pyridine') + W('-') + I('d5') |
    I('d5') + W('-') + I('pyridine') | I('DMSO') + W('-') + I('d6') | I('d6') + W('-') + I('DMSO') |
    I('dimethylsulfoxide') + W('-') + I('d6') | I('d6') + W('-') + I('dimethylsulfoxide') |
    W('MeOH') + W('-') + I('d4') | I('d4') + W('-') + W('MeOH') | I('benzene-d6') + W('-') + I('d6') |
    I('d6') + W('-') + I('benzene') | I('d2') + W('-') + I('tetrachloroethane') |
    I('tetrachloroethane') + W('-') + I('d2') |

    I('(CD3)2CO') | I('(CDCl2)2') | I('C6D6') | I('C2D5CN') | I('CD2Cl2') | I('CD3CN') | I('CD3COCD3') | I('CD3OD') |
    I('CD3SOCD3') | I('CDCl3') | I('CH3OD') | I('D2O') | W('EtOD') | W('MeOD') | I('THF-d8') | I('d8-THF') |
    I('acetone-d6') | I('d6-acetone') | I('chloroform-d') | I('d-chloroform') | I('methanol-d4') | I('d4-methanol') |
    I('pyridine-d5') | I('d5-pyridine') | I('DMSO-d6') | I('d6-DMSO') | I('dimethylsulfoxide-d6') | W('C7D8') |
    I('d6-dimethylsulfoxide') | W('MeOH-d4') | W('d4-MeOH') | I('DMSO') | I('benzene-d6') | I('d6-benzene') |
    I('1,1,2,2-tetrachloroethane-d2') | I('tetrachloroethane-d2') | I('d2-tetrachloroethane')

)

# My abbreviations
AMO_abbrev = ('GST')

#: Solvent names.
other_solvent = (
    I('3-amino-4-ethoxycarbonylpyrazole') |
    I('1-butanol') | I('1-butylimidazole') | I('1-cyclohexanol') | I('1-decanol') | I('1-heptanol') | I('1-hexanol') |
    I('1-methylethyl') + I('acetate') | I('1-octanol') | I('1-pentanol') | I('1-phenylethanol') | I('1-propanol') |
    I('1-undecanol') | I('1,1,1-trifluoroethanol') | I('1,1,1,3,3,3-hexafluoro-2-propanol') |
    I('1,1,1,3,3,3-hexafluoropropan-2-ol') | I('1,1,2-trichloroethane') | I('1,2-c2h4cl2') | I('1,2-dichloroethane') |
    I('1,2-dimethoxyethane') | I('1,2-dimethylbenzene') | I('1,2-ethanediol') | I('1,2,4-trichlorobenzene') |
    I('1,4-dimethylbenzene') | I('1,4-dioxane') | I('2-(n-morpholino)ethanesulfonic') + I('acid') | I('2-butanol') |
    I('2-butanone') | I('2-me-thf') | I('2-methf') | I('2-methoxy-2-methylpropane') |
    I('2-methyl') + I('tetrahydrofuran') | I('2-methylpentane') | I('2-methylpropan-1-ol') | I('2-methylpropan-2-ol') |
    I('2-methyltetrahydrofuran') | I('2-proh') | I('2-propanol') | I('2-propyl') + I('acetate') | I('2-pyrrolidone') |
    I('2,2,2-trifluoroethanol') | I('2,2,4-trimethylpentane') | I('2Me-THF') | I('2MeTHF') | I('3-methyl-pentane') |
    I('4-methyl-1,3-dioxolan-2-one') | I('acetic') + I('acid') | I('aceto-nitrile') | I('acetone') | I('acetonitrile') |
    I('acetononitrile') | I('AcOEt') | I('AcOH') | I('AgNO3') | I('aniline') | I('anisole') | I('benzene') |
    I('benzonitrile') | I('benzyl') + I('alcohol') | I('bromoform') | I('Bu2O') | I('Bu4NBr') | I('Bu4NClO4') |
    I('Bu4NPF6') | I('BuCN') | I('BuOH') | I('butan-1-ol') | I('butan-2-ol') | I('butan-2-one') | I('butane') |
    I('butanol') | I('butanone') | I('butene') | I('butyl') + I('acetate') | I('butyl') + I('acetonitrile') |
    I('butyl') + I('alcohol') | I('butyl') + I('amine') | I('butyl') + I('chloride') | I('butyl') + I('imidazole') |
    I('butyronitrile') | I('c-hexane') | I('carbon') + I('disulfide') | I('carbon') + I('tetrachloride') |
    I('chlorobenzene') | I('chloroform') | I('chloromethane') | I('chlorotoluene') | I('CHX') | I('cumene') |
    I('cyclohexane') | I('cyclohexanol') | I('cyclopentyl') + I('methyl') + I('ether') | I('DCE') | I('DCM') | I('decalin') |
    I('decan-1-ol') | I('decane') | I('decanol') | I('DEE') | I('di-isopropyl') + I('ether') |
    I('di-n-butyl') + I('ether') | I('di-n-hexyl') + I('ether') | I('dibromoethane') | I('dibutoxymethane') |
    I('dibutyl') + I('ether') | I('dichloro-methane') | I('dichlorobenzene') | I('dichloroethane') |
    I('dichloromethane') | I('diethoxymethane') | I('diethyl') + I('carbonate') | I('diethyl') + I('ether') |
    I('diethylamine') | I('diethylether') | I('diglyme') | I('dihexyl') + I('ether') | I('diiodomethane') |
    I('diisopropyl') + I('ether') | I('diisopropylamine') | I('dimethoxyethane') | I('dimethoxymethane') |
    I('dimethyl') + I('acetamide') | I('dimethyl') + I('acetimide') | I('dimethyl') + I('benzene') |
    I('dimethyl') + I('carbonate') | I('dimethyl') + I('ether') | I('dimethyl') + I('formamide') |
    I('dimethyl') + I('sulfoxide') | I('dimethylacetamide') | I('dimethylbenzene') | I('dimethylformamide') |
    I('dimethylformanide') | I('dimethylsulfoxide') | I('dioctyl') + I('sodium') + I('sulfosuccinate') | I('dioxane') |
    I('dioxolane') | I('dipropyl') + I('ether') | I('DMAc') | I('DMF') | I('DMSO') | I('Et2O') | I('EtAc') |
    I('EtAcO') | I('EtCN') | I('ethane') + I('diol') | I('ethane-1,2-diol') | I('ethanol') |
    I('ethyl') + I('(S)-2-hydroxypropanoate') | I('ethyl') + I('acetate') | I('ethyl') + I('benzoate') |
    I('ethyl') + I('formate') | I('ethyl') + I('lactate') | I('ethyl') + I('propionate') | I('ethylacetamide') |
    I('ethylacetate') | I('ethylene') + I('carbonate') | I('ethylene') + I('glycol') | I('ethyleneglycol') |
    I('ethylhexan-1-ol') | I('EtOAc') | I('EtOH') | I('eucalyptol') | I('F3-ethanol') | I('F3-EtOH') | I('formamide') |
    I('formic') + I('acid') | I('glacial') + I('acetic') + I('acid') | I('glycerol') | I('H2O') | I('H2O2') |
    I('H2SO4') | I('HBF4') | I('HCl') | I('HClO4') | I('HCO2H') | I('HCONH2') | I('heptan-1-ol') |
    I('heptane') | I('heptanol') | I('heptene') | I('HEX') | I('hexadecylamine') | I('hexafluoroisopropanol') |
    I('hexafluoropropanol') | I('hexan-1-ol') | I('hexane') | I('hexanes') | I('hexanol') | I('hexene') |
    I('hexyl') + I('ether') | I('HFIP') | I('HFP') | I('HNO3') | I('hydrochloric') + I('acid') |
    I('hydrogen') + I('peroxide') | I('iodobenzene') | I('isohexane') | I('isooctane') | I('isopropanol') |
    I('isopropyl') + I('benzene') | I('KBr') | I('LiCl') | I('ligroine') | I('limonene') | I('Me-THF') | I('Me2CO') |
    I('MeCN') | I('MeCO2Et') | I('MeNO2') | I('MeOH') | I('mesitylene') | I('methanamide') | I('methanol') |
    I('MeTHF') | I('methoxybenzene') | I('methoxyethylamine') | I('methyl') + I('acetamide') |
    I('methyl') + I('acetoacetate') | I('methyl') + I('benzene') | I('methyl') + I('butane') |
    I('methyl') + I('cyclohexane') | I('methyl') + I('ethyl') + I('ketone') | I('methyl') + I('formamide') |
    I('methyl') + I('formate') | I('methyl') + I('isobutyl') + I('ketone') | I('methyl') + I('laurate') |
    I('methyl') + I('methanoate') | I('methyl') + I('naphthalene') | I('methyl') + I('pentane') |
    I('methyl') + I('propan-1-ol') | I('methyl') + I('propan-2-ol') | I('methyl') + I('propionate') |
    I('methyl') + I('pyrrolidin-2-one') | I('methyl') + I('pyrrolidine') | I('methyl') + I('pyrrolidinone') |
    I('methyl') + I('t-butyl') + I('ether') | I('methyl') + I('tetrahydrofuran') | I('methyl-2-pyrrolidone') |
    I('methylbenzene') | I('methylcyclohexane') | I('methylene') + I('chloride') | I('methylformamide') |
    I('methyltetrahydrofuran') | I('MIBK') | I('morpholine') | I('mTHF') | I('n-butanol') |
    I('n-butyl') + I('acetate') | I('n-decane') | I('n-heptane') | I('n-HEX') | I('n-hexane') | I('n-methylformamide') |
    I('n-methylpyrrolidone') | I('n-nonane') | I('n-octanol') | I('n-pentane') | I('n-propanol') |
    I('n,n-dimethylacetamide') | I('n,n-dimethylformamide') | I('n,n-DMF') | I('Na2SO4') | I('NaCl') | I('NaClO4') |
    I('NaHCO3') | I('NaOH') | I('nBu4NBF4') | I('nitric') + I('acid') | I('nitrobenzene') | I('nitromethane') |
    I('nonane') | I('nujol') | I('o-dichlorobenzene') | I('o-xylene') | I('octan-1-ol') | I('octane') | I('octanol') |
    I('octene') | I('ODCB') | I('p-xylene') | I('pentan-1-ol') | I('pentane') | I('pentanol') | I('pentanone') |
    I('pentene') | I('PeOH') | I('perchloric') + I('acid') | I('PhCH3') | I('PhCl') | I('PhCN') | I('phenoxyethanol') |
    I('phenyl') + I('acetylene') | I('Phenyl') + I('ethanol') | I('phenylamine') | I('phenylethanolamine') |
    I('phenylmethanol') | I('PhMe') | I('phosphate') | I('phosphate') + I('buffered') + I('saline') | I('pinane') |
    I('piperidine') | I('polytetrafluoroethylene') | I('potassium') + I('bromide') |
    I('potassium') + I('phosphate') + I('buffer') | I('PrCN') | I('PrOH') | I('propan-1-ol') | I('propan-2-ol') |
    I('propane') | I('propane-1,2-diol') | I('propane-1,2,3-triol') | I('propanol') | I('propene') |
    I('propionic') + I('acid') | I('propionitrile') | I('propyl') + I('acetate') | I('propyl') + I('amine') |
    I('propylene') + I('carbonate') | I('propylene') + I('glycol') | I('pyridine') | I('pyrrolidone') | I('quinoline') |
    I('silver') + I('nitrate') | I('SNO2') | I('sodium') + I('chloride') | I('sodium') + I('hydroxide') |
    I('sodium') + I('perchlorate') | I('sulfuric') + I('acid') | I('t-butanol') | I('TBABF4') | I('TBAF') | I('TBAH') |
    I('TBAOH') | I('TBAP') | I('TBAPF6') | I('TEAP') | I('TEOA') | I('tert-butanol') | I('tert-butyl') + I('alcohol') |
    I('tetrabutylammonium') + I('hexafluorophosphate') | I('tetrabutylammonium') + I('hydroxide') |
    I('tetrachloroethane') | I('tetrachloroethylene') | I('tetrachloromethane') | I('tetrafluoroethylene') |
    I('tetrahydrofuran') | I('tetralin') | I('tetramethylsilane') | I('tetramethylurea') | I('tetrapiperidine') |
    I('TFA') | I('TFE') | I('THF') | I('tin') + I('dioxide') | I('titanium') + I('dioxide') | I('toluene') |
    I('tri-n-butyl') + I('phosphate') | I('triacetate') | I('triacetin') | I('tribromomethane') |
    I('tributyl') + I('phosphate') | I('trichlorobenzene') | I('trichloroethene') | I('trichloromethane') |
    I('triethyl') + I('amine') | I('triethyl') + I('phosphate') | I('triethylamine') |
    I('trifluoroacetic') + I('acid') | I('trifluoroethanol') | I('trimethyl') + I('benzene') |
    I('trimethyl') + I('pentane') | I('tris') | I('undecan-1-ol') | I('undecanol') | I('valeronitrile') | I('water') |
    I('xylene') | I('xylol') |

    I('[nBu4N][BF4]') | I('BCN') | I('ACN') | I('BTN') | I('BHDC') | I('AOT') | I('DMA') | I('Triton X-100') |
    I('MOPS') | I('TX-100') | I('H2O') + I('+') + I('TX') | I('H2O-Triton X') | I('MES') | I('HDA') | I('PIPES') |
    I('heavy') + I('water') | I('IPA') | I('KPB') | I('MCH') | I('NPA') | I('NMP') | I('PBS') | I('HEPES') |
    I('SDS') | I('TBP') | I('TEA')
)

# Potentially problematic solvent names at the end above...


# scheme blacklist - avoid scheme labels e.g S1 from being a cem
scheme_blacklist = R('^S\d+$')

# magnetic and chemical compound prefixes and suffixes - cc889
cem_prefixes = (I('bulk') | I('crystalline') | I('amorphous') | I('pure') | I('powdered') | (Optional(R('^[A-Z][a-z]?$') + R('\-')) + I('doped')))
cem_suffixes = (I('nanoparticles') | I('NPs') | I('nanocrystals') | I('nanotubes') | I('nanowires') | I('cores') | I('crystals') | (Optional(I('thin')) + I('films')) | I('ceramics'))

# magnetic blacklist, avoid common magnetism terms being labelled as a cem
magnetic_blacklist = (I('Morin') | I('RE') | R('^[P|p]erovskite(s)?') | R('^[o|O]xide(s)?$') | I('oxide') |
                      I('Oxy-anions') | I('oxy-anion') | I('transition-metal') | I('rare-earth') | R('^CO$') | I('ferrous') |
                      I('ferro-') | I('ferro') | I('ferri-') |
                      ((I('Ti') | I('Fe') | I('Mn')) + R('\-') + (I('poor') | I('rich'))) |
                      (I('ferroelectric') + I('oxides')) | (I('[') + OneOrMore(R('^\d.?$')) + I(']')))

# Magnetic names, common cems found in magnetism literature - added by cc889
magnetic_name = (W('La1/3Ca2/3MnO3') | I('β-MnS') | I('α-MnS') | I('BFSMO') | I('BFO') | I('BF') | I('LCO') | I('BLFMO') | I('RE–BFO') | I('LFP') | I('NFP') | I('R-LFP') | I('LCP') | W('Pb(Fe2/3W1/3)O3') | (I('bismuth') + (I('ferrites') | I('chromites'))) | W('Pb(Fe2/3W1/3)O3') | I('LSMO') | (I('Mn') + R('\-') + I('Pp0')))

solvent_name_options = (nmr_solvent | solvent_formula | other_solvent)
solvent_name = (Optional(include_prefix) + solvent_name_options)('name').add_action(join).add_action(fix_whitespace)

chemical_name_options = Not(scheme_blacklist | magnetic_blacklist | formula_blacklist) + (Optional(cem_prefixes) + (cm | element_name | element_symbol | registry_number | amino_acid | amino_acid_name | formula | magnetic_name) + Optional(cem_suffixes)) + Not(I('concentration'))
chemical_name = (Optional(include_prefix) + chemical_name_options)('name').add_action(join).add_action(fix_whitespace)


# Label phrase structures
# label_type delim? label delim? chemical_name ZeroOrMore(delim cc label delim? chemical_name)

label_name_cem = (chemical_label + optdelim + chemical_name)('cem')
labelled_as = (R('^labell?ed$') + W('as')).hide()
optquote = Optional(quote.hide())

label_before_name = Optional(synthesis_of | to_give) + label_type + optdelim + label_name_cem + ZeroOrMore(optdelim + cc + optdelim + label_name_cem)

likely_abbreviation = (Optional(include_prefix + Optional(hyphen)) + R('^([A-Z]{2,6}(\-[A-Z]{1,6})?|[A-Z](\-[A-Z]{2,6}))$'))('name').add_action(join).add_action(fix_whitespace)

name_with_optional_bracketed_label = (Optional(synthesis_of | to_give) + chemical_name + Optional(I('with') + chemical_name) + Optional(lbrct + Optional(labelled_as + optquote) + (chemical_label | lenient_chemical_label | likely_abbreviation | chemical_name) + Optional(comma) + Optional((chemical_label | lenient_chemical_label | likely_abbreviation | chemical_name)) + optquote + rbrct))('cem')

name_with_bracketed_label = (chemical_name + lbrct + lenient_chemical_label + rbrct)('cem')

# Lenient name match that should be used with stricter surrounding context
lenient_name = OneOrMore(Not(rbrct) + (bcm | icm | jj | nn | nnp | nns | hyph | cd | ls | W(',')))('name').add_action(join).add_action(fix_whitespace)

# Very lenient name and label match, with format like "name (Compound 3)"
lenient_name_with_bracketed_label = (Start() + Optional(synthesis_of) + lenient_name + lbrct + label_type.hide() + lenient_chemical_label + rbrct)('cem')

# chemical name with a comma in it that hasn't been tagged.
name_with_comma_within = Start() + Group(Optional(synthesis_of) + (cm + W(',') + Not(cm) + cm + Not(I('and')))('name').add_action(join).add_action(fix_whitespace))('cem')

# TODO: Currently ensuring roles are captured from text preceding cem/cem_phrase ... abstract out the 'to_give"
cem = (lenient_name_with_bracketed_label | label_before_name | name_with_comma_within | name_with_optional_bracketed_label)

# INFORMAL CHEMICAL NAMES ##########
# Informal chemical labels - cc889
# Informal chemical formula, highly permissive, can only be used in this context to avoid FPs
informal_chemical_formula = (R('^([\(\[]?(A[glmrsu]|B[ahikr\′]|C[adeflmnorsu]|D[bsy]|E[rsu]|F[elmr]|G[ade]|H([fgos]|REE)?|I[r]?|L([ainruv]|REE)|M[dgnot]?|N[abdeip]|O|P[abdmotu]|R([abefghnu]|E[EMOY]?)?|S[bcegimnr]|T[abehil]?|U(u[opst])|V|W|Xe?|Yb?|Z[nr])[\)\]]?([\d.\+]+)?){2,}$'))('name')
# Identifiers typically used as informal chemical symbols
informal_chemical_identifier = (W('RE') | W('R') | W('REM') | W('REO') | W('REY') | W('LREE') | W('HREE') | W('Ln') | W('B′') | W('M') | W('T') | W('ET')
                           | W('IM2py') | W('NN′3') | W('TDAE') | W('X') | I('x') | I('H2mal'))('identifier')

# list of chemical elements or ion symbols by type
metals = (R('^(Li|Be|Na|Mg|Al|K|Ca|Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|Fr|Ra|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Uut|Fl|Uup|Lv)$') | R('^metal(s)?$'))('sub_cem')
transition_metals = (R('^(Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Em|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn)$') | (I('transition') + (I('metal') | I('metals'))))('sub_cem')
lanthanides = (R('^(Sc|Y|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu)$') | R('^[Ll]anthanide(s)?$') | (R('^[Rr]are\-?earth(s)?$') | (I('rare') + Optional(T('HYPH')) + R(('^earth(s)?$')) + Optional(R('^metal(s)?$')))))('sub_cem')
ion_symbol = (R('^(Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Ce|Ir|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Li|Be|Na|Al|As)(([2|3|4|5|6|7]?\+?)|\(I{2,7}\))?$'))

# Sub compounds could be numerically labelled in brackets
sub_cem_label = (lbrct + lenient_chemical_label + rbrct)('sub_cem_label').add_action(join)
sub_cem = Group(metals | lanthanides | transition_metals | ion_symbol)('sub_cem_name').add_action(join)
sub_cem_phrase = (sub_cem + Optional(sub_cem_label))('sub_cem')

# Phrase such as REMnO3 (RE = Sc, Y, Gd)
informal_cem_phrase = ((cem | Group(informal_chemical_formula)('cem')) + Optional(optdelim) + (I('where') | optdelim) + Group(informal_chemical_identifier + W('=') + OneOrMore(sub_cem_phrase | delim | I('or') | I('and').hide()))('informal_label'))('informal_cem_phrase')

# Informal labelling, used for associating properties to informal compounds
# Informal label phrase 1, "property = value for identifier = <element>"
informal_chemical_label1 = (informal_chemical_identifier + W('=') + (metals | transition_metals | lanthanides | delim | I('and').hide()))('label').add_action(join)
# Informal label phrase 2, "property = value for the <element> compound"
informal_chemical_label2 = ((metals | lanthanides| transition_metals) + (I('compound') | I('sample') | I('material')).hide())('label').add_action(join)

informal_chemical_label = (informal_chemical_label1 | informal_chemical_label2)
informal_chemical_label_phrase = (Optional(I('for') | I('in')).hide() + Optional(I('the')).hide() + informal_chemical_label)('informal_label_phrase')

###### DOPED CHEMICAL NAMES ##########
# Chemical names with doping labels within
numeric_blacklist = (R('^\d+(\.\d+)?$') | T('CD'))
doped_chemical_formula = (Not(numeric_blacklist) +
                          R('^([\(\[\)\]]?(A[glmrsu]|B[ahikr\′]|C[adeflmnorsu]|D[bsy]|E[rsu]|F[elmr]|G[ade]|H([fgos]|REE)?|I[r]?|L([ainruv]|REE)|M[dgnot]?|N[abdeip]|O|P[abdmotu]|R([abefghnu]|E[EMOY]?)?|S[bcegimnr]|T[abehil]?|U(u[opst])|V|W|Xe?|Yb?|Z[nr])[\)\]\(\[]?(([\d.\-\+]+)?(\(?[1-9]{1,3}[\-\+])?[xy]?\)?)?[\)\]\(\[]?)+$'))('name')

doped_chemical_identifier = (W('x') | W('y'))('identifier')
doping_value = R('^(\d\.?)+$')
doping_range = doping_value + T('HPYH') + doping_value
doping = (doping_range | doping_value)('doping_value')
doped_cem_phrase = ((cem | Group(doped_chemical_formula)('cem')) + Optional(optdelim) + (I('where') | optdelim) + Group(doped_chemical_identifier + W('=') + OneOrMore(doping | delim | I('or') | I('and').hide()))('doped_label'))('doped_cem_phrase')

# dopant labelling, used for associating properties to doped compounds
# doped label phrase 1, "property = value for x = 0.1"
doped_chemical_label1 = (doped_chemical_identifier + W('=') + doping_value)('label').add_action(join)
# doped label phrase 2, "property = value for the x = 0.1 compound"
doped_chemical_label2 = (doped_chemical_identifier + W('=') + doping_value + (I('compound') | I('sample') | I('material')).hide())('label').add_action(join)

doped_chemical_label = (doped_chemical_label1 | doped_chemical_label2)
doped_chemical_label_phrase = (Optional(I('for') | I('in')).hide() + Optional(I('the')).hide() + doped_chemical_label)('doped_label_phrase')


cem_phrase = (Group(informal_cem_phrase) | Group(doped_cem_phrase) | (Group(cem)('cem_phrase'))).add_action(fix_whitespace)

chemical_label_phrase = (Group(informal_chemical_label_phrase) | Group(doped_chemical_label_phrase) | Group(chemical_label_phrase1 | chemical_label_phrase2 | chemical_label_phrase3 | chemical_label_phrase4)('chemical_label_phrase'))

r_equals = R('^[R]$') + W('=') + OneOrMore(Not(rbrct) + (bcm | icm | nn | nnp | nns | hyph | cd | ls))
of_table = (I('of') | I('in')) + Optional(dt) + I('table')

bracketed_after_name = Optional(comma) + lbrct + Optional(labelled_as + optquote) + (chemical_label | lenient_chemical_label | likely_abbreviation) + optquote + Optional(Optional(comma) + r_equals | of_table) + rbrct
comma_after_name = comma + Optional(labelled_as + optquote) + (chemical_label | likely_abbreviation)

compound_heading_ending = (Optional(comma) + ((lbrct + (chemical_label | lenient_chemical_label | lenient_name) + Optional(Optional(comma) + r_equals | of_table) + rbrct) | chemical_label) + Optional(R('^[:;]$')).hide() | comma + (chemical_label | lenient_chemical_label)) + Optional(W('.')) + End()

# Section number, to allow at the start of a heading
section_no = Optional(I('stage') | I('step') | I('section') | I('part')) + (T('CD') | R('^\d{1,3}(\.\d{1,3}(\.\d{1,3}(\.\d{1,3})?)?)?$') | (Optional(lbrct) + roman_numeral + rbrct))

compound_heading_style1 = Start() + Optional(section_no.hide()) + Optional(synthesis_of) + OneOrMore(Not(compound_heading_ending) + (bcm | icm | jj | nn | nnp | nns | hyph | sym | cd | ls | W(',')))('name').add_action(join).add_action(fix_whitespace) + compound_heading_ending + End()
compound_heading_style2 = chemical_name + Optional(bracketed_after_name)
compound_heading_style3 = synthesis_of + (lenient_name | chemical_name) + Optional(bracketed_after_name | comma_after_name)  # Possibly redundant?
compound_heading_style4 = label_type + lenient_chemical_label + ZeroOrMore((T('CC') | comma) + lenient_chemical_label) + (lenient_name | chemical_name) + Optional(bracketed_after_name | comma_after_name)


compound_heading_phrase = Group(compound_heading_style1 | compound_heading_style2 | compound_heading_style3 | compound_heading_style4)('cem')


def standardize_role(role):
    """Convert role text into standardized form."""
    role = role.lower()
    if any(c in role for c in {'synthesis', 'give', 'yield', 'afford', 'product', 'preparation of'}):
        return 'product'
    return role


def create_informal_label(idt, c):
    """
    standardise the form of informal labels
    """
    sub_cem = first(c.xpath('./sub_cem_name/text()'))
    sub_cem_label = first(c.xpath('./sub_cem_label/text()'))
    if sub_cem_label:
        return [idt + ' = ' + sub_cem, sub_cem, sub_cem_label]
    return [idt + ' = ' + sub_cem, sub_cem]


def create_doped_label(idt, v):
    """
     Standardise the form of doped compound labels

    """
    return [idt + ' = ' + v]


def standardise_name(informal_name, ident, sub_cem):
    """ Use informal sub compounds to re-create full compound names"""
    # strip out informal labels and replace with sub compound label
    split_name = [e for e in re.split(element_number_regex, informal_name) if e]
    for i in range(0, len(split_name)):
        if split_name[i] == ident:
            split_name[i] = sub_cem

    # rejoin
    new_name = ''.join(split_name)

    return [informal_name, new_name]


def standardise_doped_name(doped_name, ident, val):
    """ Use doping values to recreate full doped compound names
        e.g Li1+xMn for x = 0.1 becomes Li(1.1)Mn"""
    # strip out informal labels and replace with sub compound label
    #print(doped_name)
    split_name = [e for e in re.split(element_number_regex, doped_name) if e]
    for i in range(0, len(split_name)):
        if split_name[i] == ident:
            split_name[i] = val

    # rejoin
    new_name = ''.join(split_name)
    # Convert any (1+x) etc to numbers
    for res in re.findall(doping_regex, new_name):
        new_name = new_name.replace(res, str(eval(res.strip('(').strip(')'))))

    return [doped_name, new_name]


class CompoundParser(BaseParser):
    """Chemical name or informal chemical name possibly with an associated label."""

    root = cem_phrase

    def interpret(self, result, start, end):
        #print(etree.tostring(result))
        if result.tag == 'informal_cem_phrase':
            idt = first(result.xpath('./informal_label/identifier/text()'))
            scs = [x for x in result.xpath('./informal_label/sub_cem')]
            for sc in scs:
                dn = first(result.xpath('./cem/name/text()'))
                if dn:
                    c = Compound(names=standardise_name(first(result.xpath('./cem/name/text()')), idt, first(sc.xpath('./sub_cem_name/text()'))),
                                 labels=create_informal_label(idt, sc))

                    yield c

        if result.tag == 'doped_cem_phrase':
            idt = first(result.xpath('./doped_label/identifier/text()'))
            values = [x.text for x in result.xpath('./doped_label/doping_value')]
            for v in values:
                dn = first(result.xpath('./cem/name/text()'))
                if dn:
                    c = Compound(names=standardise_doped_name(dn, idt, v),
                                 labels=create_doped_label(idt, v))
                    yield c
        else:
            for cem_el in result.xpath('./cem'):
                c = Compound(
                    names=cem_el.xpath('./name/text()'),
                    labels=cem_el.xpath('./label/text()'),
                    roles=[standardize_role(r) for r in cem_el.xpath('./role/text()')]
                )
                yield c


class ChemicalLabelParser(BaseParser):
    """Chemical label occurrences with no associated name."""

    root = chemical_label_phrase

    def interpret(self, result, start, end):
        #print(etree.tostring(result))
        roles = [standardize_role(r) for r in result.xpath('./role/text()')]
        for label in result.xpath('./label/text()'):
            yield Compound(labels=[label], roles=roles)


class CompoundHeadingParser(BaseParser):
    """Better matching of abbreviated names in dedicated compound headings."""

    root = compound_heading_phrase

    def interpret(self, result, start, end):
        roles = [standardize_role(r) for r in result.xpath('./role/text()')]
        labels = result.xpath('./label/text()')
        if len(labels) > 1:
            for label in labels:
                yield Compound(labels=[label], roles=roles)
            for name in result.xpath('./name/text()'):
                yield Compound(names=[name], roles=roles)
        else:
            yield Compound(
                names=result.xpath('./name/text()'),
                labels=labels,
                roles=roles
            )