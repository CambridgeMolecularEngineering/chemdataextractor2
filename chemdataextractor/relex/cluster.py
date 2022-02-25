# -*- coding: utf-8 -*-
"""
Cluster of phrase objects and associated cluster dictionaries
"""
from collections import OrderedDict

import numpy as np
from lxml import etree
from scipy import spatial

from ..doc import Sentence
from ..utils import first
from .entity import Entity
from .pattern import Pattern
from .relationship import Relation
from .utils import mode_rows, subfinder

class Cluster:
    """
    Base Snowball Cluster, used to combine similar phrases
    """

    def __init__(self, label=None, learning_rate=0.5):
        """Create a new cluster
        
        Keyword Arguments:
            label {str} -- The label of this cluster (default: {None})
            order {list} -- The order of entities that all phrases in this cluster must share (default: {None})
            learning_rate {float} -- How quickly to update confidences based on new information (default: {0.5})
        """

        self.label = label
        self.phrases = []
        self.pattern = None
        self.entities = []
        self.dictionaries = {}
        self.order = None
        self.old_pattern_confidence = 1.0
        self.learning_rate = learning_rate

    def add_phrase(self, phrase):
        """ Add phrase to this cluster,
        update the word dictionary and token weights

        :param phrase: The phrase to add to the cluster
        :type phrase: chemdataextractor.relex.phrase.Phrase
        """
        self.phrases.append(phrase)
        self.order = phrase.order
        self.entities = phrase.entities
        self.update_dictionaries(phrase)
        self.update_weights()
        self.update_pattern()
        self.update_pattern_confidence()
        return

    def update_dictionaries(self, phrase):
        """Update all dictionaries in this cluster

        :param phrase: The phrase to update
        :type phrase: chemdataextractor.relex.phrase.Phrase

        """
        # Go through the prefix, middle and suffix elements
        for element in phrase.elements.keys():  # Prefix, middles, suffix
            if element not in self.dictionaries.keys():
                self.dictionaries[element] = {'token dict': OrderedDict(),
                                            'unique words': [],  # Which words appear once
                                            'total words': 0,  # counter
                                            'total recurring words': 0}  # counter
            # add the tokens
            self.add_tokens(self.dictionaries[element], phrase.elements[element]['tokens'])

        return

    @staticmethod
    def add_tokens(dictionary, tokens):
        """ Add specified tokens to the specified dictionary

        :param dictionary: The dictionary to add tokens to
        :type dictionary: OrderedDict
        :param tokens: tokens to add
        :type: list of str

        """
        for token in tokens:
            if token not in dictionary['token dict'].keys():
                dictionary['total words'] += 1
                dictionary['token dict'][token] = [1.0, 0]  # [frequeny, weight]
            else:
                dictionary['total words'] += 1
                dictionary['token dict'][token][0] += 1
        return

    def update_weights(self):
        """ Update the weights on each token in the phrases"""
        for element in self.dictionaries.keys():
            for token in self.dictionaries[element]['token dict'].keys():
                freq = self.dictionaries[element]['token dict'][token][0]
                weight = freq / self.dictionaries[element]['total words']
                self.dictionaries[element]['token dict'][token] = [freq, weight]

        return

    def update_pattern(self):
        """ Use the cluster phrases to generate a new centroid extraction Pattern object

        :param relations: List of known relations to look for
        :type: list of Relation objects
        :param sentences: List of sentences known to contain relations
        :type sentences: List of str"""

        vectors = {}
        # print("Updating pattern")
        pattern_elements = {}

        # Create a dict of vectors for all phrases in the cluster
        for phrase in self.phrases:
            for element in phrase.elements.keys():  # Prefix, ,iddles, suffix
                if element not in vectors.keys():
                    vectors[element] = []
                phrase_element_vector = []
                for token in self.dictionaries[element]['token dict'].keys():
                    if token in phrase.elements[element]['tokens']:
                        phrase_element_vector.append(self.dictionaries[element]['token dict'][token][1])
                    else:
                        phrase_element_vector.append(0)
                
                vectors[element].append(phrase_element_vector)

        # print("Vectors", vectors)

        # Find the centroid vector for prefix, middles, suffix
        for element in vectors.keys():
            element_array = np.array(vectors[element])
            # print("Element", element)
            # print("Element Array", element_array)
            # compute mode of vectors
            if element_array.any():
                element_mode = mode_rows(element_array)
            else:
                element_mode = np.array([])
            # print("Mode", element_mode)
            medoid_idx = spatial.KDTree(element_array).query(element_mode)[1]
            # print("Idx", medoid_idx)
            pattern_elements[element] = self.phrases[medoid_idx].elements[element]
            # print("Pattern element", pattern_elements[element])
        
        self.pattern = Pattern(elements=pattern_elements,
                               entities=self.entities,
                               label=self.label,
                               order=self.order,
                               relations=phrase.relations,
                               confidence=0) 
        # print("New Pattern", self.pattern)
        
        return
    
    def update_pattern_confidence(self):
        """Determine the confidence of this centroid pattern
        """
        # print("updating pattern confidence")
        # print("Old confidence:", self.old_pattern_confidence)

        total_matches = 0
        total_relations = sum([len(phrase.relations) for phrase in self.phrases])
        # print("Total relations in cluster: %d" % total_relations)
        # compare the centroid pattern to all sentences found in the phrases
        for phrase in self.phrases:
            # print("Phrase", phrase)
            sentence = Sentence(phrase.full_sentence)
            relations = phrase.relations
            found_relations = self.get_relations(sentence.tokens)
            # print("Found relations", found_relations, len(found_relations))
            # print("Known relations", relations)
            for fr in found_relations:
                if fr in relations:
                    total_matches += 1
        
        new_pattern_confidence = float(total_matches / total_relations)
        # print("new confidence", new_pattern_confidence)
        # Make sure new cluster begins with confidence 1.0
        if len(self.phrases) == 1:
            self.pattern.confidence = new_pattern_confidence
            self.old_pattern_confidence = self.pattern.confidence
        else:
            self.pattern.confidence = self.learning_rate*new_pattern_confidence + (1.0 - self.learning_rate)*self.old_pattern_confidence
            self.old_pattern_confidence = self.pattern.confidence
        return
        
    def get_relations(self, tokens):
        """Retrieve relations from a set of tokens using this clusters extraction pattern
        
        Arguments:
            tokens {list} -- Tokens to extract from
        
        Returns:
            Relations -- The found Relations
        """
        # print("Getting relations from", ' '.join([t[0] for t in tokens]), "\n\n")
        relations = []
        entity_type_indexes = {}

        for res in self.pattern.parse_expression.scan(tokens):
            match = res[0]
            # print(etree.tostring(match))
            for pattern_relation in self.pattern.relations:
                # print("Relation", pattern_relation)
                found_entities = []
                for pattern_entity in pattern_relation.entities:
                    if pattern_entity.tag not in entity_type_indexes.keys():
                        entity_type_indexes[pattern_entity.tag] = [pattern_entity]
                    else:
                        if pattern_entity not in entity_type_indexes[pattern_entity.tag]:
                            entity_type_indexes[pattern_entity.tag].append(pattern_entity)
                    # print(pattern_entity.tag)
                    xpath_str = pattern_entity.tag
                    # print(xpath_str)

                    entity_matches = match.xpath('./' + xpath_str + '/text()')
                    # print(entity_matches)

                    if len(entity_matches) > 0:
                        entity_text = entity_matches[entity_type_indexes[pattern_entity.tag].index(pattern_entity)]
                        entity_tokens = [s[0] for s in Sentence(entity_text).tokens]
                        start_idx, end_idx = subfinder([t[0] for t in tokens], entity_tokens)
                        found_entity = Entity(entity_text, pattern_entity.tag, pattern_entity.parse_expression, start_idx, end_idx)
                        found_entities.append(found_entity)
                found_relation = Relation(found_entities, confidence=0)
                # print("Found relation", found_relation)
                relations.append(found_relation)
        # print("output", relations)
        return relations
