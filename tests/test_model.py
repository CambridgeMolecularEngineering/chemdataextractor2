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

from chemdataextractor.model import Compound, MeltingPoint, UvvisSpectrum, UvvisPeak, Apparatus
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
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=False, updatable=True)
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
