from ..doc.document import Document, Paragraph
from ..doc.text import Sentence
import os
from ..parse.cem import chemical_name
from lxml import etree
from .phrase import Phrase
from .cluster import Cluster
from itertools import combinations
import numpy as np
import copy
from .relationship import Relationship
from .entity import Entity
from chemdataextractor.parse import R, I, W, Optional, merge, join, OneOrMore, Any, ZeroOrMore
import pickle

def match(pi, pj, prefix_weight=0.1, middle_weight=0.8, suffix_weight=0.1):
    """ Compute match between phrases using a dot product of vectors
    :param pi Phrase or pattern
    :param pj phrase or pattern
    # add weights to dot products to put more emphasis on matching the middles
    """

    if pi.order != pj.order:
        return 0

    #print(pi.as_string(), pj.as_string())

    number_of_middles_i = pi.number_of_entities - 1
    number_of_middles_j = pj.number_of_entities - 1
    if number_of_middles_i != number_of_middles_j:
        return 0

    prefix_i = pi.elements['prefix']['1']['vector']
    middles_i = [pi.elements['middles'][m]['vector']
                 for m in pi.elements['middles'].keys()]
    suffix_i = pi.elements['suffix']['1']['vector']

    prefix_j = pj.elements['prefix']['1']['vector']
    middles_j = [pj.elements['middles'][m]['vector']
                 for m in pj.elements['middles'].keys()]
    suffix_j = pj.elements['suffix']['1']['vector']

    if len(prefix_i) == 0 and len(prefix_j) == 0:
        prefix_dot_prod = 1.0
    else:
        prefix_dot_prod = np.dot(prefix_i, prefix_j)

    middle_dot_prod = []
    for i in range(0, len(middles_i)):
        if len(middles_i[i]) == 0 and len(middles_j[i]) == 0:
            middle_dot_prod.append(1.0)
        elif len(middles_i[i]) != len(middles_j[i]):
            middle_dot_prod.append(0)
        else:
            #print(i, pi.elements['middles'], pj.elements['middles'])
            #print(middles_i, middles_j)
            m_dot = np.dot(middles_i[i], middles_j[i])
            middle_dot_prod.append(m_dot)

    if len(suffix_i) == 0 and len(suffix_j) == 0:
        suffix_dot_prod = 1.0
    else:
        suffix_dot_prod = np.dot(suffix_i, suffix_j)

    sim = (prefix_weight * prefix_dot_prod) + ((middle_weight/number_of_middles_j)
                                               * sum(middle_dot_prod)) + (suffix_weight * suffix_dot_prod)
    return sim

    


