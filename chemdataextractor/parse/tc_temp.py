# -*- coding: utf-8 -*-
"""
Temporary test solution for the sort of parser that would be generated automatically by code for Tc.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

from .auto import BaseAutoParser, AutoTableParser
from ..model.model import CurieTemperature


class CurieTemperatureParser(BaseAutoParser):
    model = CurieTemperature
    value_phrase_tag = 'curietemperature'
    root_phrase_tag = 'curietemperaturephrase'
    property_name = 'curie_temperature'


class CurieTemperatureTableParser(AutoTableParser):
    model = CurieTemperature
    value_phrase_tag = 'curietemperature'
    root_phrase_tag = 'curietemperaturephrase'
    property_name = 'curie_temperature'
