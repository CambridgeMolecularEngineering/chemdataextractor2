from ..doc.document import Document, Paragraph
import os
from lxml import etree
from itertools import combinations

class Snowball(object):
    
    def __init__(self, parser):
        self.parser = parser
    
    def update(self, sentence, relation):
        with open('sentence.txt', 'a+') as wf:
            wf.write(' '.join(sentence.raw_tokens) + '\n')
        
        with open('relations.txt', 'a+') as wf:
            for el in relation:
                wf.write(str(el) + ',')
            wf.write('\n')

    
    def train(self, corpus):
        """train the snowball algorithm on a specified corpus
        
        Arguments:
            corpus {[type]} -- [description]
        """
        for file_name in os.listdir(corpus):
            print(file_name)
            try:
                f = open(corpus + file_name, 'rb')
                # test = ['Sr2FeMoO6, which exhibits an exceptionally high ferromagnetic Curie temperature of 416 K']
                d = Document().from_file(f)
                for p in d.paragraphs:
                    for s in p.sentences:
                        #print(s)
                        for result in self.parser.scan(s.tagged_tokens):
                            #print(etree.tostring(result[0]))
                            compounds = result[0].xpath('./cem/name/text()')
                            specifiers = result[0].xpath('./specifier/text()')
                            values = result[0].xpath('./value/text()')
                            units = result[0].xpath('./units/text()')

                            #print(compound, value, units, specifier)
                            if compounds and specifiers and values and units:
                                all_entities = compounds + specifiers + values + units
                                combs = [m for r in range(4, len(all_entities) + 1)
                                        for m in combinations(all_entities, r)]
                                
                                i = 0
                                print(s)
                                candidates = {}
                                for c in combs:
                                    if not any(i in compounds for i in c):
                                        continue
                                    if not any(i in specifiers for i in c):
                                        continue
                                    if not any(i in values for i in c):
                                        continue
                                    if not any(i in units for i in c):
                                        continue
                                    candidates[str(i)] = c
                                    print("Candidate " + str(i))
                                    print(c)
                                    i += 1

                                res = input("...: ")
                                if res == 'n':
                                    continue
                                elif res in candidates.keys():
                                    self.update(s, candidates[res])
                                else:
                                    continue
            except Exception as e:
                print(e)
                continue


