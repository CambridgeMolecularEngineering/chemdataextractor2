# -*- coding: utf-8 -*-
"""

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging


__title__ = 'ChemDataExtractor'
__version__ = '2.01'
__author__ = 'Matt Swain, Callum Court, Edward Beard, Juraj Mavracic and Taketomo Isazawa'
__email__ = 'm.swain@me.com, cc889@cam.ac.uk, ejb207@cam.ac.uk, jm2111@cam.ac.uk, ti250@cam.ac.uk'
__license__ = 'MIT'
__copyright__ = 'Copyright 2019 Matt Swain and contributors'

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
