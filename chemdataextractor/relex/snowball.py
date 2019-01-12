# -*- coding: utf-8 -*-
"""
Chemdataextractor.relex.snowball

The Snowball Relationship Extraction algorithm
"""
import copy
import os
import pickle
import six
from itertools import combinations

import numpy as np
import io

from ..parse import (Any, I, OneOrMore, Optional, R, W,
                     ZeroOrMore, join, merge)

from ..doc.document import Document, Paragraph
from ..doc.text import Sentence
from ..model import Compound
from ..parse.cem import chemical_name
from .cluster import Cluster
from .entity import Entity
from .phrase import Phrase
from .relationship import Relation
from .utils import match


class Snowball(object):
    """Main Snowball class

    ::Usage: Define a ChemicalRelationship (see relex.relationship)
        ```snowball = Snowball(relationship=my_relationhip)```
        Then train the system on a corpus
        ```snowball.train(corpus)```
        This will generate an online training system

    ::params:
    For full detail see the associated paper: https://www.nature.com/articles/sdata2018111
        tc: The minimum confidence of a relationship in order to be accepted
        tsim: Minimum similarity between sentences in order for them to be clustered
        prefix_weight: The weight of the sentence prefix in the similarity calculation
        middle_weight: weight of middles in similarity calcs
        suffix_weight: weight of the suffix in similarity calcs
        prefix_length: Number of tokens to use in the phrase prefix
        suffix_length: number of tokens to use in phrase suffix
        learning_rate: How fast new confidences update based on new data (1 means new confidence is always taken, 0 means no update, )
    """

    def __init__(self, relationship,
                 tc=0.95,
                 tsim=0.95,
                 prefix_weight=0.1,
                 middle_weight=0.8,
                 suffix_weight=0.1,
                 prefix_length=1,
                 suffix_length=1,
                 learning_rate=0.5,
                 max_candidate_combinations=400):
        self.relationship = relationship
        self.relations = []
        self.phrases = []
        self.clusters = []
        self.cluster_counter = 0
        self.sentences = []
        self.max_candidate_combinations = max_candidate_combinations
        self.save_dir = 'chemdataextractor/relex/data/'
        self.save_file_name = relationship.name

        # params
        if not 0 <= tc <= 1.0:
            raise ValueError("Tc must be between 0 and 1")

        if not 0 <= tsim <= 1.0:
            raise ValueError("Tsim must be between 0 and 1")

        if not 0 <= learning_rate <= 1.0:
            raise ValueError("Learning rate must be between 0 and 1")

        if not 0 <= prefix_weight <= 1.0:
            raise ValueError("Prefix weight must be between 0 and 1")

        if not 0 <= middle_weight <= 1.0:
            raise ValueError("middle_weight must be between 0 and 1")

        if not 0 <= suffix_weight <= 1.0:
            raise ValueError("suffix weight must be between 0 and 1")

        self.minimum_relation_confidence = tc
        self.minimum_cluster_similarity_score = tsim
        self.prefix_weight = prefix_weight
        self.middle_weight = middle_weight
        self.suffix_weight = suffix_weight
        self.prefix_length = prefix_length
        self.suffix_length = suffix_length
        self.learning_rate = learning_rate

    @classmethod
    def load(cls, path):
        """Load a snowball instance from file

        Arguments:
            path {str} -- path to the pkl file

        Returns:
            self -- A Snowball Instance
        """

        f = open(path, 'rb')
        return pickle.load(f)

    def update(self, sentence_tokens, relations=[]):
        """Update the learned extraction pattern clusters based on the incoming sentence and relation

        Arguments:
            sentence_tokens {list} -- the sentence tokenised
            relation {list} -- The Relation objects that are in the sentence
        """
        new_phrase = Phrase(sentence_tokens, relations, self.prefix_length, self.suffix_length)
        self.cluster(new_phrase)
        self.save()
        return

    def save(self):
        """ Write all snowball settings to file for loading later"""
        save_dir = self.save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        with open(save_dir + self.save_file_name + '.pkl', 'wb') as f:
            pickle.dump(self, f)

        with io.open(save_dir + self.save_file_name + '_clusters.txt', 'w+', encoding='utf-8') as f:
            s = "Cluster set contains " + \
                six.text_type(len(self.clusters)) + " clusters."
            f.write(s + "\n")
            for c in self.clusters:
                s = "Cluster " + six.text_type(c.label) + " contains " + six.text_type(
                    len(c.phrases)) + " phrases"
                f.write(s + "\n")
                for phrase in c.phrases:
                    f.write("\t " + phrase.full_sentence + "\n")
                f.write(u"The cluster centroid pattern is: ")
                p = c.pattern
                f.write(six.text_type(p.to_string()) +
                        " with confidence score " + six.text_type(p.confidence) + "\n")

        with io.open(save_dir + self.save_file_name + '_patterns.txt', 'w+', encoding='utf-8') as f:
            for c in self.clusters:
                p = c.pattern
                f.write(six.text_type(p.to_string()) +
                        " with confidence score " + str(p.confidence) + "\n\n")

        with io.open(save_dir + self.save_file_name + '_relations.txt', 'w+', encoding='utf-8') as wf:
            for c in self.clusters:
                for phrase in c.phrases:
                    for relation in phrase.relations:
                        wf.write(six.text_type(relation) + " Confidence:  " + six.text_type(relation.confidence) + '\n')

        return

    def cluster(self, phrase):
        """Assign a phrase object to a cluster

        Arguments:
            phrase {Phrase} -- The Phrase to cluster
        """

        # If no clusters, create a new one
        if len(self.clusters) == 0:
            cluster0 = Cluster(str(self.cluster_counter), learning_rate=self.learning_rate)
            cluster0.add_phrase(phrase)
            self.clusters.append(cluster0)
        else:
            # Use a single pass classification algorithm to classify
            self.classify(phrase)
        return

    def delete_cluster(self, idx):
        """Delete all data associated with a cluster

        Arguments:
            idx {int} -- Cluster to delete
        """
        to_del = self.clusters[idx]
        del to_del
        return

    def classify(self, phrase):
        """
        Assign a phrase to clusters based on similarity score using single pass classification
        :param phrase: Phrase object
        :return:
        """
        phrase_added = False
        for cluster in self.clusters:
            # Only compare clusters that have the same ordering of entities
            if phrase.order == cluster.order:
                # vectorise the phrase using this cluster dictionary
                cluster.vectorise(cluster.pattern)
                cluster.vectorise(phrase)

                # Check the level of similarity to the cluster pattern
                similarity = match(phrase, cluster.pattern)

                if similarity >= self.minimum_cluster_similarity_score:
                    cluster.add_phrase(phrase)
                    phrase_added = True
                else:
                    phrase.reset_vectors()
                    continue

        if phrase_added is False:
            # Create a new cluster
            self.cluster_counter += 1
            # create a new cluster
            new_cluster = Cluster(str(self.cluster_counter), learning_rate=self.learning_rate)
            new_cluster.add_phrase(phrase)
            self.clusters.append(new_cluster)
        return

    def extract(self, s):
        """Retrieve probabilistic relationships from a sentence

        Arguments:
            s {Sentence} -- The Sentence object to extract from
        Returns:
            relations -- The Relations found in the sentence
        """
        # Use the default tagger to find candidate relationships
        candidate_relations = self.relationship.get_candidates(s.tagged_tokens)
        num_candidates = len(candidate_relations)
        all_combs = []
        unique_names = set()
        for i in candidate_relations:
            for j in i.entities:
                if j.tag.name == 'name':
                    unique_names.update(j.text)

        number_of_unique_name = len(unique_names)
        product = num_candidates * number_of_unique_name
        if product <= self.max_candidate_combinations:
            all_combs = [i for r in range(1, number_of_unique_name + 1) for i in combinations(candidate_relations, r)]
        # Create a candidate phrase for each possible combination
        all_candidate_phrases = []
        for combination in all_combs:
            rels = [r for r in combination]
            new_rels = copy.copy(rels)

            candidate_phrase = Phrase(s.raw_tokens, new_rels, self.prefix_length, self.suffix_length)
            all_candidate_phrases.append(candidate_phrase)

        # Only pick the phrase with the best confidence score
        best_candidate_phrase = None
        best_candidate_cluster = None
        best_candidate_phrase_score = 0

        for candidate_phrase in all_candidate_phrases:
            # For each cluster
            # Compare the candidate phrase to the cluster extraction patter
            best_match_score = 0
            best_match_cluster = None
            confidence_term = 1

            for cluster in self.clusters:
                if candidate_phrase.order != cluster.order:
                    continue

                cluster.vectorise(candidate_phrase)
                cluster.vectorise(cluster.pattern)

                match_score = cluster.get_phrase_match_score(candidate_phrase)
                if match_score >= self.minimum_cluster_similarity_score:
                    confidence_term *= (1.0 - (match_score * cluster.pattern.confidence))
                if match_score > best_match_score:
                    best_match_cluster = cluster
                    best_match_score = match_score
                candidate_phrase.reset_vectors()

            # Confidence in the relationships we found
            phrase_confidence_score = 1.0 - confidence_term

            if phrase_confidence_score > best_candidate_phrase_score:
                best_candidate_phrase = candidate_phrase
                best_candidate_phrase_score = phrase_confidence_score
                best_candidate_cluster = best_match_cluster

        if best_candidate_phrase and best_candidate_phrase_score >= self.minimum_relation_confidence:
            for candidate_relation in best_candidate_phrase.relations:
                candidate_relation.confidence = phrase_confidence_score
            # update the knowlegde base
            best_candidate_cluster.add_phrase(best_candidate_phrase)
            self.save()
            return best_candidate_phrase.relations

    def parse(self, filename):
        """Parse the sentences of a file

        Arguments:
            f {str} -- the file path to parse
        """
        f = open(filename, 'rb')
        d = Document().from_file(f)
        for p in d.paragraphs:
            for s in p.sentences:
                candidate_dict = {}
                candidate_relationships = self.relationship.get_candidates(s.tagged_tokens)
                if len(candidate_relationships) > 0:
                    print("\n\n")
                    print(s)
                    print('\n')
                    for i, candidate in enumerate(candidate_relationships):
                        candidate_dict[str(i)] = candidate
                        print("Candidate " + str(i) + ' ' + str(candidate) + '\n')

                    res = six.moves.input("...: ")
                    if res:
                        chosen_candidate_idx = res.split(',')
                        chosen_candidates = []
                        for cci in chosen_candidate_idx:
                            if cci in candidate_dict.keys():
                                cc = candidate_dict[cci]
                                cc.confidence = 1.0
                                chosen_candidates.append(cc)
                        if chosen_candidates:
                            self.update(s.raw_tokens, chosen_candidates)

        f.close()
        return

    def train(self, corpus):
        """train the snowball algorithm on a specified corpus

        Arguments:
            corpus {str} -- path to a corpus of documents
        """
        corpus_list = os.listdir(corpus)
        for i, file_name in enumerate(corpus_list):
            print('{}/{}:'.format(i + 1, len(corpus_list)), ' ', file_name)
            f = os.path.join(corpus, file_name)
            self.parse(f)
        return
