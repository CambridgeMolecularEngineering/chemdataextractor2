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

from chemdataextractor.model import Compound, MeltingPoint, UvvisSpectrum, UvvisPeak
from chemdataextractor.model.units.temperature import TemperatureModel
from chemdataextractor.parse.elements import I, W
from chemdataextractor.model.base import StringType, ModelType
from chemdataextractor.doc.text import Sentence
from chemdataextractor.doc import Document
from lxml import etree
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

#: Models for testing
class NeelTemperature(TemperatureModel):
    specifier_expression = (I('Néel')+I('temperature'))
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=False, mutable=True)
    compound = ModelType(Compound, required=False, contextual=True)

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

    def test_is_contextual(self):
        """Test is_contextual method returns expected result."""
        self.assertEqual(Compound(names=['Coumarin 343']).is_contextual, False)
        self.assertEqual(Compound(melting_points=[MeltingPoint(value=[240])]).is_contextual, True)
        self.assertEqual(Compound(melting_points=[MeltingPoint(units='K')]).is_contextual, True)
        self.assertEqual(Compound(melting_points=[MeltingPoint(apparatus='Some apparatus')]).is_contextual, True)
        self.assertEqual(Compound(labels=['3a'], melting_points=[MeltingPoint(apparatus='Some apparatus')]).is_contextual, False)
        self.assertEqual(Compound(uvvis_spectra=[UvvisSpectrum(apparatus='Some apparatus')]).is_contextual, True)
        self.assertEqual(Compound(uvvis_spectra=[UvvisSpectrum(peaks=[UvvisPeak(value='378')])]).is_contextual, True)
        self.assertEqual(Compound(uvvis_spectra=[UvvisSpectrum(peaks=[UvvisPeak(units='nm')])]).is_contextual, True)
    
    def test_model_update_definitions(self):
        """Test that the model parse expressions update method.
        """
        elements = [Sentence('Here we define the Néel temperature, TN')]
        definitions = elements[0].definitions
        NeelTemperature.update(definitions)
        test_sentence = Sentence('TN = 300 K')
        results = [i for i in NeelTemperature.parsers[0].parse_sentence(test_sentence.tagged_tokens)][0].serialize()

        self.assertEqual(results, {'NeelTemperature': {'raw_value': '300', 'raw_units': 'K', 'value': [300.0], 'units': 'Kelvin^(1.0)', 'specifier': 'TN'}})





if __name__ == '__main__':
    unittest.main()
