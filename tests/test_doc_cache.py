# -*- coding: utf-8 -*-
"""
test_doc_cache
~~~~~~~~~~~~~~~~~

Test the Document caching using the PlainTextCacher class.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import os
import unittest

from chemdataextractor.doc.document import Document
from chemdataextractor.doc.document_cacher import PlainTextCacher
from chemdataextractor.model import Compound


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestDocument(unittest.TestCase):
    def test_caching(self):
        fname = '10.1039_C6OB02074G.html'
        full_path = os.path.join(os.path.dirname(__file__), 'data', 'rsc', fname)
        test_cache_location = os.path.join(os.path.dirname(__file__), 'data', 'test_cache')

        doc = Document.from_file(full_path)
        doc.models = [Compound]
        cacher = PlainTextCacher(test_cache_location)
        cacher.cache_document(doc, 'test_cache', overwrite_cache=True)

        cached_document = Document.from_file(full_path)
        cached_document.models = [Compound]
        cached_document = cacher.hydrate_document(cached_document, 'test_cache')

        for sentence1, sentence2 in zip(doc.sentences, cached_document.sentences):
            tokens1 = sentence1.tokens
            tokens2 = sentence2.tokens
            for token1, token2 in zip(tokens1, tokens2):
                self.assertEqual(token1.text, token2.text)
                self.assertEqual(token1.start, token2.start)
                self.assertEqual(token1.end, token2.end)
                self.assertEqual(token1.ner_tag, token2.ner_tag)
                self.assertEqual(token1.pos_tag, token2.pos_tag)

        self.assertCountEqual(doc.records.serialize(), cached_document.records.serialize())
