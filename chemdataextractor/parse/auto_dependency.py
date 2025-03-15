# -*- coding: utf-8 -*-
"""
Parser for automatic parsing, without user-written parsing rules, implemeting the DepIE algorithm
"""
from .auto import AutoSentenceParser, match_dimensions_of, construct_unit_element
from ..model import ModelType
from .cem import cem, chemical_label, lenient_chemical_label
from .elements import Group
from .quantity import value_element
import copy
from lxml.builder import E


class _LabelledRange:
    """
    An internal class used to hold the text for results from ChemDataExtractor
    parse rules alongside their locations. Correctly handles subsentences,
    unlike a naive usage of the indices on the sentence.
    """

    def __init__(self, data, range_):
        self.data = data
        self.range = range_

    @classmethod
    def from_cde_result(cls, result, subsentence):
        start_index = subsentence.tokens[result[1]].index
        end_index = subsentence.tokens[result[2] - 1].index + 1
        return cls(result[0], (start_index, end_index))

    @classmethod
    def from_cde_results(cls, results, subsentence):
        return [cls.from_cde_result(result, subsentence) for result in results]

    def __hash__(self):
        return hash((str(self.data), self.range))

    def __eq__(self, other):
        if self.data == other.data and self.range == other.range:
            return True
        return False

    def __str__(self):
        return "_LabelledRange(data: {}, range:{}".format(self.data, self.range)

    def __repr__(self):
        return str(self)


