# -*- coding: utf-8 -*-
"""
Parser elements.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import collections
import copy
import logging
import re
from copy import deepcopy

from lxml.builder import E
import six
import types

log = logging.getLogger(__name__)


class ParseException(Exception):
    """Exception thrown by a ParserElement when it doesn't match input."""

    def __init__(self, tokens, i=0, msg=None, element=None):
        self.i = i
        self.msg = msg
        self.tokens = tokens
        self.element = element

    @classmethod
    def wrap(cls, parse_exception):
        return cls(parse_exception.tokens, parse_exception.loc, parse_exception.msg, parse_exception.element)

    def __str__(self):
        return ('%s (at token %d)' % (self.msg, self.i))


XML_SAFE_TAGS = {
    '-LRB-': 'LRB',
    '-RRB-': 'RRB',
    '.': 'STOP',
    ',': 'COMMA',
    ':': 'COLON',
    '$': 'DOLLAR',
    '``': 'LQUOTE',
    '\'\'': 'RQUOTE',
    'PRP$': 'PRPPOS',
    'WP$': 'WPPOS',
    None: 'NONE'
}


def safe_name(name):
    """Make name safe for use in XML output."""
    return XML_SAFE_TAGS.get(name, name)


class BaseParserElement(object):
    """Abstract base parser element class."""

    def __init__(self):
        self.name = None
        #: str or None: name for BaseParserElement. This is used to set the name of the Element when a result is found
        self.actions = []
        #: list(chemdataextractor.parse.actions): list of actions that will be applied to the results after parsing. Actions are functions with arguments of (tokens, start, result)
        self.streamlined = False
        self.condition = None

    def set_action(self, *fns):
        self.actions = fns
        return self

    def add_action(self, *fns):
        self.actions += fns
        return self

    def with_condition(self, condition):
        """
        Add a condition to the parser element. The condition must be a function that takes
        a match and return True or False, i.e. a function which takes tuple(list(Element), int)
        and returns bool. If the function evaluates True, the match is kept, while if the function
        evaluates False, the match is discarded. The condition is executed after any other actions.
        """
        self.condition = condition
        return self

    def copy(self):
        new = copy.copy(self)
        new.actions = self.actions[:]
        return new

    def set_name(self, name):
        new = self.copy()
        new.name = name
        return new

    def scan(self, tokens, max_matches=six.MAXSIZE, overlap=False):
        """
        Scans for matches in given tokens.

        :param list(tuple(string, string)) tokens: A tokenized representation of the text to scan. The first string in the tuple is the content, typically a word, and the second string is the part of speech tag.
        :param int max_matches: The maximum number of matches to look for. Default is the maximum size possible for a list.
        :param bool overlap: Whether the found results are allowed to overlap. Default False.
        :returns: A generator of the results found. Each result is a tuple with the first element being a list of elements found, and the second and third elements are the start and end indices representing the span of the result.
        :rtype: generator(tuple(list(lxml.etree.Element), int, int))
        """
        if not self.streamlined:
            self.streamline()
        matches = 0
        i = 0
        length = len(tokens)
        while i < length and matches < max_matches:
            try:
                results, next_i = self.parse(tokens, i)
            except ParseException as err:
                # print(err.msg)
                i += 1
            else:
                if next_i > i:
                    matches += 1
                    if len(results) == 1:
                        results = results[0]
                    yield results, i, next_i
                    if overlap:
                        i += 1
                    else:
                        i = next_i
                else:
                    i += 1

    def parse(self, tokens, i, actions=True):
        """
        Parse given tokens and return results

        :param tokens: A tokenized representation of the text to scan. The first string in the tuple is the content, typically a word, and the second string is the part of speech tag.
        :type tokens: list(tuple(string, string))
        :param int i: The index at which to start scanning from
        :param bool actions: Whether the actions attached to this element will be executed. Default True.
        :returns: A tuple where the first element is a list of elements found (can be None if no results were found), and the last index investigated.
        :rtype: tuple(list(Element) or None, int)
        """
        try:
            result, found_index = self._parse_tokens(tokens, i, actions)
        except IndexError:
            raise ParseException(tokens, i, 'IndexError', self)
        if actions:
            for action in self.actions:
                action_result = action(tokens, i, result)
                if action_result is not None:
                    result = action_result
        if self.condition is not None:
            if not self.condition(result):
                raise ParseException(tokens, found_index, 'Did not satisfy condition', self)
        return result, found_index

    def try_parse(self, tokens, i):
        return self.parse(tokens, i, actions=False)[1]

    def _parse_tokens(self, tokens, i, actions=True):
        """
        Implemented by subclasses, parses given tokens and returns the results

        :param list(tuple(string, string)) tokens: A tokenized representation of the text to scan. The first string in the tuple is the content, typically a word, and the second string is the part of speech tag.
        :param int i: The index at which to start scanning from
        :param bool actions: Whether the actions attached to this element will be executed. Default True.
        :returns: A tuple where the first element is a list of elements found (can be None if no results were found), and the last index investigated.
        :rtype: tuple(list(Element) or None, int)
        """
        # TODO: abstractmethod?
        return None, i

    def streamline(self):
        """
        Streamlines internal representations. e.g., if we have something like And(And(And(And(a), b), c), d), streamline this to And(a, b, c, d)
        """
        self.streamlined = True
        return self

    def __add__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        if not isinstance(other, BaseParserElement):
            # raise?
            return None
        return And([self, other])

    def __radd__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        if not isinstance(other, BaseParserElement):
            # raise?
            return None
        return other + self

    def __or__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        if not isinstance(other, BaseParserElement):
            return None
        return First([self, other])

    def __ror__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        if not isinstance(other, BaseParserElement):
            return None
        return other | self

    def __xor__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        if not isinstance(other, BaseParserElement):
            return None
        return Or([self, other])

    def __rxor__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        if not isinstance(other, BaseParserElement):
            return None
        return other ^ self

    # def __and__(self, other):
    #     if isinstance(other, six.text_type):
    #         other = Word(other)
    #     if not isinstance(other, BaseParserElement):
    #         return None
    #     return Each([self, other])
    #
    # def __rand__(self, other):
    #     if isinstance(other, six.text_type):
    #         other = Word(other)
    #     if not isinstance(other, BaseParserElement):
    #         return None
    #     return other & self

    def __invert__(self):
        return Not(self)

    def __call__(self, name):
        """
        If a BaseParserElement is called, returns the BaseParserElement with its name set to the argument. The name is used to identify the results parsed by this element.

        :param str name: Name to give BaseParserElement
        :returns: A BaseParserElement with the given name
        :rtype: BaseParserElement
        """
        return self.set_name(name)

    def hide(self):
        return Hide(self)


