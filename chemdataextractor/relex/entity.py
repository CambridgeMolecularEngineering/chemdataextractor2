

class Entity(object):
    """ Individual instance of a chemical entity """

    def __init__(self, text, tag, start, end):
        self.text = text
        self.tag = tag
        self.start = start
        self.end = end


class DummyRelationship(object):
    def __init__(self, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)


class Relationship(DummyRelationship):
    """ Proposed relationship between entities"""
    def __init__(self, iterable=(), **kwargs):
        super().__init__(iterable, **kwargs)


