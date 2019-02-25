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

from .element import CaptionedElement
from tabledataextractor import Table as TdeTable
from tabledataextractor.exceptions import TDEError
from ..doc.text import Cell

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Table(CaptionedElement):
    """
    Main Table object. Relies on TableDataExtractor.
    """

    def __init__(self, caption, label=None, table_data=[], models=None, **kwargs):
        """
        In addition to the parameters below, any keyword arguments supported by TableDataExtractor.TdeTable
        can be passed in as keyword arguments and they will be passed on to TableDataExtractor.TdeTable.

        .. note::

            If intended as part of a :class:`~chemdataextractor.doc.document.Document`,
            an element should either be initialized with a reference to its containing document,
            or its :attr:`document` attribute should be set as soon as possible.
            If the element is being passed in to a :class:`chemdataextractor.doc.document.Document`
            to initialise it, the :attr:`document` attribute is automatically set
            during the initialisation of the document, so the user does not need to worry about this.

        :param BaseElement caption: The caption for the element.
        :param str label: (Optional) The label for the captioned element, e.g. Table 1 would have a label of 1.
        :param list table_data: (Optional) Table data to be passed on to TableDataExtractor to be parsed.
            Refer to documentation for TableDataExtractor.TdeTable for more information on how this should be structured.
        :param list[chemdataextractor.models.BaseModel] models: A list of models for this element to parse.
            If the element is part of another element (e.g. a :class:`~chemdataextractor.doc.text.Sentence`
            inside a :class:`~chemdataextractor.doc.text.Paragraph`), or is part of a :class:`~chemdataextractor.doc.document.Document`,
            this is set automatically to be the same as that of the containing element, unless manually set otherwise.
        :param Document document: (Optional) The document containing this element.
        :param Any id: (Optional) Some identifier for this element. Must be equatable.
        """
        super(Table, self).__init__(caption=caption, label=label, models=models, **kwargs)
        try:
            self.tde_table = TdeTable(table_data, **kwargs)  # can pass any kwargs into TDE directly
        except TDEError:
            self.category_table = None
            self.heading = None
        else:
            self.category_table = self.tde_table.category_table
            self.heading = self.tde_table.title_row if self.tde_table.title_row is not None else []

    def serialize(self):
        """
        Convert self to a dictionary. The key 'type' will contain
        the name of the class being serialized, and the key 'caption' will contain
        a serialized representation of :attr:`caption`, which is a :class:`~chemdataextractor.doc.element.BaseElement`
        """
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
                cde_cell = Cell(cell[0] + ' ' + ' '.join(cell[1]) + ' ' + ' '.join(cell[2]))
                results = parser.parse_cell(cde_cell)
                for result in results:
                    if result.serialize() != {}:
                        yield {parser.model.__name__: result.serialize()}

    @property
    def records(self):
        caption_records = self.caption.records
        # print(caption_records.serialize())
        table_records = []
        for model in self.models:
            for parser in model.parsers:
                for record in self._parse_table(parser, self.category_table):
                    table_records.append(record)
        return table_records