class AutoDependencyParser(AutoSentenceParser):
    """
    Implementation of DepIE algorithm for ChemDataExtractor models
    """

    _excluded_fields_for_quantity_model = ["raw_value", "raw_units", "compound"]

    def __init__(
        self,
        chem_name=None,
        skip_phrase=None,
        primary_keypath=None,
        skip_section_phrase=None,
        allow_section_phrase=None,
        value_phrase_constructor=None,
    ):
        """

        :param chem_name: Parse expression to use to detect chemical names, defaults to None,
            in which case the default chemical names expression from ChemDataExtractor is used
        :param skip_phrase: Parse expression used to skip sentences, defaults to None. If this exists
            and matches a sentence, the sentence is skipped for the purposes of information extraction.
        :param primary_keypath: Keypath for field based on which DepIE functions, defaults to None,
            in which case this class tries to infer the primary keypath intelligently.
            See paper for more details on the algorithm, and parse_sentence for more details on how
            the primary keypath is determined from the model.
        :param skip_section_phrase: Parse expression used to skip sections, defaults to None. If this exists
            and matches a heading, the section following the heading is skipped
            for the purposes of information extraction.
        :param allow_section_phrase: Parse expression to ensure a section is processed, defaults to None.
            Even if a heading matches `skip_section_phrase`, if it also matches
            `allow_section_phrase`, the section will be parsed.
        :param value_phrase_constructor: Constructor used for value phrase, defaults to None,
            in which case the default ChemDataExtractor phrase is used.
        """
        super().__init__()
        self.chem_name = (
            chem_name
            if chem_name is not None
            else (cem | chemical_label | lenient_chemical_label)
        )
        self.skip_phrase = skip_phrase
        self.primary_keypath = primary_keypath
        self.skip_section_phrase = skip_section_phrase
        self.allow_section_phrase = allow_section_phrase
        self.value_phrase_constructor = value_phrase_constructor

    def parse_sentence(self, sentence):
        # Skip parsing sentence if it fits skip_phrase
        if self.skip_phrase is not None:
            skip_phrase_results = [
                result for result in self.skip_phrase.scan(sentence.tokens)
            ]
            if skip_phrase_results:
                return []
        # Skip parsing sentence unless it fits trigger_phrase
        if self.trigger_phrase is not None:
            trigger_phrase_results = [
                result for result in self.trigger_phrase.scan(sentence.tokens)
            ]
            if not trigger_phrase_results:
                return []
        # Check for a few scenarios and do a different parsing path depending on what sort of model we have
        # - If primary_keypath is specified, use that as the primary keypath and associate everything to that.
        #   This path *does not* require a chem_name while the other two do.
        # - Otherwise, if it is a full quantity model, i.e. one that contains compounds, then do parsing specifically tailored to that
        # - Finally, if neither of these apply, parse using a specifier. Probably safe to deprecate as it can be rolled into the
        #   first code path?
        if self.primary_keypath is not None:
            return self._parse_sentence_primary_keypath(sentence)
        elif all(
            hasattr(self.model, field)
            for field in self._excluded_fields_for_quantity_model
        ):
            return self._parse_sentence_quantity_model(sentence)
        elif hasattr(self.model, "specifier"):
            return self._parse_sentence_specifier(sentence)
        else:
            raise TypeError(
                f"{self.model} is not supported by AutoDependencyParser as it lacks a quantity or specifier, and a primary keypath was not specified."
            )

    def _parse_sentence_primary_keypath(self, sentence):
        other_results = self._do_other_phrases(sentence)
        value_results = {}
        if "raw_value" in self.model.fields:
            value_results = self.do_value_phrase(sentence)
        try:
            return self._create_models_primary_keypath(
                value_results, other_results, sentence
            )
        except AttributeError as e:
            print(e)
            return []

    def _create_models_primary_keypath(self, value_results, other_results, sentence):
        try:
            primary_results = other_results.pop(self.primary_keypath)
            other_values_map = {}
            for keypath, results in other_results.items():
                other_values_map[keypath] = _find_associated(
                    primary_results, results, False, sentence
                )
            values_map = _find_associated(
                primary_results, value_results, True, sentence
            )

            for primary in primary_results:
                record = self.model()

                if isinstance(primary.data, list):
                    record[self.primary_keypath] = primary.data[0].text
                else:
                    record[self.primary_keypath] = primary.data.text

                record.set_confidence(self.primary_keypath, 1.0)

                for keypath, results_map in other_values_map.items():
                    if (
                        primary in results_map.keys()
                        and results_map[primary] is not None
                    ):
                        data = results_map[primary][0].data
                        if isinstance(data, list):
                            record[keypath] = data[0].text
                        else:
                            record[keypath] = data.text
                        record.set_confidence(keypath, results_map[primary][1])

                if primary in values_map.keys() and values_map[primary] is not None:
                    value = values_map[primary][0]
                    for element in value.data:
                        if element.tag == "raw_value":
                            record.raw_value = element.text
                        elif element.tag == "raw_units":
                            record.raw_units = element.text

                    record.set_confidence("raw_value", values_map[primary][1])
                    record.set_confidence("raw_units", values_map[primary][1])
                yield record
        except AttributeError as e:
            print(e)
            return []

    def _parse_sentence_specifier(self, sentence):
        chem_results = self._do_chem_phrase(sentence)

        other_results = self._do_other_phrases(sentence)

        specifier_results = other_results.pop("specifier")

        parent_results = copy.copy(specifier_results)

        for _, other_result in other_results.items():
            parent_results.extend(other_result)

        _remove_contained_ranges(chem_results, parent_results)

        try:
            return self._create_models_specifier(
                chem_results, specifier_results, other_results, sentence
            )
        except AttributeError as e:
            print(e)
            return []

    def _create_models_specifier(
        self, chem_results, specifier_results, other_results, sentence
    ):
        try:
            chem_values_map = _find_associated(
                specifier_results, chem_results, False, sentence
            )

            other_values_map = {}
            for keypath, results in other_results.items():
                other_values_map[keypath] = _find_associated(
                    specifier_results, results, False, sentence
                )

            for specifier in specifier_results:
                record = self.model()

                if isinstance(specifier.data, list):
                    record.specifier = specifier.data[0].text
                else:
                    record.specifier = specifier.data.text

                record.set_confidence("specifier", 1.0)

                if (
                    specifier in chem_values_map.keys()
                    and chem_values_map[specifier] is not None
                ):
                    test_result = E(
                        "wrapped_result", chem_values_map[specifier][0].data
                    )
                    parsed_result = self._get_data(
                        "compound", self.model.fields["compound"], test_result
                    )["compound"]

                    record["compound"] = parsed_result

                    record.set_confidence("compound", chem_values_map[specifier][1])

                for keypath, results_map in other_values_map.items():
                    if (
                        specifier in results_map.keys()
                        and results_map[specifier] is not None
                    ):
                        data = results_map[specifier][0].data
                        if isinstance(data, list):
                            record[keypath] = data[0].text
                        else:
                            record[keypath] = data.text
                        record.set_confidence(keypath, results_map[specifier][1])
                yield record
        except AttributeError as e:
            print(e)
            return []
        except Exception as e:
            print("Big exception!:", e)
            return []

    def _parse_sentence_quantity_model(self, sentence):
        value_results = self.do_value_phrase(sentence)
        if not value_results:
            return []
        chem_results = self._do_chem_phrase(sentence)
        other_results = self._do_other_phrases(sentence)

        parent_results = copy.copy(value_results)
        for _, other_result in other_results.items():
            parent_results.extend(other_result)

        _remove_contained_ranges(chem_results, parent_results)

        try:
            return self._create_models(
                chem_results, value_results, other_results, sentence
            )
        except AttributeError as e:
            print(e)
            return []

    def _create_models(self, chem_results, value_results, other_results, sentence):
        # TODO(ti250): refactor so all of these create_models are the same - or at least share a lot more...
        try:
            chem_values_map = _find_associated(
                value_results, chem_results, False, sentence
            )

            other_values_map = {}
            for keypath, results in other_results.items():
                other_values_map[keypath] = _find_associated(
                    value_results, results, False, sentence
                )

            for value in value_results:
                record = self.model()
                for element in value.data:
                    if element.tag == "raw_value":
                        record.raw_value = element.text
                    elif element.tag == "raw_units":
                        record.raw_units = element.text

                record.set_confidence("raw_value", 1.0)
                record.set_confidence("raw_units", 1.0)

                if (
                    value in chem_values_map.keys()
                    and chem_values_map[value] is not None
                ):
                    test_result = E("wrapped_result", chem_values_map[value][0].data)
                    parsed_result = self._get_data(
                        "compound", self.model.fields["compound"], test_result
                    )["compound"]

                    record["compound"] = parsed_result

                    record.set_confidence("compound", chem_values_map[value][1])

                for keypath, results_map in other_values_map.items():
                    if value in results_map.keys() and results_map[value] is not None:
                        data = results_map[value][0].data
                        if isinstance(data, list):
                            record[keypath] = data[0].text
                        else:
                            record[keypath] = data.text
                        record.set_confidence(keypath, results_map[value][1])
                yield record
        except AttributeError:
            return []

    def _do_other_phrases(self, sentence):
        results = {}
        for keypath, phrase in self._phrases_for_keypaths.items():
            results[keypath] = _LabelledRange.from_cde_results(
                phrase.scan(sentence.tokens), subsentence=sentence
            )
        return results

    def do_value_phrase(self, sentence):
        value_phrase = self._value_phrase
        value_phrase_results = _LabelledRange.from_cde_results(
            value_phrase.scan(sentence.tokens), subsentence=sentence
        )
        return value_phrase_results

    def _do_chem_phrase(self, sentence):
        chem_phrase = self._chem_phrase

        unfiltered_chem_phrase_results = _LabelledRange.from_cde_results(
            chem_phrase.scan(sentence.tokens), subsentence=sentence
        )
        chem_phrase_results = []
        for result in unfiltered_chem_phrase_results:
            if isinstance(result.data, list) and result.data[0].tag == "compound":
                chem_phrase_results.append(result)
            elif not isinstance(result.data, list) and result.data.tag == "compound":
                chem_phrase_results.append(result)
        return chem_phrase_results

    @property
    def _value_phrase(self):
        value_phrase_constructor = self.value_phrase_constructor
        if self.value_phrase_constructor is None:
            value_phrase_constructor = value_element
        if hasattr(self.model, "dimensions") and not self.model.dimensions:
            return value_phrase_constructor()
        unit_element = Group(
            construct_unit_element(self.model.dimensions).with_condition(
                match_dimensions_of(self.model)
            )("raw_units")
        )
        return value_phrase_constructor(unit_element)

    @property
    def _chem_phrase(self):
        return self.chem_name

    @property
    def _phrases_for_keypaths(self):
        phrases_keypaths = {}
        for field_name, field in self.model.fields.items():
            phrases_keypaths.update(
                self._get_phrases_for_field(field_name, field, do_model=False)
            )
        return phrases_keypaths

    def _get_phrases_for_field(self, field_name, field, do_model=True):
        phrases_for_field = {}
        if field_name not in self._excluded_fields_for_quantity_model:
            if isinstance(field, ModelType) and do_model:
                for model_field_name, model_field in field.model_class.fields.items():
                    if model_field not in self._excluded_fields_for_quantity_model:
                        new_keypath = f"{field_name}.{model_field_name}"
                        phrases_for_field.update(
                            self._get_phrases_for_field(new_keypath, model_field)
                        )
            else:
                if field.parse_expression is not None:
                    phrases_for_field[field_name] = field.parse_expression
        return phrases_for_field


