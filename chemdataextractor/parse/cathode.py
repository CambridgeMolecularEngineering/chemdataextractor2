from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re

from lxml import etree
from .cem import (
    cem,
    chemical_label,
    lenient_chemical_label,
)
from .common import lbrct, dt, rbrct
from ..utils import first
from .actions import merge, join
from .base import BaseSentenceParser
from .quantity import value_element, value_element_plain
from .elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore, Group, SkipTo
from .template import MultiQuantityModelTemplateParser, QuantityModelTemplateParser

log = logging.getLogger(__name__)

delimeters = R("^[:;\.,]$")

cathode_expression = (
    Optional(R(("[[Cc]athode(s?)")))
)
