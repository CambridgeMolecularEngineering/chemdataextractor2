# -*- coding: utf-8 -*-
"""
Extraction pattern object
"""
import copy
import six
from ..parse import Group, join

class Entity(object):
    """A base entity, the fundamental unit of a Relation

    """


    def __init__(self, text, tag, parse_expression, start ,end):
        """Create a new Entity

        Arguments:
            text {str} -- The text of the entity
            tag {str or list} -- name of the entity
            parse_expression -- how the entity is identified in text
            start {int} -- The index of the Entity in tokens
            end {int} -- The end index of the entity in tokens
        """
        self.text = six.text_type(text)
        self.tag = tag
        self.parse_expression = copy.copy(parse_expression)
        self.parse_expression.set_name(None)

        if self.parse_expression.name is None or self.parse_expression.name == 'compound':
            if isinstance(self.tag, tuple):
                for sub_tag in self.tag:
                    self.parse_expression = Group(self.parse_expression)(sub_tag)
            else:
                self.parse_expression = Group(self.parse_expression)(self.tag).add_action(join)
        
        self.end = end
        self.start = start

    def __eq__(self, other):
        if self.text == other.text and self.end == other.end and self.start == other.start:
            return True
        else:
            return False

    def __repr__(self):
        if isinstance(self.tag, str):
            return '(' + self.text + ',' + self.tag + ',' + str(self.start) + ',' + str(self.end) + ')'
        else:
            return '(' + self.text + ',' + '_'.join([i for i in self.tag]) + ',' + str(self.start) + ',' + str(self.end) + ')'

    def __str__(self):
        return self.__repr__()
    
    def serialize(self):
        
        output = current = {}
        if '__' in self.tag:
            tag = [i for i in self.tag.split('__')]
            for i, t in enumerate(tag):
                if i == len(tag)-1:
                    current[t] = self.text
                else:
                    current[t] = {}
                current = current[t]
        else:
            output[self.tag] = self.text
        return output