def _route_to_root(source_range, tokens):
    token = tokens[source_range.start]
    route = []
    while token is not None:
        if token.index in source_range:
            route = []
        route.append(token.index)
        token = token.dependency.head
    return route


def _find_distance(route_1, route_2, blocked_elements=None):
    intersect_element = _find_intersect_element(route_1, route_2, blocked_elements)
    if intersect_element is None:
        return None

    # Get the distance from the root node, and do 1 / that, i.e. penalize
    # being in a different tree branch as much as possible
    # Add in a small term for the actual distance in between to be a "tie-breaker"
    # if we get two that meet at the same location
    return (1.0 / (len(route_1) - route_1.index(intersect_element))) + 0.01 * (
        route_1.index(intersect_element) + route_2.index(intersect_element)
    )


def _find_intersect_element(route_1, route_2, blocked_elements=None):
    # assumes both have same final element
    intersect_element = None
    if len(route_1) > len(route_2):
        route_1, route_2 = route_2, route_1
    route_2 = route_2[len(route_2) - len(route_1) :]
    for el1, el2 in zip(reversed(route_1), reversed(route_2)):
        if el1 == el2:
            intersect_element = el1
    if blocked_elements is not None:
        if intersect_element is None:
            return intersect_element
        for el in route_1[: route_1.index(intersect_element)]:
            if el in blocked_elements:
                return None
        for el in route_2[: route_2.index(intersect_element)]:
            if el in blocked_elements:
                return None
    return intersect_element


