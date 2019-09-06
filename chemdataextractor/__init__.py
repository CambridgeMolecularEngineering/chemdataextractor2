# -*- coding: utf-8 -*-
"""

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging


__title__ = 'ChemDataExtractor'
__version__ = '1.3.0'
__author__ = 'Matt Swain'
__email__ = 'm.swain@me.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 Matt Swain and contributors'

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# jm2111
# all messages with effective level higher or equal to warning will be shown
# in every module/file set:
#     log = logging.getLogger(__name__)
#     log.setLevel(logging.DEBUG)
# to change the effective level of the module logger
logging.basicConfig(format=u'%(levelname)-10s in %(filename)-20s--> %(message)s', level=logging.INFO, filename='log.txt', filemode='w')

from .doc.document import Document
