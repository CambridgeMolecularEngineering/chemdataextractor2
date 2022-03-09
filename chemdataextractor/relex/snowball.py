# -*- coding: utf-8 -*-
"""
The Snowball Relationship Extraction algorithm
"""
import copy
import io
import os
import pickle
from collections import OrderedDict
from itertools import combinations

import numpy as np
import six
import pprint
from ..doc.document import Document, Paragraph
from ..model.base import BaseModel
from ..parse.auto import AutoSentenceParser
from ..doc.text import Sentence
from ..model import Compound, FloatType
from ..parse import Any, I, OneOrMore, Optional, R, W, ZeroOrMore, join, merge
from ..parse.cem import chemical_name
from .cluster import Cluster
from .entity import Entity
from .phrase import Phrase
from .relationship import Relation
from .utils import match, vectorise, KnuthMorrisPratt
from lxml import etree
from itertools import product
from ..parse.auto import BaseSentenceParser, BaseAutoParser
import logging

from os.path import basename
from playsound import playsound
import pkg_resources

log = logging.getLogger(__name__)

class Snowball(BaseSentenceParser):
    """
    Main Snowball class

    ::Usage: Define a Chemdataextractor Model
        ```snowball = Snowball(model=my_relationhip)```
        Then train the system on a corpus
        ```snowball.train(corpus)```
        This will generate an online training system

    ::params:

    For full detail see the associated paper: https://www.nature.com/articles/sdata2018111

        tc: The minimum confidence of a model in order to be accepted
        tsim: Minimum similarity between sentences in order for them to be clustered
        prefix_weight: The weight of the sentence prefix in the similarity calculation
        middle_weight: weight of middles in similarity calcs
        suffix_weight: weight of the suffix in similarity calcs
        prefix_length: Number of tokens to use in the phrase prefix
        suffix_length: number of tokens to use in phrase suffix
        learning_rate: How fast new confidences update based on new data (1 means new confidence is always taken, 0 means no update, )
    """

    def __init__(self, model,
                 tc=0.95,
                 tsim=0.95,
                 prefix_weight=0.1,
                 middle_weight=0.8,
                 suffix_weight=0.1,
                 prefix_length=1,
                 suffix_length=1,
                 learning_rate=0.5,
                 max_candidate_combinations=400,
                 save_dir='chemdataextractor/relex/data/',
                 play_sound=False):

        self.model = model
        self.relations = []
        self.phrases = []
        self.clusters = []
        self.cluster_counter = 0
        self.sentences = []
        self.max_candidate_combinations = max_candidate_combinations
        self.save_dir = save_dir
        self.save_file_name = model.__name__
        self.play_sound = play_sound


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

    def set_learning_rate(self, alpha):
        self.learning_rate =  alpha
        for cluster in self.clusters:
            cluster.learning_rate = alpha
        return

    def train(self, corpus, skip=0):
        """train the snowball algorithm on a specified corpus

        Arguments:
            corpus {str or list} -- path to a corpus of documents or list of training sentences
        """
        if isinstance(corpus, str):
            corpus_list = os.listdir(corpus)
            for i, file_name in enumerate(corpus_list[skip:]):
                print('{}/{}:'.format(i + skip + 1, len(corpus_list)), ' ', file_name)
                f = os.path.join(corpus, file_name)
                self.train_from_file(f)
        else:
            assert(isinstance(corpus, list))
            for s in corpus[skip:]:
                if isinstance(s, Sentence):
                    self.train_from_sentence(s)
                elif isinstance(s, Document):
                    self.train_from_document(s)
        return

    def train_from_file(self, filename):
        """Train Snowball from the elements of a file

        Arguments:
            f {str} -- the file path to parse
        """
        f = open(filename, 'rb')
        d = Document().from_file(f)

        # if 'train_from_document' found any candidates, print the file to a log so that
        # files used for training are saved automatically
        f_log = open('snowball_training_set.txt', 'a')
        if self.train_from_document(d):
            print(basename(filename), file=f_log)
        f_log.close()
        f.close()
        return

    def train_from_document(self, d):
        """Train Snowball from a Document object

        Arguments:
            d {str} -- the document to parse
        """
        candidate_found = False
        for p in d.paragraphs:
            for s in p.sentences:
                # skip sentence if it is too long
                if s.end - s.start > 300:
                    continue
                sent_definitions = s.definitions
                if sent_definitions:
                    self.model.update(sent_definitions)
                if self.train_from_sentence(s):
                    # return 'True if there was a Snowball candidate in the document
                    candidate_found = True
        self.model.reset_updatables()
        return candidate_found

    def train_from_sentence(self, s):
        """Train Snowball from a single sentence

        Arguments:
            s {[type]} -- [description]
        """
        candidate_dict = {}
        candidate_relationships = self.candidates(s.tokens)
        candidate_found = False
        if len(candidate_relationships) > 0:
            candidate_found = True
            print("\n\n")
            print(s)
            print('\n')
            for i, candidate in enumerate(candidate_relationships):
                candidate_dict[str(i)] = candidate
                print("Candidate " + str(i) + ' ' + str(candidate) + '\n')

            if self.play_sound:
                sound_file = pkg_resources.resource_filename('chemdataextractor', 'eval/sound.mp3')
                playsound(sound_file)
            res = six.moves.input("...: ").replace(' ', '')
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
        return candidate_found
    
    def required_fulfilled(self, model, entities_dict):
        """Recursive check for requiredd entities on nested models

        Args:
            model ([type]): [description]
            entities_dict ([type]): [description]
        """
        model_name = model.__name__.lower()
        for field in model.fields:
            # print(model_name, field)
            if hasattr(model.fields[field], 'model_class'):
                # print(field, "is a submodel, required = ", model.fields[field].required)
                if model.fields[field].required and not self.required_fulfilled(model.fields[field].model_class, entities_dict):
                    return False
            else:
                if model.fields[field].required and not model_name + '__' + field in entities_dict.keys():
                    # print("Model %s missing field %s" % (model_name, field))
                    return False
        return True
    
    def filter_incomplete(self, model, entities_dict):
        """ Remove entities from the dict if the relationship isnt complete """
        model_name = model.__name__.lower()
        for field in model.fields:
            if hasattr(model.fields[field], 'model_class'):
                entities_dict = self.filter_incomplete(model.fields[field].model_class, entities_dict)
            else:
                if model.fields[field].required and not model_name + '__' + field in entities_dict.keys():
                    # If the field is required by the model, but its not in the entities dict
                    # print("Entities dict %s missing field %s" % (model_name, field))
                    # Delete all fields of this model from entities_dict
                    key = model_name + '__'
                    dict_keys = [ i for i in entities_dict.keys()]
                    for entity_key in dict_keys:
                        if entity_key.startswith(key):
                            entities_dict.pop(entity_key, None)
                    break

        return entities_dict


    def candidates(self, tokens):
        """Find all candidate relationships of self.model within a sentence

        Arguments:
            s -- ChemdataExtractor.elements.Sentence -- the sentence to parse
        Returns
            relations {list} -- list of relations found in the text
        """
        entities_dict = {}
        candidate_relationships = []

        # Scan the tagged tokens with the parser
        detected = []

        #: Uses the default autosentenceparser to retrieve candidates
        sentence_parser = AutoSentenceParser(lenient=True)
        all_models = list(set(self.model.flatten()))
        for model in all_models:
            # Skip the compound model
            if model.__name__ == 'Compound':
                continue
            # print(model.__name__)
            sentence_parser.model = model
            for result in sentence_parser.root.scan(tokens):
                if result:
                    # print(etree.tostring(result[0]))
                    for entity in self.retrieve_entities(model, result[0]):
                        # print(entity)
                        # print("\n")
                        detected.append(entity)

        if not detected:
            return []
        detected = list(set(detected))  # Remove duplicate entries (handled by indexing)
        # print(detected)
        toks = [tok[0] for tok in tokens]
        for text, tag, parse_expression in detected:
            text_length = len(text.split(' '))
            pattern = [s[0] for s in Sentence(text).tokens]
            text_length = len(pattern)
            start_indices = [s for s in KnuthMorrisPratt(toks, pattern)]

            if isinstance(tag, tuple):
                tag = '__'.join(tag)

            # Add to dictionary  if it doesn't exist
            if tag not in entities_dict.keys():
                entities_dict[tag] = []
            entities = [Entity(text, tag, parse_expression, index, index + text_length) for index in start_indices]

            # Add entities to dictionary if new
            for entity in entities:
                if entity not in entities_dict[tag]:
                    entities_dict[tag].append(entity)

        for k in entities_dict.keys():
            entities = entities_dict[k]
            if len(entities_dict[k]) > 1:
                to_pop = []
                for i in range(len(entities)):
                    for j in range(i+1, len(entities)):
                        if entities[i].start == entities[j].start:
                            to_pop.append([i, j][np.argmin([entities[i].end, entities[j].end])])
                for p in to_pop:
                    entities_dict[k].pop(p)

        # Filter out incomplete models
        entities_dict = self.filter_incomplete(self.model, entities_dict)

        # jm2111, Fixed check for required fields
        if not self.required_fulfilled(self.model, entities_dict):
            return []

        # print("\n", entities_dict, "\n")

        # Construct all valid combinations of entities
        all_entities = [e for e in entities_dict.values()]
        # Intra-Candidate sorting (within each candidate)
        for i in range(len(all_entities)):
            all_entities[i] = sorted(all_entities[i], key=lambda t: t.start)
        candidates = list(product(*all_entities))

        for candidate in candidates:
            lst = sorted(candidate, key=lambda t: t.start)
            candidate = tuple(lst)

            # Remove candidates that are not valid (if a token has two different tags at the same location)
            r = Relation(candidate, confidence=0)
            # print(r)
            if r.is_valid():
                # print(candidate, "is valid", "\n")
                candidate_relationships.append(r)
        return candidate_relationships

    def retrieve_entities(self, model, result):
        """Recursively retrieve the entities from a parse result for a given model

        Arguments:
            result {lxml.etree.element} -- The parse result
        """
        if isinstance(result, list):
            for r in result:
                for entity in self.retrieve_entities(model, r):
                    yield entity
        else:
            for tag, field in model.fields.items():
                #: Nested models
                if hasattr(field, 'model_class'):
                    for nested_entity in self.retrieve_entities(field.model_class, result.xpath('./' + tag)):
                        yield nested_entity
                else:
                    text_list = result.xpath('./' + tag + '/text()')
                    for text in text_list:
                        yield (text, (model.__name__.lower(), tag), field.parse_expression)

    def update(self, sentence_tokens, relations=[]):
        """Update the learned extraction pattern clusters based on the incoming sentence and relation

        Arguments:
            sentence_tokens {list} -- the sentence tokenised
            relation {list} -- The Relation objects that are in the sentence
        """
        #: Create a new phrase from the sentence and corresponding relations
        new_phrase = Phrase(sentence_tokens, relations, self.prefix_length, self.suffix_length)
        # print("New Phrase", new_phrase)
        self.cluster(new_phrase)
        self.save()
        return

    def cluster(self, phrase):
        """Assign a phrase object to a cluster

        Arguments:
            phrase {Phrase} -- The Phrase to cluster
        """
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
        self.cluster_counter -= 1
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

                # Check the level of similarity to the cluster pattern
                similarity = match(phrase, cluster, self.prefix_weight, self.middle_weight, self.suffix_weight)

                if similarity >= self.minimum_cluster_similarity_score:
                    cluster.add_phrase(phrase)
                    phrase_added = True

        if phrase_added is False:
            self.cluster_counter += 1
            # create a new cluster
            new_cluster = Cluster(str(self.cluster_counter), learning_rate=self.learning_rate)
            new_cluster.add_phrase(phrase)
            self.clusters.append(new_cluster)

        return

    #: Override from BaseSentenceParser
    def parse_sentence(self, sentence):
        """Parse a Sentence object probabilistically using the Snowball Method

        Arguments:
            sentence -- The sentence
        Returns:
            The matching records
        """
        tokens = sentence.tokens
        # print("\n\nParsing sentece", ' '.join([t[0] for t in tokens]))
        # Use the default tagger to find candidate relationships
        candidate_relations = self.candidates(tokens)
        # print("Candidates", candidate_relations)
        num_candidates = len(candidate_relations)
        all_combs = []
        unique_names = set()
        for i in candidate_relations:
            for j in i.entities:
                if j.tag == 'compound__names':
                    unique_names.add(j.text)

        number_of_unique_name = len(unique_names)
        product = num_candidates * number_of_unique_name
        if product <= self.max_candidate_combinations:
            all_combs = [i for r in range(1, number_of_unique_name + 1) for i in combinations(candidate_relations, r)]


        # Create a candidate phrase for each possible combination
        all_candidate_phrases = []
        for combination in all_combs:
            rels = [r for r in combination]
            new_rels = copy.copy(rels)

            candidate_phrase = Phrase([t[0] for t in tokens], new_rels, self.prefix_length, self.suffix_length)
            all_candidate_phrases.append(candidate_phrase)

        # Only pick the phrase with the best confidence score
        best_candidate_phrase = None
        best_candidate_cluster = None
        best_candidate_phrase_score = 0

        for candidate_phrase in all_candidate_phrases:
            # print("Evaluating candidate", candidate_phrase)
            # For each cluster
            # Compare the candidate phrase to the cluster extraction patter
            best_match_score = 0
            best_match_cluster = None
            confidence_term = 1
            for cluster in self.clusters:
                if candidate_phrase.order != cluster.order:
                    continue
                match_score = match(candidate_phrase, cluster, self.prefix_weight, self.middle_weight, self.suffix_weight)
                # print("Match score %f" % match_score)
                if match_score >= self.minimum_cluster_similarity_score:
                    confidence_term *= (1.0 - (match_score * cluster.pattern.confidence))

                if match_score > best_match_score:
                    best_match_cluster = cluster
                    best_match_score = match_score

            # Confidence in the relationships we found
            phrase_confidence_score = 1.0 - confidence_term
            # print("Confidence %f" % phrase_confidence_score)

            if phrase_confidence_score > best_candidate_phrase_score:
                best_candidate_phrase = candidate_phrase
                best_candidate_phrase_score = phrase_confidence_score
                best_candidate_cluster = best_match_cluster

        if best_candidate_phrase and best_candidate_phrase_score >= self.minimum_relation_confidence:
            for candidate_relation in best_candidate_phrase.relations:
                candidate_relation.confidence = best_candidate_phrase_score
            # update the knowlegde base
            best_candidate_cluster.add_phrase(best_candidate_phrase)
            self.save()

            # print(best_candidate_phrase.relations)

            for relation in best_candidate_phrase.relations:
                for model in self.interpret(relation):
                    yield model

    def _get_data(self, field_name, field, relation_data):
        if hasattr(field, 'model_class'): # temperature, compound
            field_result = relation_data[field_name]  # {spec. val. units}

            if field_result is None and field.required and not field.contextual:
                raise TypeError('Could not find element for ' + str(field_name))
            elif field_result is None:
                return None

            field_data = {}
            for subfield_name, subfield in six.iteritems(field.model_class.fields):  # compound, names
                data = self._get_data(subfield_name, subfield, field_result)
                if data is not None:
                    field_data.update(data)
            field_object = field.model_class(**field_data)
            log.debug('Created for' + field_name)
            log.debug(field_object)
            return {field_name: field_object}
        elif hasattr(field, 'field'):
            # Case that we have listtype
            # Always only takes the first found one though
            field = field.field
            field_data = self._get_data(field_name, field, relation_data)
            if field_data is not None:
                if field_name not in field_data.keys() or field_data[field_name] is None:
                    return None
                field_data = [field_data[field_name]]
            elif field_data is None and field.required and not field.contextual:
                raise TypeError('Could not find element for ' + str(field_name))
            elif field_data is None:
                return None
            return {field_name: field_data}
        else:
            try:
                field_result = relation_data[field_name]
            except KeyError:
                return {}
            if field_result is None and field.required and not field.contextual:
                raise TypeError('Could not find element for ' + str(field_name))
            return {field_name: field_result}

    def interpret(self, relation):
        """Convert a detected relation to a ModelType Record

        Arguments:
            relation {[type]} -- [description]
        """
        # print("\n\n", "Interpreting")
        # Set the confidence field if not already set
        if not 'confidence' in self.model.fields.keys():
            setattr(self.model, 'confidence', FloatType())

        # Get the serialized relation data
        relation_data = relation.serialize()
        # print(relation_data)
        # Do conversions etc
        models = list(self.model.flatten())
        model_instances = []

        for model in models:
            model_name = model.__name__.lower()
            if model_name == self.model.__name__.lower():
                is_root_instance=True
            else:
                is_root_instance=False

            model_data = {}
            if model_name not in relation_data.keys():
                continue

            if 'specifier' in relation_data[model_name].keys():
                model_data['specifier'] = relation_data[model_name]['specifier']
            model_data['confidence'] = relation_data['confidence']

            if hasattr(model, 'dimensions') and not model.dimensions:
                # the specific entities of a DimensionlessModel are retrieved explicitly and packed into a dictionary
                raw_value = relation_data[model_name]['raw_value']
                value = self.extract_value(raw_value)
                error = self.extract_error(raw_value)

                model_data.update({"raw_value": raw_value,
                                        "value": value,
                                        "error": error})

            elif hasattr(model, 'dimensions') and model.dimensions:
                # the specific entities of a QuantityModel are retrieved explicitly and packed into a dictionary
                # print(etree.tostring(result))
                raw_value = relation_data[model_name]['raw_value']
                raw_units = relation_data[model_name]['raw_units']
                value = self.extract_value(raw_value)
                error = self.extract_error(raw_value)
                units = None
                try:
                    units = self.extract_units(raw_units, strict=True)
                except TypeError as e:
                    log.debug(e)
                model_data.update({"raw_value": raw_value,
                                        "raw_units": raw_units,
                                        "value": value,
                                        "error": error,
                                        "units": units})
            elif hasattr(model, 'category') and model.category:
                raw_value = relation_data[model_name]['raw_value']
                model_data.update({"raw_value": raw_value})

            for field_name, field in six.iteritems(model.fields):
                if field_name not in ['raw_value', 'raw_units', 'value', 'units', 'error', 'specifier', 'confidence']:
                    try:
                        data = self._get_data(field_name, field, relation_data)
                        if data is not None:
                            model_data.update(data)
                    # if field is required, but empty, the requirements have not been met
                    except (TypeError, KeyError) as e:
                        log.debug(self.model)
                        log.debug(e)
            model_instance = model(**model_data)
            model_instances.append((model_instance, is_root_instance))
        
        root_model_instance = [i[0] for i in model_instances if i[1]][0]
        for m in model_instances:
            if m[1]:
                continue
            root_model_instance.merge_all(m[0])
        

        # records the parser that was used to generate this record, can be used for evaluation
        root_model_instance.record_method = self.__class__.__name__
        yield root_model_instance
