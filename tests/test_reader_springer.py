# -*- coding: utf-8 -*-
"""
test_reader_springer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test reader for Springer.

.. codeauthor:: Shu Huang <sh2009@cam.ac.uk>
"""
import unittest
import logging
import io
import os

from chemdataextractor.doc.document import Document
from chemdataextractor.reader.springer_jats import SpringerJatsReader

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class TestSpringerJatsReader(unittest.TestCase):

    def test_detect(self):
        """Test RscXMLReader can detect an RSC document."""
        r = SpringerJatsReader()
        fname = 'spr_test1.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'springer', fname), 'rb')
        content = f.read()
        f.close()
        self.assertEqual(r.detect(content, fname=fname), True)

    def test_direct_usage(self):
        """Test RscXMLReader used directly to parse file."""
        r = SpringerJatsReader()
        fname = 'spr_test1.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'springer', fname), 'rb')
        content = f.read()
        d = r.readstring(content)
        f.close()
        self.assertEqual(len(d.elements), 307)

    def test_document_usage(self):
        """Test RscXMLReader used via Document.from_file."""
        fname = 'spr_test1.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'springer', fname), 'rb')
        d = Document.from_file(f, readers=[SpringerJatsReader()])
        self.assertEqual(len(d.elements), 307)


if __name__ == '__main__':
    unittest.main()
