# -*- coding: utf-8 -*-
"""
Relex package 

For performing semi-supervised chemical Relationship Extraction using the Snowball Algorithm

This package is still under development, please use it for beta testing only and notify myself of any bugs

cc889
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import os
from .snowball import Snowball
from.relationship import ChemicalRelationship, Relation
from.entity import Entity
from .phrase import Phrase
from .cluster import Cluster
from .pattern import Pattern


__title__ = 'ChemDataExtractor'
__version__ = '1.4.0'
__author__ = 'Callum Court'
__email__ = 'cc889@cam.ac.uk'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 Matt Swain and contributors'

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
