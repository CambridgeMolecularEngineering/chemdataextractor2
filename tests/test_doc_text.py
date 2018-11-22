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
import os

from chemdataextractor.doc.document import Document
from chemdataextractor.doc.text import Paragraph, Title
from chemdataextractor.config import Config
from chemdataextractor.parse.cem import CompoundParser, ChemicalLabelParser
from chemdataextractor.parse.nmr import NmrParser

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestText(unittest.TestCase):
    """Simple Text instantiation tests."""

    def get_config(self):

        test_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'test_config.yml')
        print(test_config_path)
        return Config(test_config_path)

    def test_set_parsers(self):

        d = Document(Paragraph('Test'), Title('Test'), config=self.get_config())
        self.assertEqual(d.paragraphs[0].parsers, [CompoundParser, ChemicalLabelParser, NmrParser])
        self.assertEqual(d.titles[0].parsers, [NmrParser])

    def test_without_set_parsers(self):
        d = Document(Paragraph('Test'), Title('Test'))

