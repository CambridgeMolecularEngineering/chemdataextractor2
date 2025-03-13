from collections import namedtuple
import copy

CoordinatedGroup = namedtuple("CoordinatedGroup", ["root", "content"])


def _add(subsentences, coordinated_group, prev_location, min_index):
    if len(subsentences) != len(coordinated_group.content):
        raise AttributeError(
            "To perform add, there should be an equal number of coordinated clauses and subsentences."
        )
    added_subsentences = []
    for coordinated_content, subsentence in zip(
        coordinated_group.content, subsentences
    ):
        sub = copy.copy(subsentence)
        sub.extend([i for i in range(prev_location + 1, min_index)])

        coordinated_indices = sorted([el[0] for el in coordinated_content])
        sub.extend(coordinated_indices)

        added_subsentences.append(sub)
    return added_subsentences


def _multiply(subsentences, coordinated_group, prev_location, min_index):
    mul_subsentences = []
    for subsentence in subsentences:
        for coordinated_content in coordinated_group.content:
            sub = copy.copy(subsentence)
            sub.extend([i for i in range(prev_location + 1, min_index)])

            coordinated_indices = sorted([el[0] for el in coordinated_content])
            sub.extend(coordinated_indices)

            mul_subsentences.append(sub)
    return mul_subsentences


