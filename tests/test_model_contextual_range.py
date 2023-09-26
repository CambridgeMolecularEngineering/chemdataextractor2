# -*- coding: utf-8 -*-
"""
test_model_contextual_range
~~~~~~~~~~~~~~~~~

Test contextual ranges.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest
import os

from chemdataextractor.model.contextual_range import ContextualRange, DocumentRange, SectionRange, ParagraphRange, SentenceRange
from chemdataextractor.model import BaseModel, ModelType, StringType, TemperatureModel, Compound
from chemdataextractor.parse.auto import AutoSentenceParser
from chemdataextractor.parse.elements import R, I
from chemdataextractor.doc.document import Document
from chemdataextractor.doc.text import Paragraph, Heading, Title

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class InnerModel(BaseModel):
    string_field = StringType(contextual=True, contextual_range=SectionRange())
    string_field_2 = StringType(contextual=True, contextual_range=SectionRange())


class OuterModel(BaseModel):
    string_field = StringType(contextual=True, contextual_range=SectionRange())
    model_field = ModelType(InnerModel, contextual=True, contextual_range=SectionRange())


class BoilingPoint(TemperatureModel):
    compound = ModelType(Compound, contextual=True, contextual_range=SentenceRange())
    specifier = StringType(contextual=False, required=True, parse_expression=R("boil"))
    parsers = [AutoSentenceParser()]


class TestContextualRange(unittest.TestCase):
    """Contextual range tests"""

    def test_add(self):
        new_range = DocumentRange() + DocumentRange() + SectionRange()
        print(len(DocumentRange()._constituent_ranges))
        print(DocumentRange().constituent_ranges)
        expected_ranges = {DocumentRange(): 2, SectionRange(): 1}
        self.assertDictEqual(new_range.constituent_ranges, expected_ranges)

    def test_mul(self):
        new_range = 2 * DocumentRange() * 2
        expected_ranges = {DocumentRange(): 4}
        self.assertDictEqual(new_range.constituent_ranges, expected_ranges)

    def test_div(self):
        new_range = (2 * DocumentRange()) / 0.8
        expected_ranges = {DocumentRange(): 2.5}
        self.assertDictEqual(new_range.constituent_ranges, expected_ranges)

    def test_rdiv_fails(self):
        with self.assertRaises(TypeError):
            2.0 / DocumentRange()

    def test_complex_maths(self):
        new_range = 2 * DocumentRange() + SectionRange()
        expected_ranges = {DocumentRange(): 2, SectionRange(): 1}
        self.assertDictEqual(new_range.constituent_ranges, expected_ranges)

    def test_comparison(self):
        range_a = DocumentRange()
        range_b = DocumentRange() + SectionRange()
        range_c = DocumentRange() + 2 * SectionRange()
        range_d = SentenceRange()
        range_e = DocumentRange() + SectionRange() + SentenceRange()
        range_f = 2 * SectionRange() + 1 * SentenceRange()
        range_g = 2 * SectionRange() + 10 * SentenceRange()

        self.assertTrue(range_b > range_a)
        self.assertTrue(range_c > range_b)
        self.assertTrue(range_c > range_d)
        self.assertTrue(range_e > range_b)
        self.assertTrue(range_e < range_c)
        self.assertTrue(range_c > range_e)
        self.assertTrue(range_f < range_g)

    def test_merge_contextual_respects_range_for_field(self):
        inner_model_a = InnerModel()
        inner_model_b = InnerModel(string_field="test_string")

        inner_model_a.merge_contextual(inner_model_b, distance=DocumentRange())
        self.assertEqual(inner_model_a.get("string_field"), None)

        inner_model_a.merge_contextual(inner_model_b, distance=SectionRange())
        self.assertEqual(inner_model_a.get("string_field"), "test_string")

    def test_merge_contextual_respects_range_for_model(self):
        outer_model_a = OuterModel()
        inner_model_a = InnerModel(string_field="test_string")

        outer_model_a.merge_contextual(inner_model_a, distance=DocumentRange())
        self.assertEqual(outer_model_a.get("model_field"), None)

        outer_model_a.merge_contextual(inner_model_a, distance=ParagraphRange())
        self.assertEqual(outer_model_a.get("model_field"), inner_model_a)

        inner_model_b = InnerModel(string_field_2="test_string_2")
        outer_model_a.merge_contextual(inner_model_b, distance=ParagraphRange())
        self.assertEqual(outer_model_a.get("model_field").get("string_field"), "test_string")
        self.assertEqual(outer_model_a.get("model_field").get("string_field_2"), "test_string_2")

    def parse_document_1(self, expected):
        doc = Document(
            Title("Boiling behaviour"),
            Heading("H2O investigation"),
            Paragraph("It's great, and we investigate how H2O behaves in this paper. Stay hydrated!"),
            Heading("Methodology"),
            Paragraph("What do you expect here?"),
            Heading("Results"),
            Paragraph("It has a boiling temperature of 373K. What a surprise!"),
        )
        doc.models = [BoilingPoint]
        for el in doc.elements:
            print(el.records.serialize())
        print(doc.records.serialize())
        self.assertCountEqual(expected, doc.records.serialize())
        BoilingPoint.compound.contextual_range = SentenceRange()

    def test_contextual_range_during_parsing(self):
        expected = [
            {
                'BoilingPoint':
                {
                    'raw_value': '373',
                    'raw_units': 'K',
                    'value': [373.0],
                    'units': 'Kelvin^(1.0)',
                    'specifier': 'boiling'
                }
            }
        ]
        self.parse_document_1(expected)

    def test_contextual_range_during_parsing_2(self):
        BoilingPoint.compound.contextual_range = 2 * SectionRange() + 10 * ParagraphRange()
        expected = [
            {
                'BoilingPoint':
                {
                    'raw_value': '373',
                    'raw_units': 'K',
                    'value': [373.0],
                    'units': 'Kelvin^(1.0)',
                    'specifier': 'boiling',
                    'compound': {
                        'Compound': {'names': ['H2O']}
                    },
                }
            }
        ]
        self.parse_document_1(expected)

    def test_contextual_range_during_parsing_3(self):
        BoilingPoint.compound.contextual_range = DocumentRange()
        expected = [
            {
                'BoilingPoint':
                {
                    'raw_value': '373',
                    'raw_units': 'K',
                    'value': [373.0],
                    'units': 'Kelvin^(1.0)',
                    'specifier': 'boiling',
                    'compound': {
                        'Compound': {'names': ['H2O']}
                    },
                }
            }
        ]
        self.parse_document_1(expected)


if __name__ == '__main__':
    unittest.main()
