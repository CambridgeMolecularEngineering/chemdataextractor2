# -*- coding: utf-8 -*-
"""
chemdataextractor.relex.phrase
Phrase object

"""
import re

class Phrase:

    def __init__(self, sentence_tokens, relations):
        """
        :param sentence: String of the sentence used to create phrase(s)
        :param matches: Dict containing relations and the associated compound/value/unit/specifier regex matches
        """
        self.sentence_tokens = sentence_tokens
        self.full_sentence = ' '.join(sentence_tokens)

        self.cluster_assignments = set()  # Set of cluster labels, describing which clusters this belongs to
        self.number_of_entities = 0
        self.relations = relations
        self.elements = {}
        self.entities = []
        self.order = []
        if sentence_tokens and relations:
            self.create()
    
    def __repr__(self):
        return self.to_string()
    
    def to_string(self):
        output_string = ''
        output_string += ' '.join(self.elements['prefix']['tokens']) + ' '
        output_string += self.entities[0].tag.name + ' '
        for i in range(0, self.number_of_entities - 1):
            output_string += ' '.join(self.elements['middle_' + str(i + 1)]['tokens']) + ' '
            output_string += self.entities[i + 1].tag.name + ' '
        output_string += ' '.join(self.elements['suffix']['tokens'])

        return output_string

    def create(self):
        """ Create a phrase from known relations"""
        sentence = self.sentence_tokens
        relations = self.relations
        entity_counter = {}
        print("Creating phrase")
        combined_entity_list = []
        for relation in relations:
            for entity in relation:

                if entity in combined_entity_list:
                    new_tag_name = entity.tag.name + '_' + str(entity_counter[entity.tag.name])
                    entity.tag.name = new_tag_name
                    continue
                else: 
                    if entity.tag.name not in entity_counter.keys():
                            entity_counter[entity.tag.name] = 1
                    else:
                        entity_counter[entity.tag.name] += 1
                    new_tag_name = entity.tag.name + '_' + str(entity_counter[entity.tag.name])
                    entity.tag.name = new_tag_name
                    combined_entity_list.append(entity)

        # Number of entities
        self.number_of_entities = len(combined_entity_list)
        number_of_middles = self.number_of_entities - 1

        # Determine the entitiy ordering
        sorted_entity_list = sorted(combined_entity_list, key=lambda t: t.start)

        print(sorted_entity_list)
        self.entities = sorted_entity_list
        
        # Create ordering
        self.order = [e.tag for e in self.entities]
        print(self.order)
        print(self.entities)

        # Create the phrase elements, prefix, middles, suffix
        self.elements['prefix'] = {'tokens': [t for t in sentence[:sorted_entity_list[0].start]]}


        for m in range(0, number_of_middles):
            prev_entity_end = sorted_entity_list[m].end
            next_entitiy_start = sorted_entity_list[m+1].start
            self.elements['middle_' + str(m+1)] = {'tokens': [t for t in sentence[prev_entity_end:next_entitiy_start]]}

        self.elements['suffix'] = {'tokens': [t for t in sentence[sorted_entity_list[-1].end:]]}

        return

    def reset_vectors(self):
        """ Set all element vectors to None"""
        for element in self.elements:
            for element_num in self.elements[element].keys():
                self.elements[element][element_num]['vector'] = None
        return

    def as_string(self):
        """

        :return: phrase object as a string
        """
        output_string = ''
        output_string += ' '.join(self.elements['prefix']['1']['tokens']) + ' '
        output_string += self.entities[0][1] + ' '
        for i in range(0, self.number_of_entities - 1):
            if str(i+1) in self.elements['middles'].keys():
                output_string += ' '.join(
                    self.elements['middles'][str(i + 1)]['tokens']) + ' '
            output_string += self.entities[i + 1][1] + ' '
        output_string += ' '.join(self.elements['suffix']['1']['tokens'])

        # replace troublesome characters
        output_string = output_string.replace('\n', ' ')
        # Possibly a hidden non breaking space
        output_string = output_string.replace(u'\u00A0', ' ')
        output_string = output_string.replace(u'\u2212', '-')
        output_string = output_string.replace(u'\u2009 ', ' ')

        output_string.replace('  ', ' ')

        return output_string

    def retrieve_relations(self):
        """ Use the entity tags to recover the related entities from this phrase """
        retrieved_relations = []
        number_of_units = self.order.count('3')
        # print(number_of_units)
        for i in self.entities:
            # print(i)
            for j in self.entities:
                # print(j)
                if i[1].startswith('<CEM') and j[1].startswith('<VALUE') and i[1][4] == j[1][6] and number_of_units == 1:
                    unit_index = self.order.index('3')
                    retrieved_relations.append(
                        [i[0], j[0], self.entities[unit_index][0]])
                elif i[1].startswith('<CEM') and j[1].startswith('<VALUE') and i[1][4] == j[1][6] and number_of_units != 1:
                    for k in self.entities:
                        if k[1].startswith('<UNIT') and k[1][5] == j[1][6] and k[1][5] == i[1][4]:
                            retrieved_relations.append([i[0], j[0], k[0]])
        # print(retrieved_relations)
        return retrieved_relations