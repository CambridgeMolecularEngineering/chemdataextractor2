from .entity import Entity
from itertools import combinations, product
from collections import Counter


class ChemicalRelationship(object):

    def __init__(self, entities, parser):
        self.entities = entities
        self.parser = parser

    def get_candidates(self, tokens):
        """Find all candidate relationships of this type within a sentence
        
        Arguments:
            tokens {[type]} -- [description]
        """
        # Scan the tagged tokens with the parser

        for result in self.parser.scan(tokens):
            detected = []
            for e in self.entities:
                text_list = result[0].xpath('./' + e + '/text()')
                for i, text in enumerate(text_list):
                    if not text:
                        continue
                    detected.append((text, e))

            print(detected)

        entities_dict = {}

        # Find duplicate results
        occurrences = Counter(elem[0] for elem in detected)
        duplicates = [k for k, v in occurrences.items() if v > 1]

        detected = list(set(detected))  # Remove duplicate entries ( handled by indexing)
        for text, specifier in detected:
            indices = [i for i, token in enumerate(tokens) for word in text.split(' ') if word in token]

            # Add specifier to dictionary  if it doesn't exist
            if specifier not in entities_dict.keys():
                entities_dict[specifier] = []

            # Keeps separate entities if tokens are duplicated
            if text in duplicates:
                entities = [Entity(text, specifier, index, index) for index in indices]

            else:
                entities = [Entity(text, specifier, min(indices), max(indices))]

            # Add entities to dictionary if new
            for entity in entities:
                if entity not in entities_dict[specifier]:
                    entities_dict[specifier].append(entity)

        # check all required entities are present
        if not all(e in entities_dict.keys() for e in self.entities):
            return []

        # Construct all valid combinations of entities
        all_entities = [e for e in entities_dict.values()]
        candidates = list(product(*all_entities))
        return candidates


