# -*- coding: utf-8 -*-
"""
Error classes for ChemDataExtractor.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class ChemDataExtractorError(Exception):
    """Base ChemDataExtractor exception."""
    pass


class ReaderError(ChemDataExtractorError):
    """Raised when a reader is unable to read a document."""


class ModelNotFoundError(ChemDataExtractorError):
    """Raised when a model file could not be found."""
