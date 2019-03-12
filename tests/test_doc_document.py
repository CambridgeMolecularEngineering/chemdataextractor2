# -*- coding: utf-8 -*-
"""
test_doc_document
~~~~~~~~~~~~~~~~~

Test the Document class.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest

from chemdataextractor.doc.document import Document

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestDocument(unittest.TestCase):
    """Simple Document instantiation tests."""

    def test_text_elements(self):
        """Test Document can be instantiated with a list of strings."""
        els = [
            'A first paragraph. With two sentences.',
            'A second paragraph.',
            'A third paragraph.'
        ]
        d = Document(*els)
        self.assertEqual(d.elements[0].text, 'A first paragraph. With two sentences.')
        self.assertEqual(d.elements[0].sentences[1].text, 'With two sentences.')
        self.assertEqual(d.elements[1].document, d)

    def test_bytestring_elements(self):
        """Test Document can be instantiated with a list of bytestrings."""
        els = [
            'A first paragraph. With two sentences.'.encode('ascii'),
            'A second paragraph. \u00a9'.encode('utf-8'),
            'A third paragraph (\u00b6).'.encode('windows-1252'),
        ]
        d = Document(*els)
        self.assertEqual(d.elements[0].text, 'A first paragraph. With two sentences.')
        self.assertEqual(d.elements[0].sentences[1].text, 'With two sentences.')
        self.assertEqual(d.elements[1].document, d)

    def test_document_iter(self):
        """Test Document can be iterated like a list to access its elements."""
        els = [
            'A first paragraph. With two sentences.',
            'A second paragraph.',
            'A third paragraph.'
        ]
        d = Document(*els)
        self.assertEqual(len(d), 3)
        self.assertEqual(d[2].text, 'A third paragraph.')
        self.assertEqual([e.text for e in d], els)

    def test_document_definitions(self):
        """Test getting defintions from a document
        """
        els = ['Here we define the Curie temperature (TC).',
               'Next we have the uv-vis absorption maximum, λmax',
               'Finally, the melting point, Tm']
        d = Document(*els)
        defs = d.definitions
        expected = [{'definition': 'Curie temperature', 'specifier': 'TC', 'tokens': [('Curie', 'JJ'), ('temperature', 'NN'), ('(', '-LRB-'), ('TC', 'NN'), (')', '-RRB-')], 'start': 4, 'end': 9}, {'definition': 'uv - vis absorption maximum', 'specifier': 'λmax', 'tokens': [('uv', 'NN'), ('-', 'HYPH'), ('vis', 'NN'), ('absorption', 'NN'), ('maximum', 'NN'), (',', ','), ('λmax', 'NN')], 'start': 4, 'end': 11}, {'definition': 'melting point', 'specifier': 'Tm', 'tokens': [('melting', 'NN'), ('point', 'NN'), (',', ','), ('Tm', 'NN')], 'start': 3, 'end': 7}]
        self.assertEqual(defs, expected)


if __name__ == '__main__':
    unittest.main()
