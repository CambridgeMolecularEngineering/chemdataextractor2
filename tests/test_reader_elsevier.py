# -*- coding: utf-8 -*-
"""
chemdataextractor.tests.test_reader_els.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test reader for Elsevier.

.. codeauthor:: Juraj Mavračić <jm2111@cam.ac.uk>
Callum Court (cc889@cam.ac.uk)

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
        self.assertEqual(len(d.elements), 165)

    def test_document_usage(self):
        """Test RscXMLReader used via Document.from_file."""
        fname = 'j.jnoncrysol.2017.07.006.xml'
        f = io.open(os.path.join(os.path.dirname(__file__), 'data', 'elsevier', fname), 'rb')
        d = Document.from_file(f, readers=[ElsevierXmlReader()])
        self.assertEqual(len(d.elements), 165)


if __name__ == '__main__':
    unittest.main()
