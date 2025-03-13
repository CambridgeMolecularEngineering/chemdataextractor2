# -*- coding: utf-8 -*-
"""
A factory class for making Chemical entity mention parser elements to make overriding easier.
..codeauthor:: Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractproperty, abstractmethod
import logging
import re
from lxml import etree

from .actions import join, fix_whitespace, merge
from .common import (
    roman_numeral,
    cc,
    nnp,
    hyph,
    nns,
    nn,
    cd,
    ls,
    optdelim,
    bcm,
    icm,
    rbrct,
    lbrct,
    sym,
    jj,
    hyphen,
    quote,
    dt,
    delim,
)
from .base import BaseSentenceParser, BaseTableParser
from .elements import (
    I,
    R,
    W,
    T,
    ZeroOrMore,
    Optional,
    Not,
    Group,
    End,
    Start,
    OneOrMore,
    Any,
    SkipTo,
    Every,
)


def not_separator(result):
    """
    To make things as simple as possible when parsing Tables, we concatenate the Cell content
    and the table headings using special characters (we have chosen 🙃 as we don't believe
    this should ever occur in a paper). This checks whether this is included in the result.
    """
    # print(etree.tostring(result[0]), result[0].text, '🙃' in result[0].text)
    if "🙃" in result[0].text:
        return False
    return True


class _CemFactory:
    _default_cem_factory = None

    def __init__(self, **kwargs):
        self.icm = kwargs.get("icm", icm.with_condition(not_separator))
        self.bcm = kwargs.get("bcm", bcm.with_condition(not_separator))
        # self.joining_characters = kwargs.get("joining_characters", R(r'^\@|\/|:|[-–‐‑‒–—―]$'))
        self.joining_characters = kwargs.get(
            "joining_characters", R(r"^\@|\/|[-–‐‑‒–—―]$")
        )

        # Tagged chemical mentions - One B-CM tag followed by zero or more I-CM tags.
        self.cm = kwargs.get(
            "cm",
            (
                self.bcm + ZeroOrMore((self.joining_characters + self.bcm) | self.icm)
            ).add_action(join),
        )

        self.alphanumeric = kwargs.get(
            "alphanumeric",
            Every(
                [
                    R(r"^(d-)?(\d{1,2}[A-Za-z]{1,2}[′″‴‶‷⁗]?)(-d)?$"),
                    Not(self.bcm | self.icm),
                ]
            ),
        )

        self.lenient_alphanumeric = kwargs.get(
            "lenient_alphanumeric", R(r"^(d-)?(\d{1,2}[A-Za-z]{1,2}[′″‴‶‷⁗]?)(-d)?$")
        )

        self.numeric = kwargs.get(
            "numeric", Every([R(r"^\d{1,3}$"), Not(self.bcm | self.icm)])
        )
        self.lenient_numeric = kwargs.get("lenient_numeric", R(r"^\d{1,3}$"))

        self.letter_number = kwargs.get(
            "letter_number",
            Every([R(r"^(H\d)?[LSNM]{1,2}\d\d?$"), Not(self.bcm | self.icm)]),
        )
        self.lenient_letter_number = kwargs.get(
            "lenient_letter_number", R(r"^(H\d)?[LSNM]{1,2}\d\d?$")
        )

        # Blocklist to truncate chemical mentions where tags continue on incorrectly
        self.cm_blocklist = kwargs.get(
            "cm_blocklist",
            (
                W("in")
                | I("electrodes")
                | I("anodes")
                | I("specimen")
                | I("and")
                | W(":") + R(r"^m\.?p\.?$", re.I)
                | W(":") + Any() + R(r"^N\.?M\.?R\.?\(?$", re.I)
            ),
        )

        self.exclude_prefix = kwargs.get(
            "exclude_prefix",
            Start()
            + (
                lbrct + roman_numeral + rbrct + Not(hyphen)
                | (R(r"^\d{1,3}(\.\d{1,3}(\.\d{1,3}(\.\d{1,3})?)?)?$") + Not(hyphen))
                | (I("stage") | I("step") | I("section") | I("part"))
                + (self.alphanumeric | self.numeric | roman_numeral | R("^[A-Z]$"))
            ),
        )

        self.comma = kwargs.get("comma", (W(",") | T(",")).hide())
        self.colon = kwargs.get("colon", (W(":") | T(":")).hide())

        # Prefixes to include in the name
        self.include_prefix = kwargs.get(
            "include_prefix",
            Not(bcm)
            + (
                R(
                    "^(deuterated|triflated|butylated|brominated|acetylated|twisted)$",
                    re.I,
                )
                | ((W("g") | I("nano") | W("mpg")) + Optional(W("-")))
            ),
        )

        self.label_type = kwargs.get(
            "label_type",
            (
                Optional(I("reference") | I("comparative"))
                + R(
                    "^(compound|ligand|chemical|dye|derivative|complex|example|intermediate|product|formulae?|preparation|specimen)s?$",
                    re.I,
                )
            )("roles").add_action(join)
            + Optional(self.colon).hide(),
        )

        self.synthesis_of = kwargs.get(
            "synthesis_of",
            (
                (I("synthesis") | I("preparation") | I("production") | I("data"))
                + (I("of") | I("for"))
            )("roles").add_action(join),
        )

        self.to_give = kwargs.get(
            "to_give",
            (
                I("to") + (I("give") | I("yield") | I("afford"))
                | I("afforded")
                | I("affording")
                | I("yielded")
            )("roles").add_action(join),
        )

        self.label_blocklist = kwargs.get(
            "label_blocklist",
            R(r"^(wR.*|R\d|31P|[12]H|[23]D|15N|14C|[4567890]\d+|2A)$"),
        )

        self.prefixed_label = kwargs.get(
            "prefixed_label",
            Every(
                [
                    R(
                        r"^(cis|trans)-((d-)?(\d{1,2}[A-Za-z]{0,2}[′″‴‶‷⁗]?)(-d)?|[LS]\d\d?)$"
                    ),
                    Not(self.bcm | self.icm),
                ]
            ),
        )

        #: Chemical label. Very permissive - must be used in context to avoid false positives.
        self.strict_chemical_label = kwargs.get(
            "strict_chemical_label",
            Not(self.label_blocklist)
            + (
                self.alphanumeric
                | roman_numeral
                | self.letter_number
                | self.prefixed_label
            )("labels"),
        )

        self.lenient_chemical_label = kwargs.get(
            "lenient_chemical_label",
            self.numeric("labels")
            | Every([R(r"^([A-Z]\d{1,3})$"), Not(bcm | icm)])("labels")
            | self.strict_chemical_label,
        )

        self.very_lenient_chemical_label = kwargs.get(
            "very_lenient_chemical_label",
            self.lenient_numeric("labels")
            | R(r"^([A-Z]\d{1,3})$")("labels")
            | self.strict_chemical_label,
        )

        self.chemical_label = kwargs.get(
            "chemical_label",
            (
                (
                    self.label_type
                    + self.lenient_chemical_label
                    + ZeroOrMore((T("CC") | self.comma) + self.lenient_chemical_label)
                )
                | (
                    Optional(self.label_type.hide())
                    + self.strict_chemical_label
                    + ZeroOrMore((T("CC") | self.comma) + self.strict_chemical_label)
                )
            ),
        )

        #: Chemical label with a label type before
        self.chemical_label_phrase1 = kwargs.get(
            "chemical_label_phrase1",
            (
                Optional(self.synthesis_of)
                + self.label_type
                + self.lenient_chemical_label
                + ZeroOrMore((T("CC") | self.comma) + self.lenient_chemical_label)
            ),
        )
        #: Chemical label with synthesis of before
        self.chemical_label_phrase2 = kwargs.get(
            "chemical_label_phrase2",
            (
                self.synthesis_of
                + Optional(self.label_type)
                + self.lenient_chemical_label
                + ZeroOrMore((T("CC") | self.comma) + self.lenient_chemical_label)
            ),
        )
        # Chemical label with to give/afforded etc. before, and some restriction after.
        self.chemical_label_phrase3 = kwargs.get(
            "chemical_label_phrase3",
            (
                self.to_give
                + Optional(dt)
                + Optional(self.label_type)
                + self.lenient_chemical_label
                + Optional(lbrct + OneOrMore(Not(rbrct) + Any()) + rbrct).hide()
                + (End() | I("as") | self.colon | self.comma).hide()
            ),
        )

        ###### DOPED CHEMICAL LABELS ##########
        self.doped_chemical_identifier = kwargs.get(
            "doped_chemical_identifier", (W("x") | W("y"))
        )
        self.doping_value = kwargs.get("doping_value", R(r"^(\d\.?)+$"))
        self.doping_range = kwargs.get(
            "doping_range",
            (
                self.doping_value
                + (T("HYPH", tag_type="pos_tag") | I("to"))
                + self.doping_value
            ),
        )

        self.doping_label_1 = kwargs.get(
            "doping_label_1",
            (
                self.doping_value
                + R(r"^\<$")
                + self.doped_chemical_identifier
                + R(r"^\<$")
                + self.doping_value
            ),
        )
        self.doping_label_2 = kwargs.get(
            "doping_label_2",
            (
                self.doped_chemical_identifier
                + W("=")
                + OneOrMore(
                    self.doping_range
                    | self.doping_value
                    | R(r"^[,:;\.]$")
                    | I("or")
                    | I("and")
                )
            ),
        )

        self.doped_chemical_label = kwargs.get(
            "doped_chemical_label",
            Group((self.doping_label_1 | self.doping_label_2)("labels")).add_action(
                join
            ),
        )
        self.chemical_label_phrase = kwargs.get(
            "chemical_label_phrase",
            Group(
                self.doped_chemical_label
                | self.chemical_label_phrase1
                | self.chemical_label_phrase2
                | self.chemical_label_phrase3
            )("chemical_label_phrase"),
        )

        ###### INFORMAL CHEMICAL LABELS ##########
        # Identifiers typically used as informal chemical symbols
        self.informal_chemical_symbol = kwargs.get(
            "informal_chemical_symbol",
            (
                W("AE")
                | W("T")
                | W("RE")
                | (W("R") + Not(lbrct + W("Å") + rbrct))
                | W("REM")
                | W("REO")
                | W("REY")
                | W("LREE")
                | W("HREE")
                | I("Ln")
                | R(r"^B\′?$")
                | W("M")
                | W("ET")
                | W("IM2py")
                | W("NN′3")
                | W("TDAE")
                | W("X")
                | I("H2mal")
                | (W("A") + Not(lbrct + W("Å") + rbrct))
            ),
        )

        # list of chemical elements or ion symbols by type
        self.metals = kwargs.get(
            "metals",
            (
                R(
                    "^(Li|Be|Na|Mg|Al|Ca|Sc|Ti|V|Cr|K|Mn|Fe|Co|Ni|Cu|Zn|Ga|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|Fr|Ra|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Uut|Fl|Uup|Lv)$"
                )
                | R(r"^metal(s)?$")
            ),
        )
        self.transition_metals = kwargs.get(
            "transition_metals",
            (
                R(
                    "^(Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Em|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn)$"
                )
                | (I("transition") + (I("metal") | I("metals")))
            ),
        )
        self.lanthanides = kwargs.get(
            "lanthanides",
            (
                R("^(Sc|Y|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu)$")
                | R("^[Ll]anthanide(s)?$")
                | (
                    R(r"^[Rr]are\-?earth(s)?$")
                    | (
                        I("rare")
                        + Optional(T("HYPH"))
                        + R(("^earth(s)?$"))
                        + Optional(R("^metal(s)?$"))
                    )
                )
            ),
        )
        self.ion_symbol = kwargs.get(
            "ion_symbol",
            (
                R(
                    r"^(Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Ce|Ir|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Li|Be|Na|Al|As)(([2|3|4|5|6|7]?\+?)|\(I{2,7}\))?$"
                )
            ),
        )

        self.other_symbol = kwargs.get(
            "other_symbol", (W("NO3") | W("HF2") | W("ClO4") | W("BF4"))
        )

        self.informal_values = kwargs.get(
            "informal_values",
            (
                self.metals
                | self.transition_metals
                | self.lanthanides
                | self.ion_symbol
                | self.other_symbol
            ),
        )

        # Informal labelling, used for associating properties to informal compounds
        self.informal_chemical_label_1 = kwargs.get(
            "informal_chemical_label_1",
            (
                self.informal_chemical_symbol
                + W("=")
                + OneOrMore(
                    self.informal_values
                    | R(r"^[,:;\.]$")
                    | I("and")
                    | self.informal_chemical_symbol
                    | W("=")
                )
            )("label").add_action(join),
        )

        # Informal label phrase 2, "property = value for the <element> compound"
        self.informal_chemical_label_2 = kwargs.get(
            "informal_chemical_label_2",
            (
                self.informal_values
                + (I("compound") | I("sample") | I("material")).hide()
            )("label").add_action(join),
        )

        self.informal_chemical_label = kwargs.get(
            "informal_chemical_label",
            Group(
                (self.informal_chemical_label_1 | self.informal_chemical_label_2)(
                    "labels"
                )
            ).add_action(join),
        )
        self.chemical_label_phrase = kwargs.get(
            "chemical_label_phrase",
            Group(
                self.informal_chemical_label
                | self.doped_chemical_label
                | self.chemical_label_phrase1
                | self.chemical_label_phrase2
                | self.chemical_label_phrase3
            )("chemical_label_phrase"),
        )

        # TODO: "Compound 3a-c" - in parser expand out into multiple compounds
        self.element_name = kwargs.get(
            "element_name",
            R(
                "^(actinium|aluminium|aluminum|americium|antimony|argon|arsenic|astatine|barium|berkelium|beryllium|bismuth|bohrium|boron|bromine|cadmium|caesium|calcium|californium|carbon|cerium|cesium|chlorine|chromium|cobalt|copernicium|copper|curium|darmstadtium|dubnium|dysprosium|einsteinium|erbium|europium|fermium|flerovium|fluorine|francium|gadolinium|gallium|germanium|hafnium|hassium|helium|holmium|hydrargyrum|hydrogen|indium|iodine|iridium|iron|kalium|krypton|lanthanum|laIrencium|lithium|livermorium|lutetium|magnesium|manganese|meitnerium|mendelevium|mercury|molybdenum|natrium|neodymium|neon|neptunium|nickel|niobium|nitrogen|nobelium|osmium|oxygen|palladium|phosphorus|platinum|plumbum|plutonium|polonium|potassium|praseodymium|promethium|protactinium|radium|radon|rhenium|rhodium|roentgenium|rubidium|ruthenium|rutherfordium|samarium|scandium|seaborgium|selenium|silicon|silver|sodium|stannum|stibium|strontium|sulfur|tantalum|technetium|tellurium|terbium|thallium|thorium|thulium|tin|titanium|tungsten|ununoctium|ununpentium|ununseptium|ununtrium|uranium|vanadium|Iolfram|xenon|ytterbium|yttrium|zinc|zirconium)$",
                re.I,
            ),
        )

        #: Mostly unambiguous element symbols
        self.element_symbol = kwargs.get(
            "element_symbol",
            R("^(Ag|Au|Br|Cd|Cl|Cu|Fe|Gd|Ge|Hg|Mg|Pb|Pd|Pt|Ru|Sb|Si|Sn|Ti|Xe|Zn|Zr)$"),
        )

        #: Registry number patterns
        self.registry_number = kwargs.get(
            "registry_number",
            R(r"^BRN-?\d+$")
            | R(r"^CHEMBL-?\d+$")
            | R(r"^GSK-?\d{3-7}$")
            | R(r"^\[?(([1-9]\d{2,7})|([5-9]\d))-\d\d-\d\]?$")
            | (W("CAS") + OneOrMore(R(r"^(\-?(\d+)|\-)$"))).add_action(join),
        )

        #: Amino acid abbreviations. His removed, too ambiguous
        self.amino_acid = kwargs.get(
            "amino_acid",
            R(
                "^((Ala|Arg|Asn|Asp|Cys|Glu|Gln|Gly|Ile|Leu|Lys|Met|Phe|Pro|Ser|Thr|Trp|Tyr|Val)-?)+$"
            ),
        )

        self.amino_acid_name = kwargs.get(
            "amino_acid_name",
            (
                R(
                    "^(histidine|isoleucine|leucine|lysine|methionine|phenylalanine|threonine|tryptophan|valine|selenocysteine|serine|tyrosine|alanine|arginine|asparagine|cysteine|glutamine|glycine|proline)$",
                    re.I,
                )
                | I("aspartic") + I("acid")
                | I("glutamic") + I("acid")
            ),
        )

        #: Chemical formula patterns, updated to include Inorganic compound formulae
        default_formula = (
            (
                R("^C\(?\d{1,3}\)?(([HNOP]|Cl)\(?\d\d?\)?)+(\(?\d?[\+\-]\d?\)?)?$")
                | R(
                    "^(\(?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]|D[bsy]|E[rsu]|F[elmr$]|G[ade]|H[efgos]|I[rn][1-9]?|K[r(\d\.?)]|(L[airuv])|M[dgnot]|N[abdeip(\d\.?)]|O[s\d.]?|P[abdmotuOr\d]|R[abefghnuE]|S[bcegimnr(\d\.?)]|T[abehil\d]|U(u[opst])|V|Xe|Yb?|Z[nr])(\)?([\d.]+)?)+){2,}(\+[δβγ])?"
                )
                | R(
                    "^((\(?\d{2,3}\)?)?(Fe|Ti|Mg|Ru|Cd|Se)\(?(\d\d?|[IV]+)?\)?((O|Hg)\(?\d?\d?\)?)?)+(\(?\d?[\+\-]\d?\)?)?$"
                )
                | R("(NaOH|CaCl\d?\d?|EtOH|EtAc|MeOH|CF\d|C\d?\d?H\d\d?)+$")
                | R(
                    "(NO\d|BH4|Ca\(2\+\)|Ti\(0\)2|\(CH3\)2CHOH|\(CH3\)2CO|\(CH3\)2NCOH|C2H5CN|CH2ClCH2Cl|CH3C6H5|CH3CN|CH3CO2H|CH3COCH3|CH3COOH|CH3NHCOH|CH3Ph|CH3SOCH3|Cl2CH2|ClCH2CH2Cl)"
                )
                | R(
                    "^(\(CD3\)2CO|\(CDCl2\)2|C6D6|C2D5CN|CD2Cl2|CD3CN|CD3COCD3|CD3OD|CD3SOCD3|CDCl3|CH3OD|D2O|EtOD|MeOD)$"
                )
                | R(
                    "^[\[\{\(].*(NH\d|H2O|NO\d|C\d?H\d|C–H|NBu4|CF3|CD3|CO2|[bp]i?py|\(CO\)|\d,\d['′]?-|BF4|PF6|Cl\d|Fe\d|Ph\d).*[\]\}\)]$"
                )
                | R("^[\[\{\(]{1,2}(Ru|Ph|Py|Cu|Ir|Pt|Et\d).*[\]\}\)]$")
                | R("^(GABA|NO|\(\d\)H|KCl)$")
                | W("CN")
            )
            + Optional(W("+") + W("δ"))
        ).add_action(merge)
        self.formula = kwargs.get("formula", default_formula)

        default_solvent_formula = (
            W("CCl4")
            | W("(CH3)2CHOH")
            | W("(CH3)2CO")
            | W("(CH3)2NCOH")
            | W("C2H4Cl2")
            | W("C2H5CN")
            | W("C2H5OH")
            | W("C5H5N")
            | W("C6H12")
            | W("C6H14")
            | W("C6H5CH3")
            | W("C6H5Cl")
            | W("C6H6")
            | W("C7H8")
            | W("CH2Cl2")
            | W("CH2ClCH2Cl")
            | W("CH3C6H5")
            | W("CH3Cl")
            | W("CH3CN")
            | W("CH3CO2H")
            | W("CH3COCH3")
            | W("CH3COOH")
            | W("CH3NHCOH")
            | W("CH3NO2")
            | W("CH3OH")
            | W("CH3Ph")
            | W("CH3SOCH3")
            | W("CHCl2")
            | W("CHCl3")
            | W("Cl2CH2")
            | W("ClCH2CH2Cl")
            | W("CDCl3")
        )
        self.solvent_formula = kwargs.get("solvent_formula", default_solvent_formula)

        # Over-tokenized variants first, useful for matching in tables with fine tokenizer
        default_nmr_solvent = (
            I("THF") + W("-") + I("d8")
            | I("d8") + W("-") + I("THF")
            | I("acetone") + W("-") + I("d6")
            | I("d6") + W("-") + I("acetone")
            | I("chloroform") + W("-") + I("d")
            | I("d") + W("-") + I("chloroform")
            | I("methanol") + W("-") + I("d4")
            | I("d4") + W("-") + I("methanol")
            | I("pyridine") + W("-") + I("d5")
            | I("d5") + W("-") + I("pyridine")
            | I("DMSO") + W("-") + I("d6")
            | I("d6") + W("-") + I("DMSO")
            | I("dimethylsulfoxide") + W("-") + I("d6")
            | I("d6") + W("-") + I("dimethylsulfoxide")
            | W("MeOH") + W("-") + I("d4")
            | I("d4") + W("-") + W("MeOH")
            | I("benzene-d6") + W("-") + I("d6")
            | I("d6") + W("-") + I("benzene")
            | I("d2") + W("-") + I("tetrachloroethane")
            | I("tetrachloroethane") + W("-") + I("d2")
            | I("(CD3)2CO")
            | I("(CDCl2)2")
            | I("C6D6")
            | I("C2D5CN")
            | I("CD2Cl2")
            | I("CD3CN")
            | I("CD3COCD3")
            | I("CD3OD")
            | I("CD3SOCD3")
            | I("CDCl3")
            | I("CH3OD")
            | I("D2O")
            | W("EtOD")
            | W("MeOD")
            | I("THF-d8")
            | I("d8-THF")
            | I("acetone-d6")
            | I("d6-acetone")
            | I("chloroform-d")
            | I("d-chloroform")
            | I("methanol-d4")
            | I("d4-methanol")
            | I("pyridine-d5")
            | I("d5-pyridine")
            | I("DMSO-d6")
            | I("d6-DMSO")
            | I("dimethylsulfoxide-d6")
            | W("C7D8")
            | I("d6-dimethylsulfoxide")
            | W("MeOH-d4")
            | W("d4-MeOH")
            | I("DMSO")
            | I("benzene-d6")
            | I("d6-benzene")
            | I("1,1,2,2-tetrachloroethane-d2")
            | I("tetrachloroethane-d2")
            | I("d2-tetrachloroethane")
        )
        self.nmr_solvent = kwargs.get("default_nmr_solvent", default_nmr_solvent)

        #: Solvent names.
        default_other_solvent = (
            I("1-butanol")
            | I("1-butylimidazole")
            | I("1-cyclohexanol")
            | I("1-decanol")
            | I("1-heptanol")
            | I("1-hexanol")
            | I("1-methylethyl") + I("acetate")
            | I("1-octanol")
            | I("1-pentanol")
            | I("1-phenylethanol")
            | I("1-propanol")
            | I("1-undecanol")
            | I("1,1,1-trifluoroethanol")
            | I("1,1,1,3,3,3-hexafluoro-2-propanol")
            | I("1,1,1,3,3,3-hexafluoropropan-2-ol")
            | I("1,1,2-trichloroethane")
            | I("1,2-c2h4cl2")
            | I("1,2-dichloroethane")
            | I("1,2-dimethoxyethane")
            | I("1,2-dimethylbenzene")
            | I("1,2-ethanediol")
            | I("1,2,4-trichlorobenzene")
            | I("1,4-dimethylbenzene")
            | I("1,4-dioxane")
            | I("2-(n-morpholino)ethanesulfonic") + I("acid")
            | I("2-butanol")
            | I("2-butanone")
            | I("2-me-thf")
            | I("2-methf")
            | I("2-methoxy-2-methylpropane")
            | I("2-methyl") + I("tetrahydrofuran")
            | I("2-methylpentane")
            | I("2-methylpropan-1-ol")
            | I("2-methylpropan-2-ol")
            | I("2-methyltetrahydrofuran")
            | I("2-proh")
            | I("2-propanol")
            | I("2-propyl") + I("acetate")
            | I("2-pyrrolidone")
            | I("2,2,2-trifluoroethanol")
            | I("2,2,4-trimethylpentane")
            | I("2Me-THF")
            | I("2MeTHF")
            | I("3-methyl-pentane")
            | I("4-methyl-1,3-dioxolan-2-one")
            | I("acetic") + I("acid")
            | I("aceto-nitrile")
            | I("acetone")
            | I("acetonitrile")
            | I("acetononitrile")
            | I("AcOEt")
            | I("AcOH")
            | I("AgNO3")
            | I("aniline")
            | I("anisole")
            | I("benzene")
            | I("benzonitrile")
            | I("benzyl") + I("alcohol")
            | I("bromoform")
            | I("Bu2O")
            | I("Bu4NBr")
            | I("Bu4NClO4")
            | I("Bu4NPF6")
            | I("BuCN")
            | I("BuOH")
            | I("butan-1-ol")
            | I("butan-2-ol")
            | I("butan-2-one")
            | I("butane")
            | I("butanol")
            | I("butanone")
            | I("butene")
            | I("butyl") + I("acetate")
            | I("butyl") + I("acetonitrile")
            | I("butyl") + I("alcohol")
            | I("butyl") + I("amine")
            | I("butyl") + I("chloride")
            | I("butyl") + I("imidazole")
            | I("butyronitrile")
            | I("c-hexane")
            | I("carbon") + I("disulfide")
            | I("carbon") + I("tetrachloride")
            | I("chlorobenzene")
            | I("chloroform")
            | I("chloromethane")
            | I("chlorotoluene")
            | I("CHX")
            | I("cumene")
            | I("cyclohexane")
            | I("cyclohexanol")
            | I("cyclopentyl") + I("methyl") + I("ether")
            | I("DCE")
            | I("DCM")
            | I("decalin")
            | I("decan-1-ol")
            | I("decane")
            | I("decanol")
            | I("DEE")
            | I("di-isopropyl") + I("ether")
            | I("di-n-butyl") + I("ether")
            | I("di-n-hexyl") + I("ether")
            | I("dibromoethane")
            | I("dibutoxymethane")
            | I("dibutyl") + I("ether")
            | I("dichloro-methane")
            | I("dichlorobenzene")
            | I("dichloroethane")
            | I("dichloromethane")
            | I("diethoxymethane")
            | I("diethyl") + I("carbonate")
            | I("diethyl") + I("ether")
            | I("diethylamine")
            | I("diethylether")
            | I("diglyme")
            | I("dihexyl") + I("ether")
            | I("diiodomethane")
            | I("diisopropyl") + I("ether")
            | I("diisopropylamine")
            | I("dimethoxyethane")
            | I("dimethoxymethane")
            | I("dimethyl") + I("acetamide")
            | I("dimethyl") + I("acetimide")
            | I("dimethyl") + I("benzene")
            | I("dimethyl") + I("carbonate")
            | I("dimethyl") + I("ether")
            | I("dimethyl") + I("formamide")
            | I("dimethyl") + I("sulfoxide")
            | I("dimethylacetamide")
            | I("dimethylbenzene")
            | I("dimethylformamide")
            | I("dimethylformanide")
            | I("dimethylsulfoxide")
            | I("dioctyl") + I("sodium") + I("sulfosuccinate")
            | I("dioxane")
            | I("dioxolane")
            | I("dipropyl") + I("ether")
            | I("DMAc")
            | I("DMF")
            | I("DMSO")
            | I("Et2O")
            | I("EtAc")
            | I("EtAcO")
            | I("EtCN")
            | I("ethane") + I("diol")
            | I("ethane-1,2-diol")
            | I("ethanol")
            | I("ethyl") + I("(S)-2-hydroxypropanoate")
            | I("ethyl") + I("acetate")
            | I("ethyl") + I("benzoate")
            | I("ethyl") + I("formate")
            | I("ethyl") + I("lactate")
            | I("ethyl") + I("propionate")
            | I("ethylacetamide")
            | I("ethylacetate")
            | I("ethylene") + I("carbonate")
            | I("ethylene") + I("glycol")
            | I("ethyleneglycol")
            | I("ethylhexan-1-ol")
            | I("EtOAc")
            | I("EtOH")
            | I("eucalyptol")
            | I("F3-ethanol")
            | I("F3-EtOH")
            | I("formamide")
            | I("formic") + I("acid")
            | I("glacial") + I("acetic") + I("acid")
            | I("glycerol")
            | I("H2O")
            | I("H2O2")
            | I("H2SO4")
            | I("HBF4")
            | I("HCl")
            | I("HClO4")
            | I("HCO2H")
            | I("HCONH2")
            | I("heptan-1-ol")
            | I("heptane")
            | I("heptanol")
            | I("heptene")
            | I("HEX")
            | I("hexadecylamine")
            | I("hexafluoroisopropanol")
            | I("hexafluoropropanol")
            | I("hexan-1-ol")
            | I("hexane")
            | I("hexanes")
            | I("hexanol")
            | I("hexene")
            | I("hexyl") + I("ether")
            | I("HFIP")
            | I("HFP")
            | I("HNO3")
            | I("hydrochloric") + I("acid")
            | I("hydrogen") + I("peroxide")
            | I("iodobenzene")
            | I("isohexane")
            | I("isooctane")
            | I("isopropanol")
            | I("isopropyl") + I("benzene")
            | I("KBr")
            | I("LiCl")
            | I("ligroine")
            | I("limonene")
            | I("Me-THF")
            | I("Me2CO")
            | I("MeCN")
            | I("MeCO2Et")
            | I("MeNO2")
            | I("MeOH")
            | I("mesitylene")
            | I("methanamide")
            | I("methanol")
            | I("MeTHF")
            | I("methoxybenzene")
            | I("methoxyethylamine")
            | I("methyl") + I("acetamide")
            | I("methyl") + I("acetoacetate")
            | I("methyl") + I("benzene")
            | I("methyl") + I("butane")
            | I("methyl") + I("cyclohexane")
            | I("methyl") + I("ethyl") + I("ketone")
            | I("methyl") + I("formamide")
            | I("methyl") + I("formate")
            | I("methyl") + I("isobutyl") + I("ketone")
            | I("methyl") + I("laurate")
            | I("methyl") + I("methanoate")
            | I("methyl") + I("naphthalene")
            | I("methyl") + I("pentane")
            | I("methyl") + I("propan-1-ol")
            | I("methyl") + I("propan-2-ol")
            | I("methyl") + I("propionate")
            | I("methyl") + I("pyrrolidin-2-one")
            | I("methyl") + I("pyrrolidine")
            | I("methyl") + I("pyrrolidinone")
            | I("methyl") + I("t-butyl") + I("ether")
            | I("methyl") + I("tetrahydrofuran")
            | I("methyl-2-pyrrolidone")
            | I("methylbenzene")
            | I("methylcyclohexane")
            | I("methylene") + I("chloride")
            | I("methylformamide")
            | I("methyltetrahydrofuran")
            | I("MIBK")
            | I("morpholine")
            | I("monoethanolamine")
            | I("mTHF")
            | I("n-butanol")
            | I("n-butyl") + I("acetate")
            | I("n-decane")
            | I("n-heptane")
            | I("n-HEX")
            | I("n-hexane")
            | I("n-methylformamide")
            | I("n-methylpyrrolidone")
            | I("n-nonane")
            | I("n-octanol")
            | I("n-pentane")
            | I("n-propanol")
            | I("n,n-dimethylacetamide")
            | I("n,n-dimethylformamide")
            | I("n,n-DMF")
            | I("Na2SO4")
            | I("NaCl")
            | I("NaClO4")
            | I("NaHCO3")
            | I("NaOH")
            | I("nBu4NBF4")
            | I("nitric") + I("acid")
            | I("nitrobenzene")
            | I("nitromethane")
            | I("nonane")
            | I("nujol")
            | I("o-dichlorobenzene")
            | I("o-xylene")
            | I("octan-1-ol")
            | I("octane")
            | I("octanol")
            | I("octene")
            | I("ODCB")
            | I("p-xylene")
            | I("pentan-1-ol")
            | I("pentane")
            | I("pentanol")
            | I("pentanone")
            | I("pentene")
            | I("PeOH")
            | I("perchloric") + I("acid")
            | I("PhCH3")
            | I("PhCl")
            | I("PhCN")
            | I("phenoxyethanol")
            | I("phenyl") + I("acetylene")
            | I("Phenyl") + I("ethanol")
            | I("phenylamine")
            | I("phenylethanolamine")
            | I("phenylmethanol")
            | I("PhMe")
            | I("phosphate")
            | I("phosphate") + I("buffered") + I("saline")
            | I("pinane")
            | I("piperidine")
            | I("polytetrafluoroethylene")
            | I("potassium") + I("bromide")
            | I("potassium") + I("phosphate") + I("buffer")
            | I("PrCN")
            | I("PrOH")
            | I("propan-1-ol")
            | I("propan-2-ol")
            | I("propane")
            | I("propane-1,2-diol")
            | I("propane-1,2,3-triol")
            | I("propanol")
            | I("propene")
            | I("propionic") + I("acid")
            | I("propionitrile")
            | I("propyl") + I("acetate")
            | I("propyl") + I("amine")
            | I("propylene") + I("carbonate")
            | I("propylene") + I("glycol")
            | I("pyridine")
            | I("pyrrolidone")
            | I("quinoline")
            | I("silver") + I("nitrate")
            | I("SNO2")
            | I("sodium") + I("chloride")
            | I("sodium") + I("hydroxide")
            | I("sodium") + I("perchlorate")
            | I("sulfuric") + I("acid")
            | I("t-butanol")
            | I("TBABF4")
            | I("TBAF")
            | I("TBAH")
            | I("TBAOH")
            | I("TBAP")
            | I("TBAPF6")
            | I("TEAP")
            | I("TEOA")
            | I("tert-butanol")
            | I("tert-butyl") + I("alcohol")
            | I("tetrabutylammonium") + I("hexafluorophosphate")
            | I("tetrabutylammonium") + I("hydroxide")
            | I("tetrachloroethane")
            | I("tetrachloroethylene")
            | I("tetrachloromethane")
            | I("tetrafluoroethylene")
            | I("tetrahydrofuran")
            | I("tetralin")
            | I("tetramethylsilane")
            | I("tetramethylurea")
            | I("tetrapiperidine")
            | I("TFA")
            | I("TFE")
            | I("THF")
            | I("tin") + I("dioxide")
            | I("titanium") + I("dioxide")
            | I("toluene")
            | I("tri-n-butyl") + I("phosphate")
            | I("triacetate")
            | I("triacetin")
            | I("tribromomethane")
            | I("tributyl") + I("phosphate")
            | I("trichlorobenzene")
            | I("trichloroethene")
            | I("trichloromethane")
            | I("triethyl") + I("amine")
            | I("triethyl") + I("phosphate")
            | I("triethylamine")
            | I("triethanolamine")
            | I("trifluoroacetic") + I("acid")
            | I("trifluoroethanol")
            | I("trimethyl") + I("benzene")
            | I("trimethyl") + I("pentane")
            | I("tris")
            | I("undecan-1-ol")
            | I("undecanol")
            | I("valeronitrile")
            | I("water")
            | I("xylene")
            | I("xylol")
            | I("[nBu4N][BF4]")
            | I("BCN")
            | I("ACN")
            | I("BTN")
            | I("BHDC")
            | I("AOT")
            | I("DMA")
            | I("Triton X-100")
            | I("MOPS")
            | I("TX-100")
            | I("H2O") + I("+") + I("TX")
            | I("H2O-Triton X")
            | I("MES")
            | I("HDA")
            | I("PIPES")
            | I("heavy") + I("water")
            | I("IPA")
            | I("KPB")
            | I("MCH")
            | I("NPA")
            | I("NMP")
            | I("PBS")
            | I("HEPES")
            | I("SDS")
            | I("TBP")
            | I("TEA")
        )
        # Potentially problematic solvent names at the end above...
        self.other_solvent = kwargs.get("other_solvent", default_other_solvent)

        self.solvent_name_options = kwargs.get(
            "solvent_name_options",
            (self.nmr_solvent | self.solvent_formula | self.other_solvent),
        )
        self.solvent_name = kwargs.get(
            "solvent_name",
            (Optional(self.include_prefix) + self.solvent_name_options)("names")
            .add_action(join)
            .add_action(fix_whitespace),
        )
        self.chemical_name_blocklist = kwargs.get("chemical_name_blocklist", (I("mmc")))

        default_proper_chemical_name_options = Group(
            Not(self.chemical_name_blocklist)
            + Optional(self.include_prefix)
            + (
                self.formula
                ^ self.cm
                ^ self.element_name
                ^ self.element_symbol
                ^ self.registry_number
                ^ self.amino_acid
                ^ self.amino_acid_name
            )
        )
        self.proper_chemical_name_options = kwargs.get(
            "proper_chemical_name_options", default_proper_chemical_name_options
        )

        # Mixtures e.g. 30% mol MnAs + 70% mol ZnGeAs2
        self.mixture_component = kwargs.get(
            "mixture_component",
            (
                R(r"\d+(\.\d+)?")
                + W("%")
                + Optional(I("mol"))
                + self.proper_chemical_name_options
            ).add_action(join),
        )
        self.mixture_phrase = kwargs.get(
            "mixture_phrase",
            (self.mixture_component + W("+") + self.mixture_component).add_action(join)(
                "names"
            ),
        )

        self.chemical_name_options = kwargs.get(
            "chemical_name_options",
            (self.proper_chemical_name_options | self.mixture_phrase)
            + ZeroOrMore(
                self.joining_characters
                + (self.proper_chemical_name_options | self.mixture_phrase)
            ),
        )

        self.chemical_name = kwargs.get(
            "chemical_name",
            (Optional(self.include_prefix) + self.chemical_name_options)("names")
            .add_action(join)
            .add_action(fix_whitespace),
        )
        # chemical_name = cm('names').add_action(fix_whitespace)

        # Label phrase structures
        # label_type delim? label delim? chemical_name ZeroOrMore(delim cc label delim? chemical_name)

        self.likely_abbreviation = kwargs.get(
            "likely_abbreviation",
            (
                Optional(self.include_prefix + Optional(hyphen))
                + R(r"^([A-Z]{2,6}(\-[A-Z]{1,6})?|[A-Z](\-[A-Z]{2,6}))$")
            )("names")
            .add_action(join)
            .add_action(fix_whitespace),
        )

        # Lenient name match that should be used with stricter surrounding context
        self.lenient_name = kwargs.get(
            "lenient_name",
            OneOrMore(
                (self.bcm | self.icm | jj | nn | nnp | nns | hyph | cd | ls | W(","))
            )("names")
            .add_action(join)
            .add_action(fix_whitespace),
        )

        self.label_name_cem = kwargs.get(
            "label_name_cem",
            (
                (
                    self.lenient_alphanumeric
                    | self.lenient_numeric
                    | self.lenient_letter_number
                )("labels")
                + optdelim
                + self.lenient_name
            )("compound"),
        )
        self.labelled_as = kwargs.get(
            "labelled_as", (R(r"^labell?ed$") + W("as")).hide()
        )
        self.optquote = kwargs.get("optquote", Optional(quote.hide()))

        self.name_with_optional_bracketed_label = kwargs.get(
            "name_with_optional_bracketed_label",
            (
                Optional(self.synthesis_of | self.to_give)
                + self.chemical_name
                + Optional(
                    lbrct
                    + Optional(self.labelled_as + self.optquote)
                    + (
                        self.chemical_label
                        | self.lenient_chemical_label
                        | self.likely_abbreviation
                    )
                    + self.optquote
                    + rbrct
                )
            )("compound"),
        )

        self.label_before_name = kwargs.get(
            "label_before_name",
            Optional(self.synthesis_of | self.to_give)
            + self.label_type
            + optdelim
            + self.label_name_cem
            + ZeroOrMore(optdelim + cc + optdelim + self.label_name_cem),
        )
        # Very lenient name and label match, with format like "name (Compound 3)"
        self.lenient_name_with_bracketed_label = kwargs.get(
            "lenient_name_with_bracketed_label",
            (
                Start()
                + Optional(self.synthesis_of)
                + self.lenient_name
                + lbrct
                + self.label_type.hide()
                + self.lenient_chemical_label
                + rbrct
            )("compound"),
        )

        # chemical name with a comma in it that hasn't been tagged.
        self.name_with_comma_within = kwargs.get(
            "name_with_comma_within",
            Start()
            + Group(
                Optional(self.synthesis_of)
                + (
                    self.cm
                    + W(",")
                    + self.cm
                    + Not(self.bcm | self.icm)
                    + Not(I("and"))
                )("names")
                .add_action(join)
                .add_action(fix_whitespace)
            )("compound"),
        )

        # Chemical name with a doped label after
        self.name_with_doped_label = kwargs.get(
            "name_with_doped_label",
            (
                self.chemical_name
                + OneOrMore(delim | I("with") | I("for"))
                + self.doped_chemical_label
            )("compound"),
        )

        # Chemical name with an informal label after
        self.name_with_informal_label = kwargs.get(
            "name_with_informal_label",
            (
                self.chemical_name
                + Optional(R("compounds?"))
                + OneOrMore(delim | I("with") | I("for"))
                + self.informal_chemical_label
            )("compound"),
        )

        # to_give_bracketed_label = to_give + lenient_name  # TODO: Come back to this

        # TODO: Currently ensuring roles are captured from text preceding cem/cem_phrase ... abstract out the 'to_give"

        self.cem = kwargs.get(
            "cem",
            (
                self.label_before_name
                | self.name_with_informal_label
                | self.name_with_doped_label
                | self.lenient_name_with_bracketed_label
                | self.name_with_comma_within
                | self.name_with_optional_bracketed_label
            ),
        )

        self.cem_phrase = kwargs.get(
            "cem_phrase", Group(self.cem)("cem_phrase").add_action(fix_whitespace)
        )

        self.r_equals = kwargs.get(
            "r_equals",
            R("^[R]$")
            + W("=")
            + OneOrMore(
                Not(rbrct) + (self.bcm | self.icm | nn | nnp | nns | hyph | cd | ls)
            ),
        )
        self.of_table = kwargs.get(
            "of_table", (I("of") | I("in")) + Optional(dt) + I("table")
        )

        self.bracketed_after_name = kwargs.get(
            "bracketed_after_name",
            Optional(self.comma)
            + lbrct
            + Optional(self.labelled_as + self.optquote)
            + (
                self.chemical_label
                | self.lenient_chemical_label
                | self.likely_abbreviation
            )
            + self.optquote
            + Optional(Optional(self.comma) + self.r_equals | self.of_table)
            + rbrct,
        )
        self.comma_after_name = kwargs.get(
            "comma_after_name",
            self.comma
            + Optional(self.labelled_as + self.optquote)
            + (self.chemical_label | self.likely_abbreviation),
        )

        default_compound_heading_ending = (
            (
                Optional(self.comma)
                + (
                    (
                        lbrct
                        + (
                            self.chemical_label
                            | self.lenient_chemical_label
                            | self.lenient_name
                        )
                        + Optional(Optional(self.comma) + self.r_equals | self.of_table)
                        + rbrct
                    )
                    | self.chemical_label
                )
                + Optional(R(r"^[:;]$")).hide()
                | self.comma + (self.chemical_label | self.lenient_chemical_label)
            )
            + Optional(W("."))
            + End()
        )
        self.compound_heading_ending = kwargs.get(
            "compound_heading_ending", default_compound_heading_ending
        )

        # Section number, to allow at the start of a heading
        self.section_no = kwargs.get(
            "section_no",
            Every(
                [
                    Optional(I("stage") | I("step") | I("section") | I("part"))
                    + (
                        T("CD")
                        | R(r"^\d{1,3}(\.\d{1,3}(\.\d{1,3}(\.\d{1,3})?)?)?$")
                        | (Optional(lbrct) + roman_numeral + rbrct)
                    ),
                    Not(self.bcm | self.icm),
                ]
            ),
        )

        default_compound_heading_style1 = (
            Start()
            + Optional(self.section_no.hide())
            + Optional(self.synthesis_of)
            + OneOrMore(
                Not(self.compound_heading_ending)
                + (
                    self.bcm
                    | self.icm
                    | jj
                    | nn
                    | nnp
                    | nns
                    | hyph
                    | sym
                    | cd
                    | ls
                    | W(",")
                )
            )("names")
            .add_action(join)
            .add_action(fix_whitespace)
            + self.compound_heading_ending
            + End()
        )
        self.compound_heading_style1 = kwargs.get(
            "compound_heading_style1", default_compound_heading_style1
        )
        self.compound_heading_style2 = kwargs.get(
            "compound_heading_style2",
            self.chemical_name + Optional(self.bracketed_after_name),
        )
        self.compound_heading_style3 = kwargs.get(
            "compound_heading_style2",
            self.synthesis_of
            + (self.lenient_name | self.chemical_name)
            + Optional(self.bracketed_after_name | self.comma_after_name),
        )  # Possibly redundant?
        self.compound_heading_style4 = kwargs.get(
            "compound_heading_style4",
            self.label_type
            + self.very_lenient_chemical_label
            + ZeroOrMore((T("CC") | self.comma) + self.lenient_chemical_label)
            + (self.lenient_name | self.chemical_name)
            + Optional(self.bracketed_after_name | self.comma_after_name),
        )
        self.compound_heading_style5 = kwargs.get(
            "compound_heading_style5", self.informal_chemical_label
        )
        self.compound_heading_style6 = kwargs.get(
            "compound_heading_style6", self.doped_chemical_label
        )
        # TODO: Capture label type in output

        self.compound_heading_phrase = kwargs.get(
            "compound_heading_phrase",
            Group(
                self.compound_heading_style6
                | self.compound_heading_style5
                | self.compound_heading_style1
                | self.compound_heading_style2
                | self.compound_heading_style3
                | self.compound_heading_style4
                | self.chemical_label
            )("compound"),
        )

        default_names_only = Group(
            (
                self.solvent_name
                | self.chemical_name
                | self.likely_abbreviation
                | (
                    Start()
                    + Group(
                        Optional(self.synthesis_of)
                        + (
                            self.cm
                            + W(",")
                            + self.cm
                            + Not(self.bcm | self.icm)
                            + Not(I("and"))
                        )
                        .add_action(join)
                        .add_action(fix_whitespace)
                    )
                )
            )
        )("compound")
        self.names_only = kwargs.get("names_only", default_names_only)

        self.labels_only = kwargs.get(
            "labels_only",
            Group(
                (
                    self.doped_chemical_label
                    | self.informal_chemical_label
                    | self.numeric
                    | Every([R(r"^([A-Z]\d{1,3})$"), Not(self.bcm | self.icm)])
                    | self.strict_chemical_label
                )
            )("compound"),
        )

        self.roles_only = kwargs.get(
            "roles_only",
            Group((self.label_type | self.synthesis_of | self.to_give))("compound"),
        )

    @classmethod
    def with_default_configuration(cls):
        if cls._default_cem_factory is None:
            cls._default_cem_factory = cls()
        return cls._default_cem_factory
