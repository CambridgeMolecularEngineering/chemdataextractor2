# -*- coding: utf-8 -*-
"""
Chemdataextractor.relex.relationship

Classes for defining new chemical relationships
"""
import copy
from collections import Counter
from itertools import combinations, product

from .entity import Entity
from .utils import KnuthMorrisPratt


class ChemicalRelationship(object):
    """Base ChemicalRelationship class
    
    Used to define a new relationship model based on entities
    """


    def __init__(self, entities, parser, name):
        """Create the new relationship
        
        Arguments:
            entities {list(chemdataextractor elements)} -- List of CDE parse elements that define how to identify the entities
            parser {Parserelement} -- A phrase describing how to find all entities in a single sentence
            name {str} -- What to call this relationship
        """

        self.entities = copy.copy(entities)
        self.parser = parser
        self.name = name

    def get_candidates(self, tokens):
        """Find all candidate relationships of this type within a sentence
        
        Arguments:
            tokens {list} -- List of sentence tokens, tagged using CDE
        Returns
            relations {list} -- list of relations found in the text
        """
        candidate_relationships = []
        # Scan the tagged tokens with the parser
        detected = []
        for result in self.parser.scan(tokens):
            for e in self.entities:
                text_list = result[0].xpath('./' + e.name + '/text()')
                for i, text in enumerate(text_list):
                    if not text:
                        continue
                    detected.append((text, e))

        entities_dict = {}
        
        if not detected:
            return []

        detected = list(set(detected))  # Remove duplicate entries (handled by indexing)
        for text, tag in detected:
            text_length = len(text.split(' '))
            toks = [tok[0] for tok in tokens]
            start_indices = [s for s in KnuthMorrisPratt(toks, text.split(' '))]
            
            # Add specifier to dictionary  if it doesn't exist
            if tag.name not in entities_dict.keys():
                entities_dict[tag.name] = []

            entities = [Entity(text, tag, index, index+text_length) for index in start_indices]
            # Add entities to dictionary if new
            for entity in entities:
                if entity not in entities_dict[tag.name]:
                    entities_dict[tag.name].append(entity)

        # check all required entities are present
        if not all(e.name in entities_dict.keys() for e in self.entities):
            return []

        # Construct all valid combinations of entities
        all_entities = [e for e in entities_dict.values()]
        candidates = list(product(*all_entities))
        for candidate in candidates:
            candidate_relationships.append(Relation(candidate, confidence=0))

        return candidate_relationships


class Relation(object):
    """Relation class

    Essentially a placeholder for a number of entities
    """


    def __init__(self, entities, confidence):
        """Init
        
        Arguments:
            entities {list} -- List of Entity objects that are present in this relationship
            confidence {float} -- The confidence of the relation
        """

        self.entities = copy.copy(entities)
        self.confidence = confidence
    
    def __len__(self):
        return len(self.entities)
    
    def __getitem__(self, idx):
        return self.entities[idx]
    
    def __setitem__(self, idx, value):
        self.entities[idx] = value
    
    def __repr__(self):
        return '<' + ', '.join([str(i) for i in self.entities]) + '>'
    
    def __eq__(self, other):
        # compare the text of all entities
        other_entities = other.entities
        for entity in self.entities:
            if not entity.text in [i.text for i in other_entities]:
                return False
        return True
    
    def __str__(self):
        return self.__repr__()
