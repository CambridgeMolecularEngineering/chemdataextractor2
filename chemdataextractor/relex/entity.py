

class Entity(object):
    """ Individual instance of a chemical entity """

    def __init__(self, text, specifier, start, end):
        self.text = text
        self.specifier = specifier
        self.start = start
        self.end = end

    def __str__(self):
        return self.text

class Relationship(object):
    """ Relationship object, consisting of all generated entity combinations"""

    def __init__(self, entities):
        self.entities = entities


#
# class DummyRelationship(object):
#     def __init__(self, iterable=(), **kwargs):
#         self.__dict__.update(iterable, **kwargs)
#
#
# class Relationship(DummyRelationship):
#     """ Proposed relationship between entities"""
#     def __init__(self, iterable=(), **kwargs):
#         super().__init__(iterable, **kwargs)


