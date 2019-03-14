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
    
    def serialize(self):
        output = {}
        for entity in self.entities:
            entity_data = entity.serialize()
            output.update(entity_data)
        output['confidence'] = self.confidence
        return output
