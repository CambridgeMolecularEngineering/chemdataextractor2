# -*- coding: utf-8 -*-
"""
Extraction pattern object
"""

"""
   Modify generate_cde_element() function to adapt the changes of phrase.py.
   If any prefix/middle/suffix are empty (blank), do not add it to the resulting phrase.
   Modified by jz449
"""

import re
from ..parse.elements import I, W, R, Any, And, Start, OneOrMore, Group
from ..parse.actions import join


class Pattern:
    """ Pattern object, fundamentally the same as a phrase except assigned a confidence"""

    def __init__(self, entities=None,
                 elements=None,
                 label=None,
                 sentences=None,
                 order=None, 
                 relations=None, confidence=0):
        self.cluster_label = label
        self.elements = elements
        self.entities = entities
        self.number_of_entities = len(order)
        self.order = order
        self.relations = relations
        self.confidence = confidence
        self.parse_expression = self.generate_cde_parse_expression()

    def __repr__(self):
        return self.to_string()
    
    def to_string(self):
        output_string = ''
        output_string += ' '.join(self.elements['prefix']['tokens']) + ' '
        if isinstance(self.entities[0].tag, tuple):
            output_string += '(' + ', '.join([i for i in self.entities[0].tag]) + ') '
        else:
            output_string += '(' + self.entities[0].tag + ') '
        for i in range(0, self.number_of_entities - 1):
            output_string += ' '.join(self.elements['middle_' + str(i+1)]['tokens']) + ' '
            if isinstance(self.entities[i+1].tag, tuple):
                output_string += '(' + ', '.join([i for i in self.entities[i+1].tag]) + ') '
            else:
                output_string += '(' + self.entities[i+1].tag + ') '
        output_string = output_string
        output_string += ' '.join(self.elements['suffix']['tokens'])

        return output_string
    # TODO: Finish this once new parse_expressions are handled

    def generate_cde_parse_expression(self):
        """Create a CDE parse expression for this extraction pattern
        """
        elements = []
        prefix_tokens = self.elements['prefix']['tokens']
        for token in prefix_tokens:
            if token == '<Blank>':
                continue
            elements.append(I(token))

        elements.append(self.entities[0].parse_expression)
        
        for middle in range(0, self.number_of_entities -1):
            middle_tokens = self.elements['middle_' + str(middle+1)]['tokens']
            for token in middle_tokens:
                if token == '<Blank>':
                    continue
                elements.append(I(token))
            elements.append(self.entities[middle+1].parse_expression)

        
        suffix_tokens = self.elements['suffix']['tokens']
        for token in suffix_tokens:
            if token == '<Blank>':
                continue
            elements.append(I(token))
        
        final_phrase = And(exprs=elements)
        parse_expression = (final_phrase)('phrase')
        return parse_expression
