# -*- coding: utf-8 -*-
"""
Base types for making category models.

:codeauthor: Callum Court (cc889@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import six
import copy
from abc import ABCMeta
from ..base import BaseModel, BaseType, FloatType, StringType, ListType, ModelMeta
from ...parse.elements import Any
from ...parse.auto import AutoSentenceParser, AutoTableParser, construct_unit_element, match_dimensions_of
from ...parse.category import construct_category_element


class _CategoryModelMeta(ModelMeta):
    """"""

    def __new__(mcs, name, bases, attrs):
        cls = super(_CategoryModelMeta, mcs).__new__(mcs, name, bases, attrs)
        return cls


class CategoryModel(six.with_metaclass(_CategoryModelMeta, BaseModel)):
    """
    Class for modelling categories. Subclasses of this model can be used in conjunction with Autoparsers to extract properties
    with zero human intervention. However, they must be constructed in a certain way for them to work optimally with autoparsers.
    Namely, they should have:

    - A specifier field with an associated parse expression (Optional, only required if autoparsers are desired). These parse expressions will be updated automatically using forward-looking Interdependency Resolution if the updatable flag is set to True.
    - These specifiers should also have required set to True so that spurious matches are not found.
    - If applicable, a compound field, named compound.

    Any parse_expressions set in the model should have an added action to ensure that the results are a single word. An example would be to call add_action(join) on each parse expression.
    """
    category = StringType(required=True)
    specifier = StringType(required=True)
    parsers = [AutoSentenceParser(), AutoTableParser()]

    def __str__(self):
        string = 'Category'
        return string
