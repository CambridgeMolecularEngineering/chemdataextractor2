class ChemicalRelationship(object):

    def __init__(self, entities, parser):
        self.entities = entities
        self.parser = parser
    
    def get_candidiates(self, tokens):
        """Find all candidate relationships of this type within a sentence
        
        Arguments:
            tokens {[type]} -- [description]
        """
        # Scan the tagged tokens with the parser
        for result in self.parser.scan(tokens):
            entities_dict = {} 
            for e in self.entities:
                text = result[0].xpath('./' + e + '/text()')
                if not text:
                    continue
                
                entity = (result[0].xpath('./' + e + '/text()'), result[1], result[2])

                if e not in entities_dict.keys():
                    entities_dict[e] = []
                    
                if entity not in entities_dict[e]:
                    entities_dict[e].append(entity)

        # check all required entities are present
        if not all(e in entities_dict.keys() for e in self.entities):
            return []
        


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


