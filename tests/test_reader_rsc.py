# -*- coding: utf-8 -*-
"""
test_reader_rsc
~~~~~~~~~~~~~~~

Test RSC reader.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import io
import logging
import os
import unittest

from chemdataextractor import Document
from chemdataextractor.reader import RscHtmlReader


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestRscHtmlReader(unittest.TestCase):

    maxDiff = None

    def test_detect(self):
        """Test RscHtmlReader can detect an RSC document."""
        r = RscHtmlReader()
        fname = '10.1039_C6OB02074G.html'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'rsc', fname), 'rb')
        content = f.read()
        self.assertEqual(r.detect(content, fname=fname), True)

    def test_direct_usage(self):
        """Test RscHtmlReader used directly to parse file."""
        r = RscHtmlReader()
        fname = '10.1039_C6OB02074G.html'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'rsc', fname), 'rb')
        content = f.read()
        d = r.readstring(content)
        self.assertEqual(len(d.elements), 62)

    def test_document_usage(self):
        """Test RscHtmlReader used via Document.from_file."""
        fname = '10.1039_C6OB02074G.html'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'rsc', fname), 'rb')
        d = Document.from_file(f, readers=[RscHtmlReader()])
        self.assertEqual(len(d.elements), 62)
    
    def test_metadata(self):
        fname = '10.1039_C6OB02074G.html'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'rsc', fname), 'rb')
        d = Document.from_file(f, readers=[RscHtmlReader()])
        expected = {'MetaData': {'title': 'Denitrogenative hydrofluorination of aromatic aldehyde hydrazones using (difluoroiodo)toluene  ', 'authors': ['Kaivalya G.\xa0Kulkarni', 'Boris\xa0Miokovic', 'Matthew\xa0Sauder', 'Graham K.\xa0Murphy', 'Kaivalya G.\xa0Kulkarni', 'Boris\xa0Miokovic', 'Matthew\xa0Sauder', 'Graham K.\xa0Murphy'], 'publisher': 'Royal Society of Chemistry', 'journal': 'Organic & Biomolecular Chemistry', 'language': 'en', 'doi': '10.1039/C6OB02074G', 'pdf_url': 'http://pubs.rsc.org/en/Content/ArticlePDF/2016/OB/C6OB02074G', 'html_url': 'http://pubs.rsc.org/en/Content/ArticleLanding/2016/OB/C6OB02074G'}}
        meta = d.metadata.serialize()
        self.assertDictEqual(meta, expected)



if __name__ == '__main__':
    unittest.main()
