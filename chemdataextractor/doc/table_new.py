# -*- coding: utf-8 -*-
"""
Table document elements v2.0

.. codeauthor: Juraj Mavračić (jm2111@cam.ac.uk)

.. codeauthor: Callum Court (cc889@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from collections import defaultdict
import inspect

from ..model import Compound, ModelList
# from ..doc import Sentence
from ..utils import memoized_property
from ..model import model
from ..model.base import BaseModel
from .element import CaptionedElement
from tabledataextractor import Table as TdeTable
from tabledataextractor.output.print import print_table
from ..parse.auto import AutoTableParser
from ..parse.base import BaseParser
from ..doc.table import Table as TableOld
from ..doc.text import Cell

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Table(CaptionedElement):
    """
    Main Table object. Relies on TableDataExtractor
    """

    def __init__(self, caption, label=None, table_data=[], models=[], **kwargs):
        super(Table, self).__init__(caption=caption, label=label, **kwargs)
        #print("Table data:", table_data)
        self.tde_table = TdeTable(table_data, **kwargs)  # can pass any kwargs into TDE directly
        self.category_table = self.tde_table.category_table
        self.heading = self.tde_table.title_row if self.tde_table.title_row is not None else []
        self.models = models
        #print(label, caption)
        #print_table(self.tde_table.raw_table)
        #print(self.tde_table)
        #print("\n\n")

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

    @staticmethod
    def _parse_table(parser, category_table):
        """
        Parses a table. The model and the category table have to be provided.

        :param parser: parser to use for parsing of one row of the category table
        :param category_table: list, output of TableDataExtractor
        :return: Yields one result at a time
        """
        for cell in category_table:
            if hasattr(parser, 'parse_cell'):
                cde_cell = Cell(cell[0] + ' ' + ' '.join(cell[1]) + ' '.join(cell[2]))
                results = parser.parse_cell(cde_cell)
                for result in results:
                    if result.serialize() != {}:
                        # TODO: Ask Juraj: Shouldn't this yield the result not the serialized version of the result?
                        yield result.serialize()

    @property
    def records(self):
        """Chemical records that have been parsed from the table."""
        # caption_records = self.caption.records
        table_records = []
        for model in self.models:
            for parser in self.parsers:
                for record in self._parse_table(parser, self.category_table):
                    table_records.append(record)
        return table_records



