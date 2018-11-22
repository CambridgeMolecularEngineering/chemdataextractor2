from .entity import Entity
from itertools import combinations, product
from collections import Counter
import copy


def KnuthMorrisPratt(text, pattern):

    '''Yields all starting positions of copies of the pattern in the text.
Calling conventions are similar to string.find, but its arguments can be
lists or iterators, not just strings, it returns all matches, not just
the first one, and it does not need the whole text in memory at once.
Whenever it yields, it will have read the text exactly up to and including
the match that caused the yield.'''

    # allow indexing into pattern and protect against change during yield
    pattern = list(pattern)

    # build table of shift amounts
    shifts = [1] * (len(pattern) + 1)
    shift = 1
    for pos in range(len(pattern)):
        while shift <= pos and pattern[pos] != pattern[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # do the actual search
    startPos = 0
    matchLen = 0
    for c in text:
        while matchLen == len(pattern) or \
              matchLen >= 0 and pattern[matchLen] != c:
            startPos += shifts[matchLen]
            matchLen -= shifts[matchLen]
        matchLen += 1
        if matchLen == len(pattern):
            yield startPos

class ChemicalRelationship(object):

    def __init__(self, entities, parser):
        self.entities = entities
        self.parser = parser

    def get_candidates(self, tokens):
        """Find all candidate relationships of this type within a sentence
        
        Arguments:
            tokens {[type]} -- [description]
        """
        candidate_relationships = []
        # Scan the tagged tokens with the parser
        detected = []
        for result in self.parser.scan(tokens):
            for e in self.entities:
                text_list = result[0].xpath('./' + e.name + '/text()')
                for i, text in enumerate(text_list):
                    if not text:
                        continue
                    detected.append((text, e))

        entities_dict = {}
        
        if not detected:
            return []

        # Find duplicate results
        occurrences = Counter(elem[0] for elem in detected)
        duplicates = [k for k, v in occurrences.items() if v > 1]
        detected = list(set(detected))  # Remove duplicate entries (handled by indexing)
        for text, tag in detected:
            text_length = len(text.split(' '))
            toks = [tok[0] for tok in tokens]
            start_indices = [s for s in KnuthMorrisPratt(toks, text.split(' '))]
            
            # Add specifier to dictionary  if it doesn't exist
            if tag.name not in entities_dict.keys():
                entities_dict[tag.name] = []

            # Keeps separate entities if tokens are duplicated
            entities = [Entity(text, tag, index, index+text_length) for index in start_indices]

            # Add entities to dictionary if new
            for entity in entities:
                if entity not in entities_dict[tag.name]:
                    entities_dict[tag.name].append(entity)

        # check all required entities are present
        if not all(e.name in entities_dict.keys() for e in self.entities):
            return []

        # Construct all valid combinations of entities
        all_entities = [e for e in entities_dict.values()]
        candidates = list(product(*all_entities))
        for candidate in candidates:
            candidate_relationships.append(Relationship(candidate, confidence=0))

        return candidate_relationships


class Relationship(object):

    def __init__(self, entities, confidence):
        self.entities = copy.copy(entities)
        self.confidence = confidence
    
    def __len__(self):
        return len(self.entities)
    
    def __getitem__(self, idx):
        return self.entities[idx]
    
    def __setitem__(self, idx, value):
        self.entities[idx] = value
    
    def __repr__(self):
        return '(' + ','.join([str(i) for i in self.entities]) + ')'
    
    def __eq__(self, other):
        # compare the text of all entities
        other_entities = other.entities
        for entity in self.entities:
            if not entity.text in [i.text for i in other_entities]:
                return False
        return True
    
    def __str__(self):
        return self.__repr__()