class Any(BaseParserElement):
    """Always match a single token."""

    def _parse_tokens(self, tokens, i, actions=True):
        return [E(self.name or safe_name(tokens[i][1]), tokens[i][0])], i + 1


class NoMatch(BaseParserElement):

    def _parse_tokens(self, tokens, i, actions=True):
        raise ParseException(tokens, i, 'NoMatch will not match any tokens', self)


class Word(BaseParserElement):
    """Match token text exactly. Case-sensitive."""

    def __init__(self, match):
        super(Word, self).__init__()
        self.match = match

    def _parse_tokens(self, tokens, i, actions=True):
        token_text = tokens[i][0]
        if token_text == self.match:
            return [E(self.name or safe_name(tokens[i][1]), token_text)], i + 1
        raise ParseException(tokens, i, 'Expected %s, got %s' % (self.match, token_text), self)


class Tag(BaseParserElement):
    """Match tag exactly."""

    def __init__(self, match, tag_type=None):
        super(Tag, self).__init__()
        self.match = match
        if tag_type:
            self.tag_type = tag_type
        else:
            self.tag_type = 1

    def _parse_tokens(self, tokens, i, actions=True):
        token = tokens[i]
        tag = token[self.tag_type]
        if tag == self.match:
            return [E(self.name or safe_name(tag), token[0])], i + 1
        raise ParseException(tokens, i, 'Expected %s, got %s' % (self.match, tag), self)


class IWord(Word):
    """Case-insensitive match token text."""

    def __init__(self, match):
        super(IWord, self).__init__(match.lower())

    def _parse_tokens(self, tokens, i, actions=True):
        token_text = tokens[i][0]
        if token_text.lower() == self.match:
            return [E(self.name or safe_name(tokens[i][1]), tokens[i][0])], i + 1
        raise ParseException(tokens, i, 'Expected %s, got %s' % (self.match, tokens[i][0]), self)


