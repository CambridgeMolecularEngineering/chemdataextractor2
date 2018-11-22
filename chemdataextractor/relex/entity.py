
import copy
class Entity(object):

    def __init__(self, text, tag, start ,end):
        self.text = text
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