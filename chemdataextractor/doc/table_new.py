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
import copy

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
        except TDEError as e:
            log.error("TableDataExtractor error: {}".format(e))
            self.category_table = []
            self.tde_table = None
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

    def _merge_partial_records(self, partial_table_records):
        """
        Merges partial records found in different rows of the table, based on the 'contextual' flags.
        A 'shared_element' can be defined below based on which the merging will be performed.
        The function returns merged records, that may still be incomplete. Completeness based on 'required' flags
        is tested outside.

        Returns a list of not serialized records.
        """
        if not partial_table_records or len(partial_table_records) <= 1:
            return partial_table_records

        #: field based on which merging is done
        shared_element = 'compound'

        contextual_records = []
        updated_records = []

        for i, record_i in enumerate(partial_table_records):
            for j in range(i+1, len(partial_table_records)):
                record_j = partial_table_records[j]

                fields_i = set([])
                for field in record_i.fields:
                    if record_i.__getattribute__(field):
                        fields_i.add(field)

                fields_j = set([])
                for field in record_j.fields:
                    if record_j.__getattribute__(field):
                        fields_j.add(field)

                # using a symmetric difference will ensure that we have correct output if we have shared elements
                # shared elements will not be found in sym_diff
                sym_diff = fields_i.symmetric_difference(fields_j)
                # we need the intersection to check if it includes the shared element
                intersection = fields_i.intersection(fields_j)

                record = None
                record_update = False
                if sym_diff \
                        and shared_element in intersection and len(intersection) == 1 \
                        and record_i.__getattribute__(list(intersection)[0]) == \
                        record_j.__getattribute__(list(intersection)[0]):

                    # update record_i until we have the full record
                    # this is for the case that the contextual elements are in record_j
                    if not record_update:
                        record = copy.copy(record_i)
                        for field in sym_diff:
                            if not record_i.__getattribute__(field) and record_i.fields[field].contextual:
                                record.__setitem__(field, record_j.__getattribute__(field))
                                record_update = True
                                updated_records.append(i)
                                updated_records.append(j)
                    # update record_j until we have the full record
                    # this is for the case that the contextual elements are in record_i
                    if not record_update:
                        record = copy.copy(record_j)
                        for field in sym_diff:
                            if not record_j.__getattribute__(field) and record_j.fields[field].contextual:
                                record.__setitem__(field, record_i.__getattribute__(field))
                                record_update = True
                                updated_records.append(i)
                                updated_records.append(j)

                if record_update:
                    log.debug("Record i = {}: {}".format(i, record_i.serialize()))
                    log.debug("Record j = {}: {}".format(j, record_j.serialize()))
                    log.debug("Record inside i = {}, j = {}: {}".format(i, j, record.serialize()))
                    contextual_records.append(record)
            if i not in updated_records:
                log.debug("Record outside i = {}: {}".format(i, record_i.serialize()))
                contextual_records.append(record_i)

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

        # obtain table records
        table_records = []
        partial_table_records = []

        for model in self.models:
            for parser in model.parsers:

                # the partial records are obtained from the autoparser
                for record in self._parse_table(parser, self.category_table):

                    # add caption compound if necessary, and append to record
                    if 'compound' in model.fields \
                            and not record.compound \
                            and caption_compounds \
                            and model.compound.contextual:
                        record.compound = caption_compounds[0]  # the first compound from the caption is used by default

                    partial_table_records.append(record)

                # the partial records are merged
                partial_table_records_merged = self._merge_partial_records(partial_table_records)

                # a check is performed to see if all the 'required' elements of the merged table records are satisfied
                for record in partial_table_records_merged:
                    requirements = True

                    # check if all required elements are present
                    unmet_requirements = []
                    for field in model.fields:
                        if model.fields[field].required \
                                and not record.__getattribute__(field):
                            unmet_requirements.append(field)
                            requirements = False
                    # check if unknown elements from a different model are present
                    for field in record.fields:
                        if field not in model.fields:
                            requirements = False

                    if requirements:
                        table_records.append(record)

                    # add the record if only the compound is missing
                    elif not requirements and len(unmet_requirements) == 1 and unmet_requirements[0] == 'compound':
                        table_records.append(record)

        # Addition of the serialized caption records
        caption_records = [c for c in caption_records if not c.is_contextual]
        table_records += caption_records

        return table_records



