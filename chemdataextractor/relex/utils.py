
# -*- coding: utf-8 -*-
"""
chemdataextractor.relex.utils.py
Various utility functions
"""
import numpy as np

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

    prefix_i = pi.elements['prefix']['vector']

    middles_i = []
    for m in range(0, number_of_middles_i):
        middles_i.append(pi.elements['middle_' + str(m+1)]['vector'])
    suffix_i = pi.elements['suffix']['vector']

    prefix_j = pj.elements['prefix']['vector']
    middles_j = []
    for m in range(0, number_of_middles_j):
        middles_j.append(pi.elements['middle_' + str(m+1)]['vector'])

    suffix_j = pj.elements['suffix']['vector']

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


def mode_rows(a):
    """
    Find the modal row of a 2d array
    :param a: The 2d array to process
    :type a: np.array()
    :return: The most frequent row
    """
    a = np.ascontiguousarray(a)
    void_dt = np.dtype((np.void, a.dtype.itemsize * np.prod(a.shape[1:])))
    _, ids, count = np.unique(a.view(void_dt).ravel(),
                              return_index=True,
                              return_counts=True)
    largest_count_id = ids[count.argmax()]
    most_frequent_row = a[largest_count_id]
    return most_frequent_row

def KnuthMorrisPratt(text, pattern):
    """Yields all starting positions of copies of the pattern in the text.
        Calling conventions are similar to string.find, but its arguments can be
        lists or iterators, not just strings, it returns all matches, not just
        the first one, and it does not need the whole text in memory at once.
        Whenever it yields, it will have read the text exactly up to and including
        the match that caused the yield.

    Source: http://code.activestate.com/recipes/117214/"""

    # allow indexing into pattern and protect against change during yield
    pattern = list(pattern)

    # build table of shift amounts
    shifts = [1] * (len(pattern) + 1)
    shift = 1
    for pos in range(len(pattern)):
        while shift <= pos and pattern[pos] != pattern[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # do the actual search
    startPos = 0
    matchLen = 0
    for c in text:
        while matchLen == len(pattern) or \
              matchLen >= 0 and pattern[matchLen] != c:
            startPos += shifts[matchLen]
            matchLen -= shifts[matchLen]
        matchLen += 1
        if matchLen == len(pattern):
            yield startPos