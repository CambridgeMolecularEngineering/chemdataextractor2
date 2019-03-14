# -*- coding: utf-8 -*-
"""
Classes for defining new chemical relationships
"""
import copy
from itertools import product

from .entity import Entity
from .utils import KnuthMorrisPratt

class Relation(object):
    """Relation class

    Essentially a placeholder for related of entities
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
    
    def __eq__(self, other):
        if len(self.entities) != len(other.entities):
            return False
            
        for i, entity in enumerate(self.entities):
            if entity != other.entities[i]:
                return False
            else:
                continue
        return True

    def __repr__(self):
        return '<' + ', '.join([str(i) for i in self.entities]) + '>'
    def __str__(self):
        return self.__repr__()
    
    def serialize(self):
        output = {}
        for entity in self.entities:
            entity_data = entity.serialize()
            output.update(entity_data)
        output['confidence'] = self.confidence
        return output
