# -*- coding: utf-8 -*-
"""
chemdataextractor.tests.test_reader_els.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test reader for Elsevier.

.. codeauthor:: Juraj Mavračić <jm2111@cam.ac.uk>
.. codeauthor:: Callum Court <cc889@cam.ac.uk>

"""

import unittest
import logging
import io
import os

from chemdataextractor import Document
from chemdataextractor.reader.elsevier import ElsevierXmlReader

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class TestElsXMLReader(unittest.TestCase):

    maxDiff = None

    def test_detect(self):
        """Test RscXMLReader can detect an RSC document."""
        r = ElsevierXmlReader()
        fname = 'j.jnoncrysol.2017.07.006.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'elsevier', fname), 'rb')
        content = f.read()
        f.close()
        self.assertEqual(r.detect(content, fname=fname), True)

    def test_direct_usage(self):
        """Test RscXMLReader used directly to parse file."""
        r = ElsevierXmlReader()
        fname = 'j.jnoncrysol.2017.07.006.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'elsevier', fname), 'rb')
        content = f.read()
        d = r.readstring(content)
        f.close()
        self.assertEqual(len(d.elements), 198)

    def test_document_usage(self):
        """Test XMLReader used via Document.from_file."""
        fname = 'j.jnoncrysol.2017.07.006.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'elsevier', fname), 'rb')
        d = Document.from_file(f, readers=[ElsevierXmlReader()])
        self.assertEqual(len(d.elements), 198)

    def test_metadata(self):
        """Test that the retrieved metadata is correct
        """
        fname = 'j.jnoncrysol.2017.07.006.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'elsevier', fname), 'rb')
        d = Document.from_file(f, readers=[ElsevierXmlReader()])
        meta = d.metadata.serialize()
        expected = {'MetaData': {'title': 'STRUCTURALELECTROCHEMICALCHARACTERIZATIONCA50MG20CU25ZN5AMORPHOUSALLOY', 'authors': ['BABILAS'], 'publisher': '© 2017 Elsevier B.V. All rights reserved.', 'journal': 'Journal of Non-Crystalline Solids', 'date': '2017-07-14', 'volume': '471', 'issue': '0022-3093', 'firstpage': '467', 'lastpage': '475', 'doi': '10.1016/j.jnoncrysol.2017.07.006', 'html_url': 'https://sciencedirect.com/science/article/pii/S0022309317303496'}}
        self.assertDictEqual(meta, expected)

    def test_parse_table_rows(self):
        """Test that the elsevier colspan and rowspan work correctly
        """
        fname = 'j.jnoncrysol.2018.02.024.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'elsevier', fname), 'rb')
        d = Document.from_file(f, readers=[ElsevierXmlReader()])
        table_1 = d.tables[0].tde_table.category_table
        expected = [['1500', ['Tm (K)'], ['MD simulations with ReaxFF potential [ ]']], ['1750', ['Tm (K)'], ['MC simulations with ARK parameters [ ]']], ['1775', ['Tm (K)'], ['MD simulations with SW potential [ ]']], ['2.36\u202f×\u202f1011', ['γC (K/s)'], ['MD simulations with ReaxFF potential [ ]']], ['4.25\u202f×\u202f1011', ['γC (K/s)'], ['MC simulations with ARK parameters [ ]']], ['4.95\u202f×\u202f1011', ['γC (K/s)'], ['MD simulations with SW potential [ ]']]]
        self.assertEqual(table_1, expected)





if __name__ == '__main__':
    unittest.main()
