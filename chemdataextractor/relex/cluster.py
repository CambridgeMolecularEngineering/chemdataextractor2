# -*- coding: utf-8 -*-
"""
chemdataextractor.relex.cluster
Cluster of phrase objects and associated cluster dictionaries
"""
from collections import OrderedDict
from .pattern import Pattern
import numpy as np
from scipy import spatial
from lxml import etree
from ..doc import Sentence
from .entity import Entity
from .relationship import Relationship
from ..utils import first

def mode_rows(a):
    """
    Find the modal row of a 2d array
    :param a: The 2d array to process
    :type a: np.array()
    :return: The most frequent row
    """
    a = np.ascontiguousarray(a)
    void_dt = np.dtype((np.void, a.dtype.itemsize * np.prod(a.shape[1:])))
    _, ids, count = np.unique(a.view(void_dt).ravel(),
                              return_index=True,
                              return_counts=True)
    largest_count_id = ids[count.argmax()]
    most_frequent_row = a[largest_count_id]
    return most_frequent_row


class Cluster:
    """
    Base Snowball Cluster
    """

    def __init__(self, label=None, order=None):
        """
        :param label: String to identify this cluster
        :type label: str
        """
        self.label = label
        self.phrases = []
        self.pattern = None
        self.entities = []
        self.dictionaries = {}
        self.order = None

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
                dictionary['token dict'][token] = [
                    1.0, 0]  # [frequeny, weight]
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
                self.dictionaries[element]['token dict'][token] = [
                        freq, weight]

        return

    def update_pattern(self):
        """ Use the cluster phrases to generate a new centroid extraction Pattern object

        :param relations: List of known relations to look for
        :type: list of Relation objects
        :param sentences: List of sentences known to contain relations
        :type sentences: List of str"""

        vectors = {}
        print("Updating pattern")


        pattern_elements = {}

        # Create a dict of vectors for all phrases in the cluster
        for phrase in self.phrases:
            self.vectorise(phrase)
            for element in phrase.elements.keys():  # Prefix, ,iddles, suffix
                if element not in vectors.keys():
                    vectors[element] = []
                if phrase.elements[element]['vector']:
                    vectors[element].append(phrase.elements[element]['vector'])
                else:
                    vectors[element] = [[]]

        # Find the centroid vector for prefix, middles, suffix
        for element in vectors.keys():
            element_array = np.array(vectors[element])

            # compute mode of vectors
            if element_array.any():
                element_mode = mode_rows(element_array)
            else:
                element_mode = np.array([])
            # find points closest to the mode
            medoid_idx = spatial.KDTree(element_array).query(element_mode)[1]
            pattern_elements[element] = self.phrases[medoid_idx].elements[element]
        
        self.pattern = Pattern(elements=pattern_elements,
                               entities=self.entities,
                               label=self.label,
                               order=self.order,
                               relations=phrase.relations)
        print(self.pattern)
        return

    def vectorise(self, phrase):
        """ Convert phrase prefix, middles and suffix into
        a normalised vector of weights

        :param phrase: The phrase to vectorise
        :type phrase: chemdataextractor.relex.phrase.Phrase

        """

        for element in phrase.elements.keys():
            #print(element, element_key)
            element_dict = phrase.elements[element]
            #print("Dict", element_dict)
            vector = np.zeros(len(self.dictionaries[element]['token dict']))
            for token in element_dict['tokens']:
                if token in list(self.dictionaries[element]['token dict'].keys()):
                    token_index = list(self.dictionaries[element]['token dict'].keys()).index(token)
                    vector[token_index] = self.dictionaries[element]['token dict'][token][1]
            norm = np.linalg.norm(vector)
            if norm > 1e-15:
                element_dict['vector'] = list((vector/np.linalg.norm(vector)))
                #print(element_dict['vector'], len(element_dict['vector']))
            else:
                element_dict['vector'] = list(np.zeros(len(self.dictionaries[element]['token dict'])))
        return
    
    def update_pattern_confidence(self):
        """Determine the confidence of this centroid pattern
        """

        total_matches = 0
        total_relations = sum([len(phrase.relations) for phrase in self.phrases])
        print("Total relations in cluster: %d" % total_relations)
        # compare the centroid pattern to all sentences found in the phrases
        for phrase in self.phrases:
            sentence = Sentence(phrase.full_sentence)
            relations = phrase.relations
            print(relations)
            pattern_element = self.pattern.generate_cde_element()
            print(sentence)

            for res in pattern_element.scan(sentence.tagged_tokens):
                match = res[0]
                print(etree.tostring(match))
                match_tokens = [i for i in match.xpath('./*/text()')]
                print(match_tokens)
                found_relations = []
                for pattern_relation in self.pattern.relations:
                    found_entities = []
                    for pattern_entity in pattern_relation.entities:
                        entity_text = first(match.xpath('./' + pattern_entity.tag.name + '/text()'))
                        found_entity = Entity(entity_text, pattern_entity.tag, 0, 0)
                        found_entities.append(found_entity)
                    found_relation = Relationship(found_entities, confidence=0)
                    found_relations.append(found_relation)
                
            
                print("Found relations", found_relations)
                print("Phrase relations", relations)
                for fr in found_relations:
                    if fr in relations:
                        total_matches += 1
        
        self.pattern.confidence = float(total_matches / total_relations)
        return
        
        