# Try to find closest child from the parent based on proximity in dependency space
def _find_associated(parents, children, remove_children, sentence):
    tokens = sentence.tokens
    num_subsentences = 1

    if hasattr(sentence, "parent_sentence"):
        parent_sentence = sentence.parent_sentence
        tokens = parent_sentence.tokens
        num_subsentences = len(parent_sentence.subsentences)

    if len(parents) == 0:
        return {}

    elif len(children) == 0:
        return {parent: None for parent in parents}

    elif len(parents) == 1 and len(children) == 1:
        # Make assumption that each subsentence has more or less the same number of children
        return {parents[0]: (children[0], (1.0 / num_subsentences))}

    # Make assumption that each subsentence has more or less the same number of children here as well.
    # Assume that we can't do worse than guessing randomly
    min_confidence = 1 / (len(children) * num_subsentences)

    if remove_children:
        children = copy.copy(children)
        min_confidence = 1 / (len(children) * len(parents) * num_subsentences)

    distances = {}

    routes = {}
    for labelled_range in parents + children:
        range_ = range(labelled_range.range[0], labelled_range.range[1])
        routes[labelled_range] = _route_to_root(range_, tokens)

    for parent_index, labelled_parent_range in enumerate(parents):
        distances[labelled_parent_range] = {}
        parent_route = routes[labelled_parent_range]

        parent_blocked_paths = set()
        for i, el in enumerate(parents):
            if i != parent_index:
                for j in range(el.range[0], el.range[1]):
                    parent_blocked_paths.add(j)

        for child_index, labelled_child_range in enumerate(children):

            child_blocked_paths = set()
            for i, el in enumerate(children):
                if i != child_index:
                    for j in range(el.range[0], el.range[1]):
                        child_blocked_paths.add(j)

            blocked_paths = parent_blocked_paths.union(child_blocked_paths)

            child_route = routes[labelled_child_range]

            strict_distance = _find_distance(
                child_route, parent_route, blocked_elements=blocked_paths
            )
            if strict_distance is not None:
                distances[labelled_parent_range][labelled_child_range] = strict_distance

            else:
                lenient_distance = 2 * _find_distance(child_route, parent_route)
                if lenient_distance is None:
                    lenient_distance = 10000
                distances[labelled_parent_range][
                    labelled_child_range
                ] = lenient_distance

    merged = {}
    removed_children = []

    for labelled_parent_range in parents:
        filtered_distances = [
            item
            for item in list(distances[labelled_parent_range].items())
            if item[0] not in removed_children
        ]
        associated_distances = sorted(
            filtered_distances, key=lambda x: x[1] if (x[1] is not None) else 10000
        )

        if len(associated_distances):
            associated_child = associated_distances[0][0]
            min_distance = associated_distances[0][1]

            if len(associated_distances) == 1:
                confidence = 1.0
            else:
                second_min_distance = associated_distances[1][1]
                confidence = (1 + (min_distance / second_min_distance)) ** -1
            confidence = confidence if confidence > min_confidence else min_confidence
            merged[labelled_parent_range] = (associated_child, confidence)

            if remove_children:
                removed_children.append(associated_child)
        else:
            merged[labelled_parent_range] = None

    return merged


# Remove any child ranges that are contained within the parent range
def _remove_contained_ranges(from_ranges, parent_ranges):
    to_remove = set()
    for labelled_parent_range in parent_ranges:
        parent_range = labelled_parent_range.range
        for labelled_child_range in from_ranges:
            child_range = labelled_child_range.range
            if child_range[0] > parent_range[0] and child_range[1] < parent_range[1]:
                to_remove.add(labelled_child_range)
    for removal_candidate in to_remove:
        from_ranges.remove(removal_candidate)
    return from_ranges
