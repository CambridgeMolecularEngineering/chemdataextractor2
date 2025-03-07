import torch
from chemdataextractor.errors import ConfigurationError
from typing import List, Optional
import math
import logging

logger = logging.getLogger(__name__)


def get_device_of(tensor: torch.Tensor) -> int:
    """
    Returns the device of the tensor.
    """
    if not tensor.is_cuda:
        return -1
    else:
        return tensor.get_device()

def get_range_vector(size: int, device: int) -> torch.Tensor:
    """
    Returns a range vector with the desired size, starting at 0. The CUDA implementation
    is meant to avoid copy data from CPU to GPU.
    """
    if device > -1:
        return torch.LongTensor(size).fill_(1).cumsum(0).to(device) - 1
    else:
        return torch.arange(0, size, dtype=torch.long)

def combine_initial_dims(tensor: torch.Tensor) -> torch.Tensor:
    """
    Given a (possibly higher order) tensor of ids with shape
    (d1, ..., dn, sequence_length)
    Return a view that's (d1 * ... * dn, sequence_length).
    If original tensor is 1-d or 2-d, return it as is.
    """
    if tensor.dim() <= 2:
        return tensor
    else:
        return tensor.view(-1, tensor.size(-1))


def uncombine_initial_dims(tensor: torch.Tensor, original_size: torch.Size) -> torch.Tensor:
    """
    Given a tensor of embeddings with shape
    (d1 * ... * dn, sequence_length, embedding_dim)
    and the original shape
    (d1, ..., dn, sequence_length),
    return the reshaped tensor of embeddings with shape
    (d1, ..., dn, sequence_length, embedding_dim).
    If original size is 1-d or 2-d, return it as is.
    """
    if len(original_size) <= 2:
        return tensor
    else:
        view_args = list(original_size) + [tensor.size(-1)]
        return tensor.view(*view_args)

