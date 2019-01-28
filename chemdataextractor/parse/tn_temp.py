# -*- coding: utf-8 -*-
"""
Temporary test solution for the sort of parser that would be generated automatically by code for Tc.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""


from .auto import BaseAutoParser, AutoTableParser
from ..model.model import NeelTemperature


class NeelTemperatureParser(BaseAutoParser):
    model = NeelTemperature
    value_phrase_tag = 'neeltemperature'
    root_phrase_tag = 'neeltemperaturephrase'
    property_name = 'neel_temperature'


class NeelTemperatureTableParser(AutoTableParser):
    model = NeelTemperature
    value_phrase_tag = 'neeltemperature'
    root_phrase_tag = 'neeltemperaturephrase'
    property_name = 'neel_temperature'