class Regex(BaseParserElement):
    """Match token text with regular expression."""

    def __init__(self, pattern, flags=0, group=None):
        super(Regex, self).__init__()
        if isinstance(pattern, six.string_types):
            self.regex = re.compile(pattern, flags)
            self.pattern = pattern
        else:
            self.regex = pattern
            self.pattern = pattern.pattern
        self.group = group

    def _parse_tokens(self, tokens, i, actions=True):
        token_text = tokens[i][0]
        result = self.regex.search(token_text)
        if result:
            text = token_text if self.group is None else result.group(self.group)
            return [E(self.name or safe_name(tokens[i][1]), text)], i + 1
        raise ParseException(tokens, i, 'Expected %s, got %s' % (self.pattern, token_text), self)

    # Solves issues with deepcopying of records, jm2111
    # only the pattern is copied and the object is created from scratch
    def __deepcopy__(self, memodict={}):
        return type(self)(deepcopy(self.pattern, memodict))


class Start(BaseParserElement):
    """Match at start of tokens."""

    def __init__(self):
        super(Start, self).__init__()

    def _parse_tokens(self, tokens, i, actions=True):
        if i != 0:
            raise ParseException(tokens, i, 'Expected start of tokens', self)
        return [], i


class End(BaseParserElement):
    """Match at end of tokens."""

    def __init__(self):
        super(End, self).__init__()

    def _parse_tokens(self, tokens, i, actions=True):
        if i < len(tokens):
            raise ParseException(tokens, i, 'Expected end of tokens', self)
        return [], i


class ParseExpression(BaseParserElement):
    """Abstract class for combining and post-processing parsed tokens."""

    def __init__(self, exprs):
        super(ParseExpression, self).__init__()
        if isinstance(exprs, types.GeneratorType):
            exprs = list(exprs)
        if isinstance(exprs, six.text_type):
            self.exprs = [Word(exprs)]
        elif isinstance(exprs, collections.Sequence):
            if all(isinstance(expr, six.text_type) for expr in exprs):
                exprs = map(Word, exprs)
            self.exprs = list(exprs)
        else:
            try:
                self.exprs = list(exprs)
            except TypeError:
                self.exprs = [exprs]

    def __getitem__(self, i):
        return self.exprs[i]

    def append(self, other):
        self.exprs.append(other)
        return self

    def copy(self):
        ret = super(ParseExpression, self).copy()
        ret.exprs = [e.copy() for e in self.exprs]
        return ret

    def streamline(self):
        if not self.streamlined:
            super(ParseExpression, self).streamline()
            for e in self.exprs:
                if not e.streamlined:
                    e.streamline()
            # collapse nested exprs from e.g. And(And(And(a, b), c), d) to And(a,b,c,d)
            if len(self.exprs) == 2:
                other = self.exprs[0]
                if isinstance(other, self.__class__) and not other.actions and other.name is None:
                    self.exprs = other.exprs[:] + [self.exprs[1]]
                other = self.exprs[-1]
                if isinstance(other, self.__class__) and not other.actions and other.name is None:
                    self.exprs = self.exprs[:-1] + other.exprs[:]
        return self


class And(ParseExpression):
    """
    Match all in the given order.
    Can probably be replaced by the plus operator '+'?
    """

    def __init__(self, exprs):
        super(And, self).__init__(exprs)

    def _parse_tokens(self, tokens, i, actions=True):
        results = []
        for e in self.exprs:
            exprresults, i = e.parse(tokens, i)
            if exprresults is not None:
                results.extend(exprresults)
        return ([E(self.name, *results)] if self.name else results), i

    def __iadd__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        return self.append(other)


# class All(BaseParserElement):
#     """
#     All elements are present in any order. Other elements can be in between.
#     This is primarily used for table parsing, to see if all required elements are found in a row of the category table.
#     """
#
#     def __init__(self, *exprs):
#         super(All, self).__init__(*exprs)
#
#     # i am not sure if this has the correct parent, but essentially, for every expression provided we have to do
#     # something like a simple Match() not And() and then go on to the next expression with resetting the tokens to zero
#     # if all expressions are found individually return the result.
#
#     def _parse_tokens(self, tokens, i, actions=True):
#         results = []
#         for expression in self.exprs:
#             for e in expression:
#                 exprresults, i = e.parse(tokens, i)
#                 if exprresults is not None:
#                     results.extend(exprresults)
#         return ([E(self.name, *results)] if self.name else results), i


