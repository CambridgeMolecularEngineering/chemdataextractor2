# -*- coding: utf-8 -*-
"""
Temporary test solution for the sort of parser that would be generated automatically by code for cn labels.

:codeauthor: Juraj Mavračić (jm2111@cam.ac.uk)
"""

from .auto import BaseAutoParser, AutoTableParser
from ..model.model import CNLabel


class CNLabelParser(BaseAutoParser):
    model = CNLabel
    # root_phrase_tag = 'cn_label_phrase'
    # property_name = 'cn_label'


class CNLabelTableParser(AutoTableParser):
    model = CNLabel
    # root_phrase_tag = 'cn_label_phrase'
    # property_name = 'cn_label'


# def parser(category_table):
#     atp = CNLabel()
#     for cell in category_table:
#         if atp.parse(cell):
#             for result in atp.parse(cell):
#                 # print(cell)
#                 if result.serialize() != {}:
#                     print(result.serialize())
#                     pass