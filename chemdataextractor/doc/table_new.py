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
from .element import CaptionedElement
from tabledataextractor import Table as TdeTable
from tabledataextractor.output.print import print_table
from ..parse.auto import TableAutoParser
from ..doc.table import Table as TableOld

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
        self.parsers = []
        self.append_parsers()
        #print(label, caption)
        #print_table(self.tde_table.raw_table)
        #print(self.tde_table)
        #print("\n\n")

    def append_parsers(self):
        """
        Appends parser list to include automated table parsers based on the models explicitly passed in or
        found in ``chemdataextractor.model.model``

        :return: list of TableAutoParser objects
        """
        for obj in self.models:
            self.parsers.append(TableAutoParser(obj))
        for name, obj in inspect.getmembers(model):
            if inspect.isclass(obj):
                self.parsers.append(TableAutoParser(obj))

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
        atp = parser
        for cell in category_table:
            if atp.parse(cell):
                for result in atp.parse(cell):
                    if result.serialize() != {}:
                        yield result.serialize()

    @property
    def records(self):
        """Chemical records that have been parsed from the table."""
        table_records = []
        for parser in self.parsers:
            for record in self._parse_table(parser, self.category_table):
                table_records.append(record)
        return table_records