class Or(ParseExpression):
    """
    Match the longest.
    Can probably be replaced by the pipe operator '|'.
    """

    def _parse_tokens(self, tokens, i, actions=True):
        furthest_exception_i = -1
        furthest_match_i = -1
        furthest_exception = None
        for e in self.exprs:
            try:
                end_i = e.try_parse(tokens, i)
            except ParseException as err:
                if err.i > furthest_exception_i:
                    furthest_exception = err
                    furthest_exception_i = err.i
            except IndexError:
                if len(tokens) > furthest_exception_i:
                    furthest_exception = ParseException(tokens, len(tokens), '', self)
                    furthest_exception_i = len(tokens)
            else:
                if end_i > furthest_match_i:
                    furthest_match_i = end_i
                    furthest_match = e

        if furthest_match_i < 0:
            if furthest_exception is not None:
                raise furthest_exception
            else:
                raise ParseException(tokens, i, 'No alternatives match', self)

        # If a name is assigned to an Or, it replaces the name of the contained result
        if self.name:
            furthest_match = furthest_match.set_name(self.name)

        # NOTE: While it may seem that there is a performance gain to be made by not redoing
        # the parse result, it's balanced out by the fact that actions are not
        # performed for try_parse.
        result, result_i = furthest_match.parse(tokens, i, actions=actions)
        return result, result_i

    def __ixor__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        return self.append(other)


class Every(ParseExpression):
    """
    Match all of the containing parse expressions, and return the longest
    """

    def _parse_tokens(self, tokens, i, actions=True):
        furthest_exception_i = -1
        furthest_match_i = -1
        furthest_exception = None
        for e in self.exprs:
            try:
                end_i = e.try_parse(tokens, i)
            except IndexError:
                if len(tokens) > furthest_exception_i:
                    furthest_exception = ParseException(tokens, len(tokens), '', self)
                    furthest_exception_i = len(tokens)
            else:
                if end_i > furthest_match_i:
                    furthest_match_i = end_i
                    furthest_match = e

        if furthest_match_i < 0:
            if furthest_exception is not None:
                raise furthest_exception
            else:
                raise ParseException(tokens, i, 'No alternatives match', self)

        # If a name is assigned to an Every, it replaces the name of the contained result
        if self.name:
            furthest_match = furthest_match.set_name(self.name)

        result, result_i = furthest_match.parse(tokens, i, actions=actions)
        return result, result_i


class First(ParseExpression):
    """Match the first."""

    def __init__(self, exprs):
        super(First, self).__init__(exprs)

    def _parse_tokens(self, tokens, i, actions=True):
        furthest_i = -1
        furthest_exception = None
        for e in self.exprs:
            try:
                result, result_i = e.parse(tokens, i, actions=True)
                # If a name is assigned to a First, it replaces the name of the contained result
                if self.name:
                    for e in result:
                        e.tag = self.name
                return result, result_i
            except ParseException as err:
                if err.i > furthest_i:
                    furthest_exception = err
                    furthest_i = err.i
        else:
            if furthest_exception is not None:
                raise furthest_exception
            else:
                raise ParseException(tokens, i, 'No alternatives match', self)

    def __ior__(self, other):
        if isinstance(other, six.text_type):
            other = Word(other)
        return self.append(other)


class ParseElementEnhance(BaseParserElement):
    """Abstract class for combining and post-processing parsed tokens."""

    def __init__(self, expr):
        super(ParseElementEnhance, self).__init__()
        if isinstance(expr, six.text_type):
            expr = Word(expr)
        self.expr = expr

    def _parse_tokens(self, tokens, i, actions=True):
        if self.expr is not None:
            return self.expr.parse(tokens, i)
        else:
            raise ParseException('', i, 'Error', self)

    def streamline(self):
        if not self.streamlined:
            super(ParseElementEnhance, self).streamline()
            if self.expr is not None:
                if not self.expr.streamlined:
                    self.expr.streamline()
        return self


