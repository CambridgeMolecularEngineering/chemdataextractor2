# -*- coding: utf-8 -*-
"""
test_model
~~~~~~~~~~

Test extracted data model.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest

from chemdataextractor.model import Compound, MeltingPoint, UvvisSpectrum, UvvisPeak, Apparatus, BaseModel
from chemdataextractor.model.units.temperature import TemperatureModel
from chemdataextractor.parse.elements import I, W
from chemdataextractor.model.base import StringType, ModelType, ListType, InferredProperty
from chemdataextractor.doc.text import Sentence
from chemdataextractor.parse.auto import AutoSentenceParser
from chemdataextractor.doc import Document
from lxml import etree
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


#: Models for testing
class NeelTemperature(TemperatureModel):
    specifier_expression = (I('Néel')+I('temperature'))
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=False, updatable=True)
    compound = ModelType(Compound, required=False, contextual=True)
    parsers = [AutoSentenceParser()]

class TestModel(unittest.TestCase):

    maxDiff = None

    def test_serialize(self):
        """Test model serializes as expected."""
        self.assertEqual(Compound(names=['Coumarin 343']).serialize(), {'Compound': {'names': ['Coumarin 343']}})

    def test_is_unidentified(self):
        """Test is_unidentified method returns expected result."""
        self.assertEqual(Compound().is_unidentified, True)
        self.assertEqual(Compound(names=['Coumarin 343']).is_unidentified, False)
        self.assertEqual(Compound(labels=['3a']).is_unidentified, False)
        self.assertEqual(Compound(names=['Coumarin 343'], labels=['3a']).is_unidentified, False)
        self.assertEqual(Compound(melting_points=[MeltingPoint(value='250')]).is_unidentified, True)

    def test_contextual_fulfilled(self):
        """Test contextual_fulfilled method returns expected result."""
        self.assertEqual(Compound(names=['Coumarin 343']).contextual_fulfilled, True)
        self.assertEqual(MeltingPoint(value=[240]).contextual_fulfilled, False)
        self.assertEqual(MeltingPoint(raw_units='K').contextual_fulfilled, False)
        self.assertEqual(MeltingPoint(apparatus=Apparatus(apparatus='Some apparatus')).contextual_fulfilled, False)
        Compound.fields['names'].contextual = True
        compound = Compound()
        spectrum = UvvisSpectrum(solvent='solvent',
                                 temperature='temperature',
                                 temperature_units='units',
                                 concentration='concentration',
                                 concentration_units='units')
        self.assertEqual(spectrum.contextual_fulfilled, False)
        spectrum.apparatus = Apparatus(apparatus_name='Some apparatus')
        self.assertEqual(spectrum.contextual_fulfilled, True)
        spectrum.compound = compound
        self.assertEqual(spectrum.contextual_fulfilled, False)
        spectrum.compound.names = ['Names']
        self.assertEqual(spectrum.contextual_fulfilled, True)
        Compound.fields['names'].contextual = False

    def test_required_fulfilled(self):
        class A(BaseModel):
            attribute_1 = StringType(required=True)
            attribute_2 = StringType(required=False)

        class B(BaseModel):
            a = ModelType(A, required=False)

        a = A(attribute_2='Test')
        self.assertFalse(a.required_fulfilled)
        b = B(a=a)
        self.assertTrue(b.required_fulfilled)
        B.fields['a'].required = True
        b = B(a=a)
        self.assertFalse(b.required_fulfilled)

    def test_model_update_definitions(self):
        """Test that the model parse expressions update method.
        """
        elements = [Sentence('Here we define the Néel temperature, TN')]
        definitions = elements[0].definitions
        NeelTemperature.update(definitions)
        test_sentence = Sentence('TN = 300 K')
        results = [i for i in NeelTemperature.parsers[0].parse_sentence(test_sentence)][0].serialize()

        self.assertEqual(results, {'NeelTemperature': {'raw_value': '300', 'raw_units': 'K', 'value': [300.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TN'}})

    def test_is_superset(self):
        class A(BaseModel):
            attribute_1 = StringType()
            attribute_2 = StringType()

        class B(BaseModel):
            a = ModelType(A)
            attribute_1 = StringType()

        a_list = [
            A(),
            A(attribute_2='test'),
            A(attribute_1='test'),
            A(attribute_1='test', attribute_2='test'),
        ]
        for i in range(1, 4):
            self.assertFalse(a_list[0].is_superset(a_list[i]))
        for i in range(3):
            self.assertTrue(a_list[-1].is_superset(a_list[i]))
        self.assertFalse(a_list[1].is_superset(a_list[2]))
        self.assertTrue(a_list[0].is_superset(a_list[0]))
        self.assertFalse(a_list[1].is_superset(a_list[3]))
        b_list = [
            B(),
            B(attribute_1='test'),
            B(a=a_list[0]),
            B(a=a_list[1]),
            B(attribute_1='test', a=a_list[0]),
            B(attribute_1='test', a=a_list[1]),
            B(attribute_1='test', a=a_list[-1]),
        ]
        for i in range(1, len(b_list)):
            self.assertFalse(b_list[0].is_superset(b_list[i]))
        for i in range(len(b_list) - 1):
            print(i)
            self.assertTrue(b_list[-1].is_superset(b_list[i]))
        self.assertTrue(b_list[-1].is_superset(b_list[-1]))
        self.assertTrue(b_list[5].is_superset(b_list[4]))
        self.assertFalse(b_list[4].is_superset(b_list[5]))
        self.assertTrue(b_list[3].is_superset(b_list[2]))
        self.assertFalse(b_list[2].is_superset(b_list[3]))
        self.assertTrue(b_list[2].is_superset(b_list[0]))

    def test_is_subset(self):
        class A(BaseModel):
            attribute_1 = StringType()
            attribute_2 = StringType()

        class B(BaseModel):
            a = ModelType(A)
            attribute_1 = StringType()

        a_list = [
            A(),
            A(attribute_2='test'),
            A(attribute_1='test'),
            A(attribute_1='test', attribute_2='test'),
        ]
        for i in range(1, 4):
            self.assertTrue(a_list[0].is_subset(a_list[i]))
        for i in range(3):
            self.assertFalse(a_list[-1].is_subset(a_list[i]))
        self.assertFalse(a_list[1].is_subset(a_list[2]))
        self.assertTrue(a_list[0].is_subset(a_list[0]))
        self.assertTrue(a_list[1].is_subset(a_list[3]))
        b_list = [
            B(),
            B(attribute_1='test'),
            B(a=a_list[0]),
            B(a=a_list[1]),
            B(attribute_1='test', a=a_list[0]),
            B(attribute_1='test', a=a_list[1]),
            B(attribute_1='test', a=a_list[-1]),
        ]
        for i in range(1, len(b_list)):
            self.assertTrue(b_list[0].is_subset(b_list[i]))
        for i in range(len(b_list) - 1):
            print(i)
            self.assertFalse(b_list[-1].is_subset(b_list[i]))
        self.assertTrue(b_list[-1].is_subset(b_list[-1]))
        self.assertFalse(b_list[5].is_subset(b_list[4]))
        self.assertTrue(b_list[4].is_subset(b_list[5]))
        self.assertFalse(b_list[3].is_subset(b_list[2]))
        self.assertTrue(b_list[2].is_subset(b_list[3]))
        self.assertFalse(b_list[2].is_subset(b_list[0]))

    def test_is_empty(self):
        class OuterModel(BaseModel):
            melting_point = ModelType(MeltingPoint)
            string_field = StringType()
            list_field = ListType(StringType())
            complex_list = ListType(ModelType(MeltingPoint))

        empty_records = [OuterModel(),
                        MeltingPoint(),
                        OuterModel(melting_point=MeltingPoint()),
                        OuterModel(melting_point=MeltingPoint(compound=Compound())),
                        OuterModel(string_field=""),
                        OuterModel(complex_list=[]),
                        OuterModel(list_field=[]),
                        OuterModel(melting_point=MeltingPoint(compound=Compound(names=[])))
                        ]

        for record in empty_records:
            self.assertTrue(record.is_empty)

        non_empty_records = [OuterModel(complex_list=[MeltingPoint()]),
                             OuterModel(melting_point=MeltingPoint(solvent="TEST")),
                             OuterModel(melting_point=MeltingPoint(compound=Compound(names=["TEST"]))),
                             OuterModel(string_field="TEST"),
                             ]

        for record in non_empty_records:
            self.assertFalse(record.is_empty)

    def test_keypath(self):
        class InnerModel(BaseModel):
            string_field = StringType()

        class OuterModel(BaseModel):
            inner_model = ModelType(InnerModel)

        inner_model = InnerModel(string_field="1234")
        outer_model = OuterModel(inner_model=inner_model)
        self.assertEqual(outer_model["inner_model.string_field"], "1234")

    def test_inferred_property(self):
        def reverse_string(string, instance):
            if string is not None:
                return string[::-1]

        class InnerModel(BaseModel):
            string_field = StringType()

        class OuterModel(BaseModel):
            inferred_from_field = InferredProperty(StringType(), origin_field="origin_field",
                                                   inferrer=reverse_string)
            inferred_from_nested = InferredProperty(StringType(), origin_field="origin_model.string_field",
                                                    inferrer=reverse_string)
            origin_field = StringType()
            origin_model = ModelType(InnerModel)

        inner_model = InnerModel(string_field="1234")
        outer_model = OuterModel(origin_model=inner_model, origin_field="abcd")
        expected = {"OuterModel": {"origin_field": "abcd",
                                   "origin_model": {"InnerModel": {"string_field": "1234"}},
                                   "inferred_from_field": "dcba",
                                   "inferred_from_nested": "4321"}}
        self.assertEqual(expected, outer_model.serialize())


if __name__ == '__main__':
    unittest.main()
