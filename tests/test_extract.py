# -*- coding: utf-8 -*-
"""
test_extract
~~~~~~~~~~~~

Test data extraction on small document examples.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest

from chemdataextractor import Document
from chemdataextractor.doc import Heading, Paragraph
from chemdataextractor.model import *

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


unittest.util._MAX_LENGTH = 2000


class TestExtract(unittest.TestCase):

    maxDiff = None

    def test_melting_point_heading_salt(self):
        """Test extraction of melting point from a heading and paragraphs. Example taken from patent US06840965B2."""
        d = Document(
            Heading('D. Synthesis of 4-Amino-2-(3-thienyl)phenol Hydrochloride'),
            Paragraph('3 g (13.5 mmoles) of 4-nitro-2-(3-thienyl)phenol was dissolved in 40 mL of ethanol and hydrogenated at 25° C. in the presence of 600 mg of a palladium—active carbon catalyst (10%). After the theoretically required amount of hydrogen had been absorbed, the catalyst was filtered off. Following concentration in a rotary evaporator, the reaction mixture was poured onto 20 mL of cold diethyl ether. The precipitated product was filtered off and dried.'),
            Paragraph('This gave 1.95 g (75% of the theoretical) of 4-amino-2-(3-thienyl)phenol hydrochloride with a melting point of 130-132° C.'))
        d.models = [Compound, MeltingPoint]
        expected = [
             {'Compound': {'names': ['4-nitro-2-(3-thienyl)phenol']}},
             {'Compound': {'names': ['ethanol']}},
             {'Compound': {'names': ['palladium']}},
             {'Compound': {'names': ['carbon']}},
             {'Compound': {'names': ['hydrogen']}},
             {'Compound': {'names': ['diethyl ether']}},
             {'Compound': {'names': ['4-Amino-2-(3-thienyl)phenol Hydrochloride',
                                     '4-amino-2-(3-thienyl)phenol hydrochloride'],
                           'roles': ['product']}},
             {'MeltingPoint': {'compound': {'Compound': {'names': ['4-Amino-2-(3-thienyl)phenol '
                                                                   'Hydrochloride',
                                                                   '4-amino-2-(3-thienyl)phenol '
                                                                   'hydrochloride'],
                                                         'roles': ['product']}},
                               'raw_units': '°C',
                               'raw_value': '130-132',
                               'units': 'Celsius^(1.0)',
                               'value': [130.0, 132.0]}}
        ]
        self.assertCountEqual(expected, d.records.serialize())

    def test_parse_control_character(self):
        """Test control character in text is handled correctly."""
        # The parser doesn't like controls because it uses LXML model so must be XML compatible.
        d = Document(Paragraph('Yielding 2,4,6-trinitrotoluene,\n m.p. 20 \x0eC.'))
        d.models = [Compound]
        expected = [{'Compound': {'names': ['2,4,6-trinitrotoluene']}}]
        self.assertCountEqual(expected, d.records.serialize())

    def test_merge_contextual(self):
        """
        Test merging in of extracted apparatus data into MeltingPoint when it's contextual.
        Example is an edited excerpt from patent US06840965B2 with added in things for apparatus.
        """
        d = Document(
            Heading('D. Synthesis of 4-Amino-2-(3-thienyl)phenol Hydrochloride'),
            Paragraph('3 g (13.5 mmoles) of 4-nitro-2-(3-thienyl)phenol was dissolved in 40 mL of ethanol and hydrogenated at 25° C. in the presence of 600 mg of a palladium—active carbon catalyst (10%). After the theoretically required amount of hydrogen had been absorbed, the catalyst was filtered off. Following concentration in a rotary evaporator, the reaction mixture was poured onto 20 mL of cold diethyl ether. The precipitated product was filtered off and dried.'),
            Paragraph('This gave 1.95 g (75% of the theoretical) of 4-amino-2-(3-thienyl)phenol hydrochloride with a melting point of 130-132° C as measured with the HORIBA F-7000 spectrofluorimeter.'))
        d.models = [Compound, MeltingPoint, Apparatus]
        expected = [
             {'Compound': {'names': ['4-nitro-2-(3-thienyl)phenol']}},
             {'Compound': {'names': ['ethanol']}},
             {'Compound': {'names': ['palladium']}},
             {'Compound': {'names': ['carbon']}},
             {'Compound': {'names': ['hydrogen']}},
             {'Compound': {'names': ['diethyl ether']}},
             {'Compound': {'names': ['4-Amino-2-(3-thienyl)phenol Hydrochloride',
                                     '4-amino-2-(3-thienyl)phenol hydrochloride'],
                           'roles': ['product']}},
             {'Apparatus': {'name': 'HORIBA F-7000 spectrofluorimeter'}},
             {'MeltingPoint': {'apparatus': {'Apparatus': {'name': 'HORIBA F-7000 '
                                                                   'spectrofluorimeter'}},
                               'compound': {'Compound': {'names': ['4-Amino-2-(3-thienyl)phenol '
                                                                   'Hydrochloride',
                                                                   '4-amino-2-(3-thienyl)phenol '
                                                                   'hydrochloride'],
                                                         'roles': ['product']}},
                               'raw_units': '°C',
                               'raw_value': '130-132',
                               'units': 'Celsius^(1.0)',
                               'value': [130.0, 132.0]}}
        ]
        self.assertCountEqual(expected, d.records.serialize())

    def test_merge_contextual_2(self):
        """Test merging a compound's full name in to another compound record containing its label."""
        p1 = Paragraph("The structure of 4-amino-2-(3-thienyl)phenol hydrochloride (1a) is shown in Fig. 1.")
        p1.models = [MeltingPoint]
        p2 = Paragraph("1a has a melting point of 130-132° C.")
        p2.models = [MeltingPoint]
        r1 = p1.records[0]
        r2 = p2.records[0]
        r2.merge_contextual(r1)
        self.assertTrue(r2._compatible(r1))



if __name__ == '__main__':
    unittest.main()