class FollowedBy(ParseElementEnhance):
    """
    Check ahead if matches.

    Example::

        Tn + FollowedBy('Neel temperature')
        Tn will match only if followed by 'Neel temperature', but 'Neel temperature' will not be part of the output/tree

    """

    def _parse_tokens(self, tokens, i, actions=True):
        self.expr.try_parse(tokens, i)
        return [], i


class Not(ParseElementEnhance):
    """
    Check ahead to disallow a match with the given parse expression.

    Example::

        Tn + Not('some_string')
        Tn will match if not followed by 'some_string'

    """

    def _parse_tokens(self, tokens, i, actions=True):
        try:
            self.expr.try_parse(tokens, i)
        except (ParseException, IndexError):
            pass
        else:
            raise ParseException(tokens, i, 'Encountered disallowed token', self)
        return [], i


class ZeroOrMore(ParseElementEnhance):
    """Optional repetition of zero or more of the given expression."""

    def _parse_tokens(self, tokens, i, actions=True):
        results = []
        try:
            results, i = self.expr.parse(tokens, i, actions)
            while 1:
                start_i = i
                tmpresults, i = self.expr.parse(tokens, start_i, actions)
                if tmpresults:
                    results.extend(tmpresults)
        except (ParseException, IndexError):
            pass
        return ([E(self.name, *results)] if self.name else results), i


class OneOrMore(ParseElementEnhance):
    """Repetition of one or more of the given expression."""

    def _parse_tokens(self, tokens, i, actions=True):
        # must be at least one
        results, i = self.expr.parse(tokens, i, actions)
        try:
            while 1:
                start_i = i
                tmpresults, i = self.expr.parse(tokens, start_i, actions)
                if tmpresults:
                    results.extend(tmpresults)
        except (ParseException, IndexError):
            pass
        return ([E(self.name, *results)] if self.name else results), i


class Optional(ParseElementEnhance):
    """
    Can be present but doesn't need to be.
    If present, will be added to the result/tree.
    """

    def __init__(self, expr):
        super(Optional, self).__init__(expr)

    def _parse_tokens(self, tokens, i, actions=True):
        results = []
        try:
            results, i = self.expr.parse(tokens, i, actions)
        except (ParseException, IndexError):
            pass
        return ([E(self.name, *results)] if self.name else results), i


class Group(ParseElementEnhance):
    """
    For nested tags; will group argument and give it a label, preserving the original sub-tags.
    Otherwise, the default behaviour would be to rename the outermost tag in the argument.
    Usage: Group(some_text)('new_tag) where 'some_text' is a previously tagged expression
    """

    def _parse_tokens(self, tokens, i, actions=True):
        results, i = self.expr.parse(tokens, i, actions)
        return ([E(self.name, *results)] if self.name else results), i


class SkipTo(ParseElementEnhance):
    """
    Skips to the next occurance of expression. Does not add the next occurance of expression to the parse tree.
    For example::

        entities + SkipTo(entities)

    will output ``entities`` only once. Whereas::

        entities + SkipTo(entities) + entities

    will output ``entities`` as well as the second occurrence of ``entities`` after an arbitrary number of tokens in between.
    """

    def __init__(self, expr, include=False):
        super(SkipTo, self).__init__(expr)
        self.include = include

    def _parse_tokens(self, tokens, i, actions=True):
        start_i = i
        tokens_length = len(tokens)
        while i <= tokens_length:
            try:
                self.expr.parse(tokens, i, actions=False)
                results = [E(safe_name(t[1]), t[0]) for t in tokens[start_i:i]]
                if self.include:
                    match_result, i = self.expr.parse(tokens, i, actions)
                    if match_result:
                        results.extend(match_result)
                return results, i
            except (ParseException, IndexError):
                i += 1
        raise ParseException(tokens, i, '', self)


class Hide(ParseElementEnhance):
    """
    Converter for ignoring the results of a parsed expression.
    It wouldn't appear in the generated xml element tree, but it would still be part of the rule.
    """

    def _parse_tokens(self, tokens, i, actions=True):
        results, i = super(Hide, self)._parse_tokens(tokens, i)
        return [], i

    def hide(self):
        return self


# Abbreviations
W = Word
I = IWord
R = Regex
T = Tag
H = Hide
