# -*- coding: utf-8 -*-
"""
Parser for sentences that provide contextual information, such as apparatus, solvent, and temperature.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re
from lxml import etree

from .common import optdelim, hyphen, slash
from ..utils import first
from ..parse.base import BaseSentenceParser
from .actions import join, merge, fix_whitespace
from .cem import chemical_name
from .elements import I, T, R, W, ZeroOrMore, Optional, Group, OneOrMore, Any, Not

log = logging.getLogger(__name__)

dt = T('DT')

apparatus_type = R('^\d{2,}$') + W('MHz')
brands = I('HORIBA') + I('Jobin') + I('Yvon') | I('Hitachi') | I('Bruker') | I('Cary') | I('Jeol') | I('PerkinElmer') | I('Agilent') | I('Shimadzu') | I('Varian')
models = I('FluoroMax-4') | I('F-7000') | I('AVANCE') | I('Digital') | R('\d\d\d+') | I('UV–vis-NIR') | I('Mercury') | I('Avatar') | I('thermonicolet') | I('pulsed') | I('Fourier') | I('transform')
instrument = I('spectrofluorimeter') | I('spectrophotometer') | Optional(I('fluorescence')) + I('spectrometer') | Optional(I('nmr')) + I('workstation') | W('NMR') | I('instrument') | I('spectrometer')
apparatus = (ZeroOrMore(T('JJ')) + Optional(apparatus_type) + OneOrMore(T('NNP') | T('NN') | brands) + ZeroOrMore(T('NNP') | T('NN') | T('HYPH') | T('CD') | brands | models) + Optional(instrument))('apparatus').add_action(join).add_action(fix_whitespace)
apparatus_blacklist = R('^(following|usual|equation|standard|accepted|method|point|temperature|melting|boiling)$', re.I)
apparatus_phrase = (W('with') | W('using') | W('on')).hide() + Optional(dt).hide() + Not(apparatus_blacklist) + apparatus


class ApparatusParser(BaseSentenceParser):

    root = apparatus_phrase

    def interpret(self, result, start, end):
        log.debug(etree.tostring(result))
        apparatus = self.model(name=first(result.xpath('./text()')))
        log.debug(apparatus.serialize())
        yield apparatus
