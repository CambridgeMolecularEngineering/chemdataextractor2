# -*- coding: utf-8 -*-
"""
Temporary test solution for the sort of parser that would be generated automatically by code for cn.

:codeauthor: Juraj Mavračić (jm2111@cam.ac.uk)
"""

from .auto import BaseAutoParser, AutoTableParser
from ..model.model import CoordinationNumber


class CoordinationNumberParser(BaseAutoParser):
    model = CoordinationNumber
    value_phrase_tag = 'coordinationnumber'
    root_phrase_tag = 'coordinationnumberphrase'
    property_name = 'coordination_number'


class CoordinationNumberTableParser(AutoTableParser):
    model = CoordinationNumber
    value_phrase_tag = 'coordinationnumber'
    root_phrase_tag = 'coordinationnumberphrase'
    property_name = 'coordination_number'


def parser(category_table):
    atp = CoordinationNumber()
    for cell in category_table:
        if atp.parse(cell):
            for result in atp.parse(cell):
                # print(cell)
                if result.serialize() != {}:
                    print(result.serialize())
                    pass