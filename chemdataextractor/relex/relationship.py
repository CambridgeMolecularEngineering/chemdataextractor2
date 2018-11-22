from .entity import Entity
from itertools import combinations, product

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
            entities_dict = {} 
            for e in self.entities:
                text_list = result[0].xpath('./' + e + '/text()')
                for i, text in enumerate(text_list):
                    if not text:
                        continue

                    entity = Entity(text, e, i, i+1)  # Correct obtaining of token position?

                    if e not in entities_dict.keys():
                        entities_dict[e] = []

                    if entity not in entities_dict[e]:
                        entities_dict[e].append(entity)

        # check all required entities are present
        if not all(e in entities_dict.keys() for e in self.entities):
            return []

        # Construct all valid combinations of entities
        all_entities = [e for e in entities_dict.values()]
        candidates = list(product(*all_entities))
        candidate_entities = [Entity(c[0], c[1], c[2], c[3]) for c in candidates]
        return candidate_entities  # Change to return Entity objects? Could do as funcition of elements?


        # Generate all possible valid candidate relationships
        # i.e. every combination of entities that contains at least one of each
        
            # #print(compound, value, units, specifier)
            # if compounds and specifiers and values and units:
            #     all_entities = compounds + specifiers + values + units
            #     combs = [m for r in range(4, len(all_entities) + 1)
            #             for m in combinations(all_entities, r)]
                
            #     i = 0
            #     print(s)
            #     candidates = {}
            #     for c in combs:
            #         if not any(i in compounds for i in c):
            #             continue
            #         if not any(i in specifiers for i in c):
            #             continue
            #         if not any(i in values for i in c):
            #             continue
            #         if not any(i in units for i in c):
            #             continue


