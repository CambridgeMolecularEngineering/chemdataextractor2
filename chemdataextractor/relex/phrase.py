# -*- coding: utf-8 -*-
"""
Phrase object

"""
import re

class Phrase(object):

    def __init__(self, sentence_tokens, relations, prefix_length, suffix_length):
        """Phrase Object

        Class for handling which relations and entities appear in a sentence, the base type used for clustering and generating extraction patterns

        Arguments:
            sentence_tokens {[list} -- The sentence tokens from which to generate the Phrase
            relations {list} -- List of Relation objects to be tagged in the sentence
            prefix_length {int} -- Number of tokens to assign to the prefix
            suffix_length {int} -- Number of tokens to assign to the suffix
        """

        self.sentence_tokens = sentence_tokens
        self.full_sentence = ' '.join(sentence_tokens)

        self.cluster_assignments = set()  # Set of cluster labels, describing which clusters this belongs to
        self.number_of_entities = 0
        self.relations = relations
        self.elements = {}
        self.entities = []
        self.order = []
        self.prefix_length = prefix_length
        self.suffix_length = suffix_length
        if sentence_tokens and relations:
            self.create()

    def __repr__(self):
        return self.to_string()

    def to_string(self):
        output_string = ''
        output_string += ' '.join(self.elements['prefix']['tokens']) + ' '
        if isinstance(self.entities[0].tag, tuple):
            output_string += '(' + ', '.join([i for i in self.entities[0].tag]) + ') '
        else:
            output_string += '(' + self.entities[0].tag + ') '
        for i in range(0, self.number_of_entities - 1):
            output_string += ' '.join(self.elements['middle_' + str(i+1)]['tokens']) + ' '
            if isinstance(self.entities[i+1].tag, tuple):
                output_string += '(' + ', '.join([i for i in self.entities[i+1].tag]) + ') '
            else:
                output_string += '(' + self.entities[i+1].tag + ') '
        output_string = output_string
        output_string += ' '.join(self.elements['suffix']['tokens'])

        return output_string

    def create(self):
        """ Create a phrase from known relations"""
        sentence = self.sentence_tokens
        relations = self.relations
        entity_counter = {}
        # print("Creating phrase")

        combined_entity_list = []
        for relation in relations:
            # print(relation)
            for entity in relation:
                # print(entity)
                if entity in combined_entity_list:
                    continue
                else:
                    if entity.tag not in entity_counter.keys():
                        entity_counter[entity.tag] = 1
                    else:
                        entity_counter[entity.tag] += 1

                    # new_tag_name = entity.tag.split('-')[0] + '-' + str(entity_counter[entity.tag])
                    # # print(new_tag_name)
                    # entity.tag = new_tag_name
                    combined_entity_list.append(entity)

        # Number of entities
        self.number_of_entities = len(combined_entity_list)
        number_of_middles = self.number_of_entities - 1

        # Determine the entitiy ordering
        sorted_entity_list = sorted(combined_entity_list, key=lambda t: t.start)

        self.entities = sorted_entity_list

        # Create ordering
        self.order = [e.tag for e in self.entities]

        # Create the phrase elements, prefix, middles, suffix
        prefix_tokens = [t for t in sentence[sorted_entity_list[0].start - self.prefix_length:sorted_entity_list[0].start]]
        if len(prefix_tokens) == 0:
            prefix_tokens = ['<Blank>']
        self.elements['prefix'] = {'tokens': prefix_tokens}

        for m in range(0, number_of_middles):
            prev_entity_end = sorted_entity_list[m].end
            next_entitiy_start = sorted_entity_list[m+1].start
            middle_tokens = [t for t in sentence[prev_entity_end:next_entitiy_start]]
            if len(middle_tokens) == 0:
                middle_tokens = ['<Blank>']
            self.elements['middle_' + str(m+1)] = {'tokens': middle_tokens}

        suffix_tokens = [t for t in sentence[sorted_entity_list[-1].end:sorted_entity_list[-1].end+self.suffix_length]]
        if len(suffix_tokens) == 0:
            suffix_tokens = ['<Blank>']
        self.elements['suffix'] = {'tokens': suffix_tokens}

        return

    def reset_vectors(self):
        """ Set all element vectors to None"""
        for element in self.elements.keys():
            self.elements[element]['vector'] = None
        return