def viterbi_decode(
    tag_sequence: torch.Tensor,
    transition_matrix: torch.Tensor,
    tag_observations: Optional[List[int]] = None,
    allowed_start_transitions: torch.Tensor = None,
    allowed_end_transitions: torch.Tensor = None,
    top_k: int = None,
):
    """
    Perform Viterbi decoding in log space over a sequence given a transition matrix
    specifying pairwise (transition) potentials between tags and a matrix of shape
    (sequence_length, num_tags) specifying unary potentials for possible tags per
    timestep.

    # Parameters

    tag_sequence : `torch.Tensor`, required.
        A tensor of shape (sequence_length, num_tags) representing scores for
        a set of tags over a given sequence.
    transition_matrix : `torch.Tensor`, required.
        A tensor of shape (num_tags, num_tags) representing the binary potentials
        for transitioning between a given pair of tags.
    tag_observations : `Optional[List[int]]`, optional, (default = `None`)
        A list of length `sequence_length` containing the class ids of observed
        elements in the sequence, with unobserved elements being set to -1. Note that
        it is possible to provide evidence which results in degenerate labelings if
        the sequences of tags you provide as evidence cannot transition between each
        other, or those transitions are extremely unlikely. In this situation we log a
        warning, but the responsibility for providing self-consistent evidence ultimately
        lies with the user.
    allowed_start_transitions : `torch.Tensor`, optional, (default = `None`)
        An optional tensor of shape (num_tags,) describing which tags the START token
        may transition *to*. If provided, additional transition constraints will be used for
        determining the start element of the sequence.
    allowed_end_transitions : `torch.Tensor`, optional, (default = `None`)
        An optional tensor of shape (num_tags,) describing which tags may transition *to* the
        end tag. If provided, additional transition constraints will be used for determining
        the end element of the sequence.
    top_k : `int`, optional, (default = `None`)
        Optional integer specifying how many of the top paths to return. For top_k>=1, returns
        a tuple of two lists: top_k_paths, top_k_scores, For top_k==None, returns a flattened
        tuple with just the top path and its score (not in lists, for backwards compatibility).

    # Returns

    viterbi_path : `List[int]`
        The tag indices of the maximum likelihood tag sequence.
    viterbi_score : `torch.Tensor`
        The score of the viterbi path.
    """
    if top_k is None:
        top_k = 1
        flatten_output = True
    elif top_k >= 1:
        flatten_output = False
    else:
        raise ValueError(f"top_k must be either None or an integer >=1. Instead received {top_k}")

    sequence_length, num_tags = list(tag_sequence.size())

    has_start_end_restrictions = (
        allowed_end_transitions is not None or allowed_start_transitions is not None
    )

    if has_start_end_restrictions:

        if allowed_end_transitions is None:
            allowed_end_transitions = torch.zeros(num_tags)
        if allowed_start_transitions is None:
            allowed_start_transitions = torch.zeros(num_tags)

        num_tags = num_tags + 2
        new_transition_matrix = torch.zeros(num_tags, num_tags)
        new_transition_matrix[:-2, :-2] = transition_matrix

        # Start and end transitions are fully defined, but cannot transition between each other.

        allowed_start_transitions = torch.cat(
            [allowed_start_transitions, torch.tensor([-math.inf, -math.inf])]
        )
        allowed_end_transitions = torch.cat(
            [allowed_end_transitions, torch.tensor([-math.inf, -math.inf])]
        )

        # First define how we may transition FROM the start and end tags.
        new_transition_matrix[-2, :] = allowed_start_transitions
        # We cannot transition from the end tag to any tag.
        new_transition_matrix[-1, :] = -math.inf

        new_transition_matrix[:, -1] = allowed_end_transitions
        # We cannot transition to the start tag from any tag.
        new_transition_matrix[:, -2] = -math.inf

        transition_matrix = new_transition_matrix

    if tag_observations:
        if len(tag_observations) != sequence_length:
            raise ConfigurationError(
                "Observations were provided, but they were not the same length "
                "as the sequence. Found sequence of length: {} and evidence: {}".format(
                    sequence_length, tag_observations
                )
            )
    else:
        tag_observations = [-1 for _ in range(sequence_length)]

    if has_start_end_restrictions:
        tag_observations = [num_tags - 2] + tag_observations + [num_tags - 1]
        zero_sentinel = torch.zeros(1, num_tags)
        extra_tags_sentinel = torch.ones(sequence_length, 2) * -math.inf
        tag_sequence = torch.cat([tag_sequence, extra_tags_sentinel], -1)
        tag_sequence = torch.cat([zero_sentinel, tag_sequence, zero_sentinel], 0)
        sequence_length = tag_sequence.size(0)

    path_scores = []
    path_indices = []

    if tag_observations[0] != -1:
        one_hot = torch.zeros(num_tags)
        one_hot[tag_observations[0]] = 100000.0
        path_scores.append(one_hot.unsqueeze(0))
    else:
        path_scores.append(tag_sequence[0, :].unsqueeze(0))

    # Evaluate the scores for all possible paths.
    for timestep in range(1, sequence_length):
        # Add pairwise potentials to current scores.
        summed_potentials = path_scores[timestep - 1].unsqueeze(2) + transition_matrix
        summed_potentials = summed_potentials.view(-1, num_tags)

        # Best pairwise potential path score from the previous timestep.
        max_k = min(summed_potentials.size()[0], top_k)
        scores, paths = torch.topk(summed_potentials, k=max_k, dim=0)

        # If we have an observation for this timestep, use it
        # instead of the distribution over tags.
        observation = tag_observations[timestep]
        # Warn the user if they have passed
        # invalid/extremely unlikely evidence.
        if tag_observations[timestep - 1] != -1 and observation != -1:
            if transition_matrix[tag_observations[timestep - 1], observation] < -10000:
                logger.warning(
                    "The pairwise potential between tags you have passed as "
                    "observations is extremely unlikely. Double check your evidence "
                    "or transition potentials!"
                )
        if observation != -1:
            one_hot = torch.zeros(num_tags)
            one_hot[observation] = 100000.0
            path_scores.append(one_hot.unsqueeze(0))
        else:
            path_scores.append(tag_sequence[timestep, :] + scores)
        path_indices.append(paths.squeeze())

    # Construct the most likely sequence backwards.
    path_scores_v = path_scores[-1].view(-1)
    max_k = min(path_scores_v.size()[0], top_k)
    viterbi_scores, best_paths = torch.topk(path_scores_v, k=max_k, dim=0)
    viterbi_paths = []
    for i in range(max_k):
        viterbi_path = [best_paths[i]]
        for backward_timestep in reversed(path_indices):
            viterbi_path.append(int(backward_timestep.view(-1)[viterbi_path[-1]]))
        # Reverse the backward path.
        viterbi_path.reverse()

        if has_start_end_restrictions:
            viterbi_path = viterbi_path[1:-1]

        # Viterbi paths uses (num_tags * n_permutations) nodes; therefore, we need to modulo.
        viterbi_path = [j % num_tags for j in viterbi_path]
        viterbi_paths.append(viterbi_path)

    if flatten_output:
        return viterbi_paths[0], viterbi_scores[0]

    return viterbi_paths, viterbi_scores