class SubsentenceExtractor(object):
    """
    Extract subsentences (i.e. clauses) from bulk text, as described in the paper
    "Automated Construction of a Photocatalysis Dataset for Water-Splitting Applications",
    coming soon.
    """

    trigger_words = {"and", "or"}
    disallowed_conjunctions = {"/", ":"}

    def __init__(self, max_subsentences=12):
        self.max_subsentences = max_subsentences

    def subsentences(self, sentence):
        # Ensure that the trigger words are found in the sentence
        if (
            len(
                self.trigger_words.intersection(
                    set(token.text.lower() for token in sentence.tokens)
                )
            )
            == 0
        ):
            return [sentence.tokens]

        dependencies = [token.dependency for token in sentence.tokens]

        # Early stopping if no coordinations found
        if "conj" not in [dependency.relation for dependency in dependencies]:
            return [sentence.tokens]

        # Find roots of coordinated phrases
        conj_roots_indices = set()
        for tok in sentence.tokens:
            dependency = tok.dependency
            index = tok.index
            if dependency.relation == "conj":
                should_add = True
                # Approach 1: Trying to look 'up' in the dependency tree to find the cc type. Doesn't always work
                # though vecause they're not neccesarily in the same tree
                # head_index = dependency.head.index
                # all_dependencies = self._all_dependencies_for_root(dependency.head.index, dependencies)
                # for i, el in all_dependencies:
                #     if sentence.tokens[i].text in self.disallowed_conjunctions:
                #         should_add = False

                # Approach 2: Try to find the closest cc in the sentence
                offset = 1
                start_index = dependency.head.index
                sent_length = len(sentence.tokens)
                while start_index + offset < sent_length or start_index - offset >= 0:
                    if start_index + offset < sent_length:
                        other_token = sentence.tokens[start_index + offset]
                        if other_token.dependency.relation == "cc":
                            if other_token.text in self.disallowed_conjunctions:
                                should_add = False
                            break
                    if start_index - offset >= 0:
                        other_token = sentence.tokens[start_index - offset]
                        if other_token.dependency.relation == "cc":
                            if other_token.text in self.disallowed_conjunctions:
                                should_add = False
                            break
                    offset += 1

                if should_add:
                    conj_roots_indices.add(dependency.head.index)
        conj_root_indices = sorted(list(conj_roots_indices))

        coordinated_groups = []
        for index, root_index in enumerate(conj_root_indices):
            next_root = None
            if root_index < len(conj_roots_indices) - 1:
                next_root = conj_root_indices[index + 1]
            coordinated_groups.append(
                CoordinatedGroup(
                    root_index,
                    self._find_coordinated_group(root_index, dependencies, next_root),
                )
            )

        # Stop early if there is exactly 1 coordinated group and it covers the whole sentence
        # as this is the case of e.g. "The mixture was heated, and then stirred", where
        # we don't really care about splitting the sentence
        if len(coordinated_groups) == 1 and len(coordinated_groups[0].content) == 2:
            coordinated_group = coordinated_groups[0]
            first_clause_min_index = min(
                [word[0] for word in coordinated_group.content[0]]
            )
            first_clause_max_index = max(
                [word[0] for word in coordinated_group.content[0]]
            )
            second_clause_min_index = min(
                [word[0] for word in coordinated_group.content[1]]
            )
            second_clause_max_index = max(
                [word[0] for word in coordinated_group.content[1]]
            )
            clauses_gap = second_clause_min_index - first_clause_max_index

            if (
                first_clause_min_index == 0
                and second_clause_max_index >= len(sentence.tokens) - 2
                and abs(clauses_gap) <= 2
            ):
                # We also allow a leniency of one token from the end as punctuation is often omitted
                # We do the above abs check because the end of the first clause and the start of the
                # second clause could be separated by an "and" that has been omitted
                return [sentence.tokens]

        extents = []

        for coordinated_group in coordinated_groups:
            max_index = -1
            min_index = 10000

            for coordinated_phrase in coordinated_group.content:
                for word in coordinated_phrase:
                    if word[0] > max_index:
                        max_index = word[0]
                    if word[0] < min_index:
                        min_index = word[0]

            extents.append((min_index, max_index))

        # print(extents)
        # Early stopping if any overlapping ranges of coordinated phrases
        for extent_1 in extents:
            for extent_2 in extents:
                if extent_1[0] == extent_2[0] and extent_1[1] == extent_2[1]:
                    pass
                elif extent_1[0] <= extent_2[1] and extent_2[0] <= extent_1[1]:
                    # print("ABORTING SUBSENTENCE, OVERLAPPING INDICES")
                    return [sentence.tokens]

        try:
            operations = self._find_operations(coordinated_groups)
        except RuntimeError:
            # print("ABORTING SUBSENTENCE, TOO MANY SENTENCES")
            return [sentence.tokens]

        subsentence_indices = [[]]
        prev_location = -1
        for extent, operation, coordinated_group in zip(
            extents, operations, coordinated_groups
        ):
            min_index = extent[0]
            max_index = extent[1]

            subsentence_indices = operation(
                subsentence_indices, coordinated_group, prev_location, min_index
            )
            prev_location = max_index

        for subsentence in subsentence_indices:
            subsentence.extend(
                [i for i in range(prev_location + 1, len(sentence.tokens))]
            )

        subsentence_tokens = []
        for subsentence in subsentence_indices:
            subsentence_tokens.append([sentence.tokens[index] for index in subsentence])

        # for subsentence in subsentence_tokens:
        #     print(' '.join([token.text for token in subsentence]))

        return subsentence_tokens

    def _find_coordinated_group(self, root_index, dependencies, next_root=None):
        phrase_roots = [root_index]
        for index, dependency in enumerate(dependencies):
            if dependency.relation == "conj" and dependency.head.index == root_index:
                phrase_roots.append(index)

        max_indices = phrase_roots[1:]
        max_indices.append(next_root)

        # excluded_relations = ["conj", "cc", "punct"]
        # mark shouldn't be necesary once we exclude syntactic similarities.
        excluded_relations = ["conj", "cc"]
        min_index_excluded = ["case", "mark", "punct"]
        to_trim = ["punct"]
        to_trim_head = []

        min_index_candidates = self._all_dependencies_for_root(
            root_index, dependencies, excluded_relations
        )
        min_index = root_index
        for el in min_index_candidates:
            if (
                el[1].head is not None
                and el[0] < min_index
                and el[1].relation not in min_index_excluded
            ):
                min_index = el[0]

        coordinated_graphs = [
            self._all_dependencies_for_root(
                phrase_root, dependencies, excluded_relations, min_index, max_index
            )
            for max_index, phrase_root in zip(max_indices, phrase_roots)
        ]

        if len(coordinated_graphs) >= 3:
            # Check for syntactic similarities
            pass

        for unneeded_el in to_trim:
            coordinated_graphs = self._remove_unneeded(coordinated_graphs, unneeded_el)

        for unneeded_el in to_trim_head:
            coordinated_graphs = self._remove_unneeded_head(
                coordinated_graphs, unneeded_el
            )

        return coordinated_graphs

    def _all_dependencies_for_root(
        self,
        root_index,
        dependencies,
        excluded_relations=None,
        min_index=None,
        max_index=None,
    ):
        if excluded_relations is None:
            excluded_relations = []
        coordinated_graph = [(root_index, dependencies[root_index])]
        for index, dependency in enumerate(dependencies):
            if max_index is not None and index > max_index:
                break
            if (
                dependency.head is not None
                and dependency.head.index == root_index
                and dependency.relation not in excluded_relations
                and (min_index is None or index >= min_index)
            ):
                coordinated_graph.extend(
                    self._all_dependencies_for_root(
                        index, dependencies, excluded_relations
                    )
                )
        return coordinated_graph

    def _remove_unneeded(self, coordinated_graphs, unneeded="punct"):
        unneeded_count = 0
        for coordinated_graph in coordinated_graphs:
            for dependency in coordinated_graph:
                if dependency[1].relation == unneeded:
                    unneeded_count += 1

        if unneeded_count >= len(coordinated_graphs) or unneeded_count == 0:
            return coordinated_graphs

        new_coordinated_graphs = []

        unneeded_coords = set()
        for coordinated_graph in coordinated_graphs:
            for dependency in coordinated_graph:
                if dependency[1].relation == unneeded:
                    unneeded_coords.add(dependency[0])

        for coordinated_graph in coordinated_graphs:
            min_index = min(coordinated_graph, key=lambda x: x[0])[0]
            max_index = max(coordinated_graph, key=lambda x: x[0])[0]
            new_coordinated_graph = []
            if len(coordinated_graph) == 1:
                new_coordinated_graph = coordinated_graph
            else:
                for el in coordinated_graph:
                    if el[0] not in unneeded_coords or (
                        el[0] != max_index and el[0] != min_index
                    ):
                        new_coordinated_graph.append(el)

            new_coordinated_graphs.append(new_coordinated_graph)

        return new_coordinated_graphs

    def _remove_unneeded_head(self, coordinated_graphs, unneeded="nummod"):
        unneeded_count = 0
        for coordinated_graph in coordinated_graphs:
            for dependency in coordinated_graph:
                if dependency[1].relation == unneeded:
                    unneeded_count += 1

        if unneeded_count >= len(coordinated_graphs) or unneeded_count == 0:
            return coordinated_graphs

        new_coordinated_graphs = []

        unneeded_coords = set()
        for coordinated_graph in coordinated_graphs:
            for dependency in coordinated_graph:
                if dependency[1].relation == unneeded:
                    unneeded_coords.add(dependency[1].head.index)
                elif (
                    dependency[1].head is not None
                    and dependency[1].head.index in unneeded_coords
                ):
                    unneeded_coords.add(dependency[0])

        for coordinated_graph in coordinated_graphs:
            min_index = min(coordinated_graph, key=lambda x: x[0])[0]
            max_index = max(coordinated_graph, key=lambda x: x[0])[0]
            new_coordinated_graph = []
            if len(coordinated_graph) == 1:
                new_coordinated_graph = coordinated_graph
            else:
                for el in coordinated_graph:
                    if el[0] not in unneeded_coords or (
                        el[0] != max_index and el[0] != min_index
                    ):
                        new_coordinated_graph.append(el)

            new_coordinated_graphs.append(new_coordinated_graph)

        return new_coordinated_graphs

    def _find_operations(self, conjugated_groups):
        operations = []
        previous_operation = None
        total_subsentences = 1
        for index, group in enumerate(conjugated_groups):
            operation = _add
            if total_subsentences != len(group.content):
                if previous_operation is _add and total_subsentences * len(
                    conjugated_groups[index - 1].content
                ) == len(group.content):
                    operations[-1] = _multiply
                    total_subsentences *= len(conjugated_groups[index - 1].content)
                else:
                    operation = _multiply
                    total_subsentences *= len(group.content)
            operations.append(operation)
            previous_operation = operation
        if total_subsentences > self.max_subsentences:
            raise RuntimeError(
                "Too many subsentences. Maximum of {} subsentences, found {}.".format(
                    total_subsentences, self.max_subsentences
                )
            )
        return operations


class NoneSubsentenceExtractor(object):

    def subsentences(self, sentence):
        return [sentence.tokens]
