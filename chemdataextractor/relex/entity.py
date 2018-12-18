# -*- coding: utf-8 -*-
"""
chemdataextractor.relex.pattern.py
Extraction pattern object
"""
import copy
import six

class Entity(object):
    """A base entity, the fundamental unit of a Relation

    """


    def __init__(self, text, tag, start ,end):
        """Create a new Entity

        Arguments:
            text {str} -- The text of the entity
            tag {ParseElement} -- How the Entity is identified
            start {int} -- The index of the Entity in tokens
            end {int} -- The end index of the entity in tokens
        """

        self.text = six.text_type(text)
        self.tag = copy.copy(tag)
        self.end = end
        self.start = start

    def __eq__(self, other):
        if self.text == other.text and self.end == other.end and self.start == other.start:
            return True
        else:
            return False

    def __repr__(self):
        return '(' + self.text + ',' + self.tag.name + ',' + str(self.start) + ',' + str(self.end) + ')'

    def __str__(self):
        return self.__repr__()
