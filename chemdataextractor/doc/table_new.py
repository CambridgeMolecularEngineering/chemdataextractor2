# -*- coding: utf-8 -*-
"""
Table document elements v2.0

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from collections import defaultdict

from ..model import Compound, ModelList
from ..nlp.tag import NoneTagger
from ..nlp.tokenize import FineWordTokenizer
from ..utils import memoized_property
from .element import CaptionedElement
from .text import Sentence
# from ..parse.new_parsers import CurieTemperatureParser, NeelTemperatureParser
from tabledataextractor import Table as TdeTable

log = logging.getLogger(__name__)

# parsers = [CurieTemperatureParser(), NeelTemperatureParser()]


class Table(CaptionedElement):
    """New 
    
    Arguments:
        CaptionedElement {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """


    def __init__(self, caption, label=None, table_data=[], **kwargs):
        super(Table, self).__init__(caption=caption, label=label, **kwargs)
        # can pass any kwargs into TDE directly
        self.tde_table = TdeTable(table_data, **kwargs)
        self.category_table = self.tde_table.category_table
        # print('\n\n', self.tde_table)
        # print(self.category_table)

    # def set_parsers(self):
    #     #: Table cell parsers
    #     if self.document:
    #         try:
    #             c = self.document.config
    #             conf_parsers = c['PARSERS'][self.__class__.__name__]
    #             self.parsers =[TABLE_PARSERS[p] for p in conf_parsers]
    #         except KeyError:
    #             pass
    #     return self

    @property
    def document(self):
        return self._document

    # @document.setter
    # def document(self, document):
    #     self._document = document
    #     self.caption.document = document
    #     for row in self.headings:
    #         for cell in row:
    #             cell.document = document
    #     for row in self.rows:
    #         for cell in row:
    #             cell.document = document

    def serialize(self):
        """Convert Table element to python dictionary."""
        data = {
            'type': self.__class__.__name__,
            'caption': self.caption.serialize(),
        }
        return data
    
    @property
    def definitions(self):
        return self.caption.definitions

    # def _repr_html_(self):
    #     html_lines = ['<table class="table">']
    #     html_lines.append(self.caption._repr_html_  ())
    #     html_lines.append('<thead>')
    #     for hrow in self.headings:
    #         html_lines.append('<tr>')
    #         for cell in hrow:
    #             html_lines.append('<th>' + cell.text + '</th>')
    #     html_lines.append('</thead>')
    #     html_lines.append('<tbody>')
    #     for row in self.rows:
    #         html_lines.append('<tr>')
    #         for cell in row:
    #             html_lines.append('<td>' + cell.text + '</td>')
    #     html_lines.append('</tbody>')
    #     html_lines.append('</table>')
    #     return '\n'.join(html_lines)

    @property
    def records(self):
        """Chemical records that have been parsed from the table.
        """
        table_records = []
        return table_records


class Cell(Sentence):
    word_tokenizer = FineWordTokenizer()
    # pos_tagger = NoneTagger()
    ner_tagger = NoneTagger()

    @memoized_property
    def abbreviation_definitions(self):
        """Empty list. Abbreviation detection is disabled within table cells."""
        return []

    @property
    def records(self):
        """Empty list. Individual cells don't provide records, this is handled by the parent Table."""
        return []