class Snowball(object):
    
    def __init__(self, relationship, tc=0.9, update_param=1, tsim=0.9, prefix_weight=0.1, middle_weight=0.8, suffix_weight=0.1):
        self.relationship = relationship
        self.relations = []
        self.phrases = []
        self.clusters = []
        self.cluster_counter = 0
        self.sentences = []
        self.save_dir = 'chemdataextractor/relex/data/'
        self.save_file_name = 'test'

        # params
        self.minimum_relation_confidence = tc
        self.update_param = update_param
        self.minimum_cluster_similarity_score = tsim
        self.prefix_weight = prefix_weight
        self.middle_weight = middle_weight
        self.suffix_weight = suffix_weight

    
    def update(self, sentence_tokens, relations=[]):
        """Update the learned extraction pattern clusters based on the incoming sentence and relation
        
        Arguments:
            sentence {[type]} -- [description]
            relation {[type]} -- [description]
        """
        
        specifier = (I('Curie') + I('temperature') + R('^T(C|c)(urie)?'))('specifier').add_action(join)
        units = (R('^[CFK]\.?$'))('units').add_action(merge)
        value = (R('^\d+(\.\,\d+)?$'))('value')
        # Create a phrase object from the sentence
        # Relations is a list of (text, tag, start, end) tuples describing the relationships present in the sentences
        s = Sentence('here BiFeO3 and LaFeO3 have curie temperature Tc of 600 and 700 K, respectively')
        r1 = Relationship([Entity('BiFeO3', chemical_name, 1, 2), Entity('curie temperature Tc', specifier, 5, 8), Entity('600', value, 9, 10), Entity('K', units, 12, 13)], confidence=1.0)
        r2 = Relationship([Entity('LaFeO3', chemical_name, 3, 4), Entity('curie temperature Tc', specifier, 5, 8), Entity('700', value, 11, 12), Entity('K', units, 12, 13)], confidence=1.0)
        relations = [r1, r2]
        # relations = Relationship([Entity('BiFeO3', chemical_name, 1, 2), Entity('Curie Temperature Tc', specifier, 6, 9), Entity('600', value, 11, 12), Entity('K', units, 15, 16)])]
        new_phrase = Phrase(s.raw_tokens, relations)
        print("Created Phrase", new_phrase)
        self.cluster(new_phrase)
        print(self.clusters)
        self.update_confidence_scores()
        self.save()
        return
    
    def update_confidence_scores(self):
        """Determine the confidence scores for all patterns in all clusters
            Do this by comparing all patterns to all previously seen sentences and determining the number of correct matches
        """
        for cluster in self.clusters:
            cluster.update_pattern_confidence()
        return

    
    def save(self):
        """ Write all snowball settings to file for loading later"""
        save_dir = self.save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        with open(save_dir + self.save_file_name + '.pkl', 'wb') as f:
            pickle.dump(self, f)

        with open(save_dir + self.save_file_name + '_clusters.txt', 'w+') as f:
            s = "Cluster set contains " + \
                str(len(self.clusters)) + " clusters."
            f.write(s + "\n")
            for c in self.clusters:
                s = "Cluster " + str(c.label) + " contains " + str(
                    len(c.phrases)) + " phrases"
                f.write(s + "\n")
                for phrase in c.phrases:
                    f.write("\t " + phrase.full_sentence + "\n")
                f.write("The cluster centroid pattern is: ")
                p = c.pattern
                f.write(str(p.to_string()) +
                        " with confidence score " + str(p.confidence) + "\n")

        with open(save_dir + self.save_file_name + '_patterns.txt', 'w+') as f:
            for c in self.clusters:
                p = c.pattern
                f.write(str(p.to_string()) +
                        " with confidence score " + str(p.confidence) + "\n\n")

        with open(save_dir + self.save_file_name + '_relations.txt', 'w+') as f:
            for r in self.relations:
                if r.found:
                    rel_str = "(" + r.compound + ", " + r.value + \
                        ", " + r.units + ", " + str(r.confidence) + ")"
                    f.write(rel_str + "\n")
                    for p in r.phrases:
                        for elem in p.as_tokens():
                            if isinstance(elem, list):
                                for el in elem:
                                    f.write(el + ' ')
                            else:
                                f.write(elem + ' ')
                        f.write('\n')
                    f.write('\n')

        return
    
    def cluster(self, phrase):
        # If no clusters, create a new one
        if len(self.clusters) == 0:
            cluster0 = Cluster(str(self.cluster_counter))
            cluster0.add_phrase(phrase)
            self.clusters.append(cluster0) 
        else:
            self.classify(phrase)
        return

    def classify(self, phrase):
        """
        Assign a phrase to clusters based on similarity score
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
            new_cluster = Cluster(str(self.cluster_counter))
            new_cluster.add_phrase(phrase)
            self.clusters.append(new_cluster)
        return

    
    def extract(self, s):
        """Retrieve candidate relationships from a sentence
        
        Arguments:
            r {[type]} -- [description]
        """
        # Create a new phrase object 
        candidate_relations = self.relationship.get_candidates(s.tagged_tokens)
        
        return



    def parse(self, filename):
        """Parse the sentences of a file
        
        Arguments:
            f {[type]} -- [description]
        """
        f = open(filename, 'rb')
        d = Document().from_file(f)
        for p in d.paragraphs:
            for s in p.sentences:
                candidate_dict = {}
                candidates = self.relationship.get_candidates(s.tagged_tokens)
                for i, candidate in enumerate(candidates):
                    candidates[str(i)] = candidate
                    print("Candidate " + str(i) + candidate)
                res = input("...: ")
                if res in candidate_dict.keys():
                    self.update(s.raw_tokens, candidates[res])
                else:
                    continue
        f.close()

    
    def train(self, corpus):
        """train the snowball algorithm on a specified corpus
        
        Arguments:
            corpus {[type]} -- [description]
        """
        for file_name in os.listdir(corpus):
            print(file_name)
            try:
                f = os.path.join(corpus, file_name)
                self.parse(f)
            except Exception as e:
                print(e)
                continue
        return


