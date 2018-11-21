from ..doc.document import Document, Paragraph
import os
from lxml import etree
from itertools import combinations

class Snowball(object):
    
    def __init__(self, relationship):
        self.relationship = relationship
    
    def update(self, sentence, relation):
        with open('sentence.txt', 'a+') as wf:
            wf.write(' '.join(sentence.raw_tokens) + '\n')
        
        with open('relations.txt', 'a+') as wf:
            for el in relation:
                wf.write(str(el) + ',')
            wf.write('\n')
        return
    
    def get_candidate_relations(self, r):
        """Retrieve candidate relationships from a tagged sentence
        
        Arguments:
            r {[type]} -- [description]
        """



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
                    self.update(s, candidates[res])
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


