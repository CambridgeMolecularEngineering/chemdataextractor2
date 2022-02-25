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
from chemdataextractor.doc.text import Paragraph, Title, Heading, Caption, Footnote, Sentence, RichToken
from chemdataextractor.nlp.tag import BaseTagger
from chemdataextractor.config import Config
from chemdataextractor.model import Compound, NmrSpectrum, IrSpectrum, UvvisSpectrum, MeltingPoint, GlassTransition
from chemdataextractor.nlp import *

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestText(unittest.TestCase):
    """Simple Text instantiation tests."""

    @staticmethod
    def get_config():
        test_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'test_config.yml')
        return Config(test_config_path)

    # TODO: Allow importing models defaults from config files
    # def test_parsers_set_from_config(self):
    #     d = Document(Title('Test'), Paragraph('Test'), Footnote('Test'), Heading('Test'), Caption('Test'), config=self.get_config())
    #     title_p = d.titles[0].parsers
    #     heading_p = d.headings[0].parsers
    #     paragraph_p = d.paragraphs[0].parsers
    #     footnotes_p = d.footnotes[0].parsers
    #     caption_p = d.captions[0].parsers

    #     for parser in paragraph_p:
    #         self.assertIn(type(parser), [CompoundParser, ChemicalLabelParser, NmrParser])
    #     self.assertEqual(type(title_p[0]), NmrParser)
    #     self.assertEqual(type(footnotes_p[0]), ChemicalLabelParser)
    #     self.assertEqual(type(heading_p[0]), NmrParser)
    #     self.assertEqual(type(caption_p[0]), NmrParser)

    def test_default_models(self):
        # Add some sort of test for ContextParser type stuff?
        d = Document(Title('Test'), Paragraph('Test'), Footnote('Test'), Heading('Test'), Caption('Test'))
        title_m = d.titles[0].models
        heading_m = d.headings[0].models
        paragraph_m = d.paragraphs[0].models
        footnotes_m = d.footnotes[0].models
        captions_m = d.footnotes[0].models
        for model in paragraph_m:
            self.assertIn(model, [])
        self.assertEqual(title_m, [])
        self.assertEqual(heading_m, [])
        self.assertEqual(captions_m, [])

    def test_set_cem(self):
        d = Document(Title('Test'), config=self.get_config())
        title = d.titles[0]
        self.assertEqual(type(title.pos_tagger), CrfPosTagger)
        self.assertEqual(type(title.ner_tagger), CemTagger)
        self.assertEqual(type(title.lexicon), Lexicon)
        self.assertEqual(type(title.sentence_tokenizer), SentenceTokenizer)
        self.assertEqual(type(title.word_tokenizer), WordTokenizer)

    def test_no_cem_set(self):
        d = Document(Title('Test'))
        title = d.titles[0]
        self.assertEqual(type(title.pos_tagger), ChemCrfPosTagger)
        self.assertEqual(type(title.ner_tagger), CemTagger)
        self.assertEqual(type(title.lexicon), ChemLexicon)
        self.assertEqual(type(title.sentence_tokenizer), ChemSentenceTokenizer)
        self.assertEqual(type(title.word_tokenizer), BertWordTokenizer)

    def test_richtokens(self):
        class TestTagger(BaseTagger):
            tag_type = "test_tag"

            def tag(self, tokens):
                tags = []
                for token in tokens:
                    pos_tag = token.pos_tag
                    new_tag = "TEST" + pos_tag
                    tags.append((token, new_tag))
                return tags

        sent = Sentence("3-Bromo-2,6-dichloroaniline: mp 71-72° C.")
        sent.taggers.append(TestTagger())

        for index, token in enumerate(sent.tokens):
            self.assertEqual("TEST" + token.pos_tag, token.test_tag)
            self.assertEqual(sent.tokens[index][1], token[1])
