# -*- coding: utf-8 -*-
"""
Extraction pattern object
"""
import copy
import six

class Entity(object):
    """A base entity, the fundamental unit of a Relation

    """


    def __init__(self, text, tag, parse_expression, start ,end):
        """Create a new Entity

        Arguments:
            text {str} -- The text of the entity
            tag {str or tuple} -- How the Entity is identified
            start {int} -- The index of the Entity in tokens
            end {int} -- The end index of the entity in tokens
        """

        self.text = six.text_type(text)
        self.tag = tag
        self.parse_expression = copy.copy(parse_expression)
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
