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
from chemdataextractor.model.model import Compound

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Table(CaptionedElement):
    """
    Main Table object. Relies on TableDataExtractor.
    """

    def __init__(self, caption, label=None, table_data=[], models=None, **kwargs):
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
                cde_cell = Cell(cell[0] + ' ' + ' '.join(cell[1]) + ' ' + ' '.join(cell[2]))
                results = parser.parse_cell(cde_cell)
                for result in results:
                    # [print(res) for res in result]
                    if result.serialize() != {}:
                        # yield {parser.model.__name__: result.serialize()}
                        yield result

    def _merged_partial_records(self, partial_table_records):
        """Merges partial records found in the table based on the 'required' and 'contextual' flags"""
        if not partial_table_records or len(partial_table_records) <= 1:
            return None

        #: element used for merging
        shared_element = 'compound'

        contextual_records = []
        for i, record_i in enumerate(partial_table_records):
            #for j, record_j in enumerate(partial_table_records, start=i+1):

            j = i + 1
            if j < len(partial_table_records):
                record_j = partial_table_records[i+1]
            else:
                break


            # fields_i = record_i.fields
            # fields_j = record_j.fields

            # TODO The order that the partial records are coming in is wrong
            # TODO This seems to work now, NOW, use only the first combination as real result.
            # It seems that something is wrong with the enumerate function, YES!! It doesn't work like that!
            # print(i, record_i.serialize())
            # print(j, record_j.serialize())

            fields_i = set([])
            for field in record_i.fields:
                if record_i.__getattribute__(field):
                    # print(i, record_i.__getattribute__(field))
                    fields_i.add(field)

            fields_j = set([])
            for field in record_j.fields:
                if record_j.__getattribute__(field):
                    # print(j, record_j.__getattribute__(field))
                    fields_j.add(field)

            # using a symmetric difference will ensure that we have no correct output if we have shared elements
            sym_diff = fields_i.symmetric_difference(fields_j)
            # we want to check if the intersection is the 'shared_element' only
            intersection = fields_i.intersection(fields_j)

            # print(i, j, sym_diff)
            # print(i, j, intersection)

            record = None
            if sym_diff and shared_element in intersection and len(intersection) == 1:
                # we will update record_i until we have the full record
                record = record_i
                for field in sym_diff:
                    # if record_i doesn't have the record, record_j must have it
                    if not record_i.__getattribute__(field):
                        record.__setitem__(field, record_j.__getattribute__(field))
                        print(i, j, record.serialize())

            # print("")

            contextual_records.append(record)
        # print("TEST")
        # print(contextual_records)
        return contextual_records

    @property
    def records(self):
        """Chemical records that have been parsed from the table."""

        # get the compounds from the caption
        caption_records = self.caption.records
        caption_compounds = []
        for record in caption_records:
            if isinstance(record, Compound):
                caption_compounds += [record]

        # obtain pure table records
        requirements = True
        table_records = []
        partial_table_records = []
        for model in self.models:
            for parser in model.parsers:
                for record in self._parse_table(parser, self.category_table):

                    # add caption compound if necessary, and append to record
                    if 'compound' in model.fields and not record.compound and caption_compounds and model.compound.contextual:
                        record.compound = caption_compounds[0]  # the first compound from the caption is used by default

                    # check if all the required elements have been found
                    for field in model.fields:
                        if model.fields[field].required and not record.__getattribute__(field):
                            requirements = False

                    if requirements:
                        table_records.append({parser.model.__name__: record.serialize()})
                    elif not requirements:
                        # store as partial_table_record
                        partial_table_records.append(record)

        # TODO Also include compound in the interdependency function
        #: only contextual for within a table
        # table_records.append(self._merged_partial_records(partial_table_records))
        self._merged_partial_records(partial_table_records)

        # TODO Merge pure caption records to the table records?
        # caption_records = [c for c in caption_records if not c.is_contextual]
        # table_records += caption_records
        return table_records



