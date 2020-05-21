# -*- coding: utf-8 -*-
"""
Parser for automatic parsing, without user-written parsing rules for finding Snowball Candidates.
.. codeauthor:: Callum Court <cc889@cam.ac.uk>

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import six
import copy

from ..parse.cem import cem, chemical_label, lenient_chemical_label
from ..parse.actions import merge, join
from ..parse.elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, Group, SkipTo, Or
from ..utils import first
from ..parse.quantity import magnitudes_dict, value_element, extract_units, value_element_plain, lbrct, rbrct
from ..parse.base import BaseSentenceParser, BaseParser, BaseTableParser
from ..parse.auto import construct_unit_element, match_dimensions_of, create_entities_list
import xml.etree.ElementTree as etree

log = logging.getLogger(__name__)



