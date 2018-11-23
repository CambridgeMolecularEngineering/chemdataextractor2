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
from chemdataextractor.doc.text import Paragraph, Title, Heading, Caption, Footnote
from chemdataextractor.config import Config
from chemdataextractor.parse.cem import CompoundParser, ChemicalLabelParser, CompoundHeadingParser
from chemdataextractor.parse.nmr import NmrParser
from chemdataextractor.parse.ir import IrParser
from chemdataextractor.parse.uvvis import UvvisParser
from chemdataextractor.parse.mp import MpParser
from chemdataextractor.parse.tg import TgParser
from chemdataextractor.parse.context import ContextParser

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestText(unittest.TestCase):
    """Simple Text instantiation tests."""

    @staticmethod
    def get_config():
        test_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'test_config.yml')
        return Config(test_config_path)

    def test_parsers_set_from_config(self):
        d = Document(Title('Test'), Paragraph('Test'), Footnote('Test'), Heading('Test'), Caption('Test'), config=self.get_config())
        title_p = d.titles[0].parsers
        heading_p = d.headings[0].parsers
        paragraph_p = d.paragraphs[0].parsers
        footnotes_p = d.footnotes[0].parsers
        caption_p = d.captions[0].parsers

        for parser in paragraph_p:
            self.assertIn(type(parser), [CompoundParser, ChemicalLabelParser, NmrParser])
        self.assertEqual(type(title_p[0]), NmrParser)
        self.assertEqual(type(footnotes_p[0]), ChemicalLabelParser)
        self.assertEqual(type(heading_p[0]), NmrParser)
        self.assertEqual(type(caption_p[0]), NmrParser)

    def test_default_parsers(self):
        d = Document(Title('Test'), Paragraph('Test'), Footnote('Test'), Heading('Test'), Caption('Test'))
        title_p = d.titles[0].parsers
        heading_p = d.headings[0].parsers
        paragraph_p = d.paragraphs[0].parsers
        footnotes_p = d.footnotes[0].parsers
        caption_p = d.captions[0].parsers

        for parser in paragraph_p:
            self.assertIn(type(parser), [CompoundParser, ChemicalLabelParser, NmrParser, IrParser, UvvisParser, MpParser,
               TgParser, ContextParser])
        self.assertEqual(type(title_p[0]), CompoundParser)
        self.assertEqual(type(footnotes_p[0]), ContextParser)
        self.assertEqual(type(heading_p[0]), CompoundHeadingParser)
        self.assertEqual(type(caption_p[0]), CompoundParser)


