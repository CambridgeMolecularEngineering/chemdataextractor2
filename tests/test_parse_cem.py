# -*- coding: utf-8 -*-
"""
test_parse_cem
~~~~~~~~~~~~~~



"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest
from lxml import etree

from chemdataextractor.doc.document import Document
from chemdataextractor.doc.text import Sentence, Heading, Paragraph
from chemdataextractor.parse.cem import cem_phrase, compound_heading_phrase, chemical_label_phrase
from chemdataextractor.model.model import Compound, MeltingPoint

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestParseCem(unittest.TestCase):

    maxDiff = None

    def do_parse(self, input, expected):
        s = Sentence(input)
        log.debug(s)
        log.debug(s.tokens)
        results = []
        for i, r in enumerate(cem_phrase.scan(s.tokens)):
            log.debug(etree.tostring(r[0], pretty_print=True, encoding='unicode'))
            results.append(etree.tostring(r[0], encoding='unicode'))
        self.assertEqual(expected, results)

    def test_simple(self):
        s = 'Such as 2,4,6-trinitrotoluene with acetone.'
        expected = [
            '<cem_phrase><compound><names>2,4,6-trinitrotoluene</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>acetone</names></compound></cem_phrase>'
        ]
        self.do_parse(s, expected)

    def test_without_tags(self):
        """Test on input where the CEM tagger has missed some obvious chemical entities."""
        tokens = [(u'A', u'DT'), (u'sample', u'NN'), (u'of', u'IN'), (u'aspartic', u'NN'), (u'acid', u'NN'), (u'with', u'IN'), (u'Ala-Arg-Val', u'NN'), (u'.', u'.')]
        expected = [
            '<cem_phrase><compound><names>aspartic acid</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>Ala-Arg-Val</names></compound></cem_phrase>'
        ]
        results = []
        for i, r in enumerate(cem_phrase.scan(tokens)):
            log.debug(etree.tostring(r[0], pretty_print=True, encoding='unicode'))
            results.append(etree.tostring(r[0], encoding='unicode'))
        self.assertEqual(expected, results)

    def test_no_doi(self):
        s = 'DOI: 10.1039/C5TC02077H (Paper) J. Mater. Chem. C, 2015, 3, 10177-10187'
        expected = []
        self.do_parse(s, expected)

    def test_no_issn(self):
        s = '1234-567X'
        expected = []
        self.do_parse(s, expected)

    def test_no_email(self):
        s = 'a.test.account@gmail.com'
        expected = []
        self.do_parse(s, expected)

    def test_comma_separated(self):
        s = '4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester (Compound 67)'
        expected = ['<cem_phrase><compound><names>4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester</names><labels>67</labels></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_comma_separated_colon(self):
        s = '4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester (Compound 67): mp 163-164° C.'
        expected = ['<cem_phrase><compound><names>4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester</names><labels>67</labels></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_high_label_colon(self):
        s = '4-Amino-3-chloro-6-[2,4-dichloro-3-(1-fluoro-1-methylethylphenyl)pyridine-3-carboxylic acid (Compound 127): mp >250° C.'
        expected = ['<cem_phrase><compound><names>4-Amino-3-chloro-6-[2,4-dichloro-3-(1-fluoro-1-methylethylphenyl)pyridine-3-carboxylic acid</names><labels>127</labels></compound></cem_phrase>']
        self.do_parse(s, expected)

    # def test_incorrect_mp_tagged(self):
    #     s = '4-Acetylamino-3-chloro-6-(4-cyano-2,6-difluoro-3-methoxyphenyl)pyridine-2-carboxylic acid, methyl ester: mp 146-147° C.'
    #     expected = ['<cem_phrase><compound><names>4-Acetylamino-3-chloro-6-(4-cyano-2,6-difluoro-3-methoxyphenyl)pyridine-2-carboxylic acid, methyl ester</names></compound></cem_phrase>']
    #     self.do_parse(s, expected)

    def test_incorrect_nmr_tagged(self):
        s = '1-Bromo-2,4-dichloro-3-(methylthio)benzene: 1H NMR (CDCl3): δ 7.52 (d, 1H), 7.25 (d, 1H), 2.46 (s, 3H).'
        expected = [
            '<cem_phrase><compound><names>1-Bromo-2,4-dichloro-3-(methylthio)benzene</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>1H</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>CDCl3</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>3H</names></compound></cem_phrase>',
        ]
        self.do_parse(s, expected)

    def test_nmr_after(self):
        s = '2-(4-Chloro-2-fluoro-3-difluoromethylphenyl)-[1,3,2]-dioxaborinane 1H NMR (CDCl3):'
        expected = [
            '<cem_phrase><compound><names>2-(4-Chloro-2-fluoro-3-difluoromethylphenyl)-[1,3,2]-dioxaborinane</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>1H</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>CDCl3</names></compound></cem_phrase>'
        ]
        self.do_parse(s, expected)

    def test_no_panel_label(self):
        """Test figure panels aren't recognised as labels."""
        s = 'FIG. 2. UV-Visible Spectral of 2 in Various Solvents. Solvents CHCl3 (A); toluene (B), ethanol (C), H2O/CrEl (D).'
        expected = [
            '<cem_phrase><compound><names>CHCl3</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>toluene</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>ethanol</names></compound></cem_phrase>',
            '<cem_phrase><compound><names>H2O/CrEl</names></compound></cem_phrase>',
        ]
        self.do_parse(s, expected)

    def test_no_fig(self):
        """Test Fig label isn't recognised."""
        s = 'FIG. 2'
        expected = []
        self.do_parse(s, expected)

    def test_no_patent_num(self):
        """Test patent number isn't recognised."""
        s = 'Similar compounds are known from EP 0 250 999 and EP 0 137 389.'
        expected = []
        self.do_parse(s, expected)

    def test_no_trailing_semicolon(self):
        """Test trailing semicolon is stripped."""
        s = '2-[1-(3-Bromo-phenyl)-1H-imidazol-4-yl]-benzooxazole;'
        expected = ['<cem_phrase><compound><names>2-[1-(3-Bromo-phenyl)-1H-imidazol-4-yl]-benzooxazole</names></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_section_numeral(self):
        """Test section isn't included in name."""
        s = '(vii) 1,3,5-Tricyano-2,4,6-tris[4-(p-diphenylaminostyryl)styryl]benzene (3j)'
        expected = ['<cem_phrase><compound><names>1,3,5-Tricyano-2,4,6-tris[4-(p-diphenylaminostyryl)styryl]benzene</names><labels>3j</labels></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_section_numeral2(self):
        """Test section isn't included in name."""
        s = '(i) 1,3,5-Tricyano-2,4,6-tris(2-dimethylaminovinyl)benzene (1f)'
        expected = ['<cem_phrase><compound><names>1,3,5-Tricyano-2,4,6-tris(2-dimethylaminovinyl)benzene</names><labels>1f</labels></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_acs_journals(self):
        """"""
        s = 'ACS journals'
        expected = []
        self.do_parse(s, expected)

    def test_to_yield_phrase(self):
        """Test role is correct in to yield phrase"""
        s = 'The crude product was recrystallized from ethanol to yield 5-hydroxy-2-methyl-1,4-dihydroanthracene-9,10-dione as golden-brown needles (0.9980 g, 75% yield).'
        expected = [
            '<cem_phrase><compound><names>ethanol</names></compound></cem_phrase>',
            '<cem_phrase><compound><roles>to yield</roles><names>5-hydroxy-2-methyl-1,4-dihydroanthracene-9,10-dione</names></compound></cem_phrase>'
        ]
        self.do_parse(s, expected)

    def test_inorganic_chemical_formula_1(self):
        s = 'Y2Ba2Cu4O7'
        expected = ['<cem_phrase><compound><names>Y2Ba2Cu4O7</names></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_inorganic_chemical_formula_2(self):
        s = 'La0.7Sr0.3MnO3'
        expected = ['<cem_phrase><compound><names>La0.7Sr0.3MnO3</names></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_inorganic_chemical_formula_3(self):
        s = 'La1+xSrxMnO3'
        expected = ['<cem_phrase><compound><names>La1 + xSrxMnO3</names></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_inorganic_chemical_formula_4(self):
        s = '(La,Sr)MnO3'
        expected = ['<cem_phrase><compound><names>(La, Sr)MnO3</names></compound></cem_phrase>']
        self.do_parse(s, expected)

    def test_inorganic_chemical_formula_5(self):
        s = 'Ba0.55K0.45As2Fe2+δ'
        expected = ['<cem_phrase><compound><names>Ba0.55K0.45As2Fe2+δ</names></compound></cem_phrase>']
        self.do_parse(s, expected)


class TestParseCemHeading(unittest.TestCase):

    maxDiff = None

    def do_parse(self, input, expected):
        s = Sentence(input)
        s.models = [Compound]
        log.debug(s)
        log.debug(s.tokens)
        results = []
        for i, r in enumerate(compound_heading_phrase.scan(s.tokens)):
            log.debug(etree.tostring(r[0], pretty_print=True, encoding='unicode'))
            results.append(etree.tostring(r[0], encoding='unicode'))
        self.assertEqual(expected, results)

    def test_preparation_of(self):
        s = 'Preparation of 4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester (Compound 41)'
        expected = ['<compound><roles>Preparation of</roles><names>4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester</names><roles>Compound</roles><labels>41</labels></compound>']
        self.do_parse(s, expected)

    def test_section_number(self):
        s = '53. Preparation of 4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester (Compound 41)'
        expected = [
            '<compound><roles>Preparation of</roles><names>4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester</names><roles>Compound</roles><labels>41</labels></compound>']
        self.do_parse(s, expected)

    def test_section_number2(self):
        s = '50. Preparation of 4-acetylamino-3-chloro-6-iodopyridine-2-carboxylic acid, methyl ester'
        expected = ['<compound><roles>Preparation of</roles><names>4-acetylamino-3-chloro-6-iodopyridine-2-carboxylic acid, methyl ester</names></compound>']
        self.do_parse(s, expected)

    # def test_just_name(self):
    #     s = '1-[2-[8-(2,6-Difluorophenyl-4-(4-fluoro-2-methylphenyl)-7-oxo-7,8-dihydro-pyrido[2,3-]pyrimidin-2-ylamino]ethyl]-3-cyclohexylurea'
    #     expected = ['']
    #     self.do_parse(s, expected)

    def test_example_name(self):
        s = 'EXAMPLE 436 N-tert-Butyl-3-[6′-methyl-4′-(4-trifluoromethoxy-phenyl)-[2,2′]bipyridinyl-6-yl]-benzenesulfonamide'
        expected = ['<compound><roles>EXAMPLE</roles><labels>436</labels><names>N-tert-Butyl-3-[6 \u2032-methyl-4 \u2032-(4-trifluoromethoxy-phenyl)-[2,2 \u2032]bipyridinyl-6-yl]-benzenesulfonamide</names></compound>']
        self.do_parse(s, expected)

    def test_label_list(self):
        s = 'Compounds 8a, 8b, 8c: pH Responsive Dye Conjugates'
        expected = ['<compound><roles>Compounds</roles><labels>8a</labels><labels>8b</labels><labels>8c</labels></compound>']
        self.do_parse(s, expected)

    def test_compound_label(self):
        s = 'Compound 6'
        expected = ['<compound><roles>Compound</roles><labels>6</labels></compound>']
        self.do_parse(s, expected)


class TestParseHeading(unittest.TestCase):

    maxDiff = None

    def do_parse(self, input, expected):
        s = Heading(input)
        s.models = [Compound]
        log.debug(s)
        log.debug(s.tokens)
        results = [r.serialize() for r in s.records]
        log.debug(results)
        log.debug(expected)
        log.debug(results == expected)
        self.assertEqual(expected, results)

    def test_preparation_of(self):
        s = 'Preparation of 4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester (Compound 41)'
        expected = [
            {'Compound': {'labels': ['41'], 'names': ['4-Amino-3-chloro-6-(2,3,4-trifluorophenyl)pyridine-2-carboxylic acid, methyl ester'], 'roles': ['compound', 'product']}}
        ]
        self.do_parse(s, expected)

    def test_background(self):
        """Ensure uppercase heading isn't recognised (as a likely abbreviation)"""
        s = 'BACKGROUND'
        expected = []
        self.do_parse(s, expected)

    def test_background_art(self):
        """Ensure uppercase heading isn't recognised (as a likely abbreviation)"""
        s = 'BACKGROUND ART'
        expected = []
        self.do_parse(s, expected)

    def test_label_list(self):
        s = 'Compounds 8a, 8b, 8c: pH Responsive Dye Conjugates'
        expected = [{'Compound': {'labels': ['8a'], 'roles': ['compounds']}},
         {'Compound': {'labels': ['8b'], 'roles': ['compounds']}},
         {'Compound': {'labels': ['8c'], 'roles': ['compounds']}}]
        self.do_parse(s, expected)

    def test_name_label(self):
        s = '4-[4-(4-[5-[5-(4-Hydroxyphenyl)-3-phenyl-1H-pyrrol-2-ylimino]-4-phenyl-5H-pyrrol-2-yl]-phenoxymethyl)-[1,2,3]triazol-1-yl]butyric acid (8b)'
        expected = [{'Compound': {'labels': ['8b'], 'names': ['4-[4-(4-[5-[5-(4-Hydroxyphenyl)-3-phenyl-1H-pyrrol-2-ylimino]-4-phenyl-5H-pyrrol-2-yl]-phenoxymethyl)-[1,2,3]triazol-1-yl]butyric acid']}}]
        self.do_parse(s, expected)

    def test_cas(self):
        """"""
        s = 'CAS 1242336-53-3'
        expected = [{'Compound': {'names': [u'CAS 1242336-53-3']}}]
        self.do_parse(s, expected)

    def test_section_numeral(self):
        """"""
        s = '(vii) 1,3,5-Tricyano-2,4,6-tris[4-(p-diphenylaminostyryl)styryl]benzene (3j)'
        expected = [{'Compound': {'labels': [u'3j'], 'names': [u'1,3,5-Tricyano-2,4,6-tris[4-(p-diphenylaminostyryl)styryl]benzene']}}]
        self.do_parse(s, expected)

    def test_fluorescent_nano_beads(self):
        """"""
        s = 'Fluorescent Nano-Beads'
        expected = []
        self.do_parse(s, expected)

    def test_test(self):
        """"""
        s = 'Test 2'
        expected = []
        self.do_parse(s, expected)

    def test_example_colon(self):
        """"""
        s = 'EXAMPLE: 3'
        expected = [{'Compound': {'labels': [u'3'], 'roles': ['example']}}]
        self.do_parse(s, expected)

    def test_comparative_example(self):
        """"""
        s = 'Comparative example 14'
        expected = [{'Compound': {'labels': [u'14'], 'roles': ['comparative example']}}]
        self.do_parse(s, expected)

    def test_reference_example(self):
        """"""
        s = 'Reference example IV'
        expected = [{'Compound': {'labels': [u'IV'], 'roles': ['reference example']}}]
        self.do_parse(s, expected)

    def test_step(self):
        """Test synthesis step."""
        s = 'Step B: 7-Fluoro-4H-1,2,4-benzothiadiazine 1,1-dioxide'
        expected = [{'Compound': {'names': [u'7-Fluoro-4H-1,2,4-benzothiadiazine 1,1-dioxide']}}]
        self.do_parse(s, expected)

    def test_label_14(self):
        """"""
        s = '1-(3,4-Dibenzyloxycinnamoyl)-3,4′-dibenzyloxyresveratrol (14):'
        expected = [{'Compound': {'labels': [u'14'], 'names': [u'1-(3,4-Dibenzyloxycinnamoyl)-3,4 \u2032-dibenzyloxyresveratrol']}}]
        self.do_parse(s, expected)

    def test_section_decimal(self):
        """"""
        s = '3.2: [3-(2-p-Tolylimidazo[1,2-a]pyridin-6-yl)phenyl]methanol'
        expected = [{'Compound': {'names': [u'[3-(2-p-Tolylimidazo[1,2-a]pyridin-6-yl)phenyl]methanol']}}]
        self.do_parse(s, expected)

    def test_prep_label(self):
        """"""
        s = 'Preparation of (E)-1-(4-(benzyloxy)phenyl)-2-(3,5-bis(benzyloxy)phenyl)ethene (I)'
        expected = [{'Compound': {'labels': [u'I'], 'names': [u'(E)-1-(4-(benzyloxy)phenyl)-2-(3,5-bis(benzyloxy)phenyl)ethene'], 'roles': ['product']}}]
        self.do_parse(s, expected)

    def test_comma_label(self):
        """"""
        s = 'Preparation of 2-(10-bromoanthracene-9-yl)thiophene, 11'
        expected = [{'Compound': {'labels': [u'11'], 'names': [u'2-(10-bromoanthracene-9-yl)thiophene'], 'roles': [u'product']}}]
        self.do_parse(s, expected)



class TestParseLabelPhrase(unittest.TestCase):

    maxDiff = None

    def do_parse(self, input, expected):
        s = Sentence(input)
        s.models = [Compound]
        log.debug(s)
        log.debug(s.tokens)
        results = []
        for i, r in enumerate(chemical_label_phrase.scan(s.tokens)):
            log.debug(etree.tostring(r[0], pretty_print=True, encoding='unicode'))
            results.append(etree.tostring(r[0], encoding='unicode'))
        self.assertEqual(expected, results)

    def test_synthesis_of_compound(self):
        s = 'Synthesis of Compound 23.'
        expected = ['<chemical_label_phrase><roles>Synthesis of</roles><roles>Compound</roles><labels>23</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_synthesis_of(self):
        s = 'The synthesis of 4a is shown below.'
        expected = ['<chemical_label_phrase><roles>synthesis of</roles><labels>4a</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_compound(self):
        s = 'This shows that Compound IV is the best.'
        expected = ['<chemical_label_phrase><roles>Compound</roles><labels>IV</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_synthesis_of2(self):
        """Test synthesis of \d on its own."""
        s = 'Synthesis of 10.'
        expected = ['<chemical_label_phrase><roles>Synthesis of</roles><labels>10</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_to_give_phrase(self):
        """Test to give phrase."""
        s = 'residue chromatographed (silica, MeOH/CH2Cl2, 2:8) to give 10 (93 mg, 57%) as a dark green solid.'
        expected = ['<chemical_label_phrase><roles>to give</roles><labels>10</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_afforded_phrase(self):
        """Test afforded phrase."""
        s = 'Subsequent chromatography (silica, CH2Cl2/MeOH, 7:3) afforded 12 as green solid (4 mg, 63%).'
        expected = ['<chemical_label_phrase><roles>afforded</roles><labels>12</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_doped_label_1(self):
        s = 'La1-xSrxMnO3 with x = 0.1, 0.2, 0.3 and 0.4'
        expected = ['<chemical_label_phrase><labels>x = 0.1 , 0.2 , 0.3 and 0.4</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_doped_label_2(self):
        s = 'La1-xSrxMnO3 (x = 0.1-0.5)'
        expected = ['<chemical_label_phrase><labels>x = 0.1 - 0.5</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_doped_label_3(self):
        s = 'La1-ySryMnO3 (y = 0 to 1)'
        expected = ['<chemical_label_phrase><labels>y = 0 to 1</labels></chemical_label_phrase>']
        self.do_parse(s, expected)

    def test_informal_label_1(self):
        s = 'LNMnO3 with LN = Ho, Dy, La and Tb'
        expected = ['<chemical_label_phrase><labels>LN = Ho , Dy , La and Tb</labels></chemical_label_phrase>']
        self.do_parse(s, expected)


class TestParseDocument(unittest.TestCase):

    maxDiff = None

    def test_consecutive_headings(self):
        d = Document(
            Heading('Preparation of 2-Amino-3-methoxy-5-chloropyridine'),
            Heading('Example 3'),
            Paragraph('The solid is suspended in hexanes, stirred and filtered to give the product as a bright yellow solid. (MP 93-94\xc2\xb0 C.).')
        )
        d.models = [Compound]
        results = [r.serialize() for r in d.records]
        self.assertEqual(results, [{'Compound': {'names': [u'hexanes']}},
                                   {'Compound': {'labels': [u'3'], 'names': [u'2-Amino-3-methoxy-5-chloropyridine'], 'roles': ['example', 'product']}}])

    # Edited by ti250 (8/11/2018)
    # Changed format of the expected results for new-style models.
    def test_consecutive_headings2(self):
        d = Document(
            Heading('Example-3'),
            Heading('Preparation of 5-Bromo-6-pentadecyl-2-hydroxybenzoic acid (DBAA)'),
            Paragraph('The product had a melting point of 70-75° C. and has structural formula VII.')
        )
        d.models = [Compound, MeltingPoint]
        results = [r.serialize() for r in d.records]
        print(results)
        self.assertCountEqual(results, [
            {'MeltingPoint': {'units': u'Celsius^(1.0)', 'value': [70.0, 75.0], 'raw_value': '70-75',
                              'raw_units': '\xb0C',
                              'compound': {'Compound': {'labels': [u'VII'], 'roles': ['formula']}}}},
            {'Compound': {'names': [u'5-Bromo-6-pentadecyl-2-hydroxybenzoic acid', u'DBAA'], 'roles': ['product']}},
            {'Compound': {'labels': [u'VII'], 'roles': [u'formula']}}
        ])  # example-3?


if __name__ == '__main__':
    unittest.main()
