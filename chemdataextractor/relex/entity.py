

class Entity(object):
    """ Individual instance of a chemical entity """

    def __init__(self, text, specifier, start, end):
        self.text = text
        self.specifier = specifier
        self.start = start
        self.end = end

    def __str__(self):
        return self.text