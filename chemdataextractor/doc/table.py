# -*- coding: utf-8 -*-
"""
Table document elements

.. codeauthor: Juraj Mavračić <jm2111@cam.ac.uk>

.. codeauthor: Callum Court <cc889@cam.ac.uk>

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import copy
import six

from .element import CaptionedElement
from tabledataextractor import Table as TdeTable
from tabledataextractor import TrivialTable as TrivialTdeTable
from tabledataextractor.exceptions import TDEError
from ..doc.text import Cell
from ..model.model import Compound
from ..model.base import ModelList, ModelType
from ..utils import memoized_property
from pprint import pprint

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
        :param list[chemdataextractor.models.BaseModel] models: (Optional) A list of models for this element to parse.
            If the element is part of another element (e.g. a :class:`~chemdataextractor.doc.text.Sentence`
            inside a :class:`~chemdataextractor.doc.text.Paragraph`), or is part of a :class:`~chemdataextractor.doc.document.Document`,
            this is set automatically to be the same as that of the containing element, unless manually set otherwise.
        :param Document document: (Optional) The document containing this element.
        :param Any id: (Optional) Some identifier for this element. Must be equatable.
        """
        super(Table, self).__init__(caption=caption, label=label, models=models, **kwargs)
        try:
            #: TableDataExtractor `Table` object. Can pass any kwargs into TDE directly.
            self.tde_table = TdeTable(table_data, **kwargs)

        except (TDEError, TypeError) as e:
            log.error("TableDataExtractor 'Table' error: {}".format(e))
            log.info("Attempting TableDataExtractor 'TrivialTable' interpretation.")

            try:
                #: TableDataExtractor `TrivialTable` object. Can pass any kwargs into TDE directly.
                self.tde_table = TrivialTdeTable(table_data, standardize_empty_data=True, **kwargs)
            except (TDEError, TypeError) as e:
                log.error("TableDataExtractor 'TrivialTable' error: {}".format(e))
                self.tde_subtables = []
                self.tde_table = None
                self.heading = None

    @memoized_property
    def cde_tables(self):
        """
        CDE tables are lists of lists of Cells, that are used for the purpose of parsing
        in CDE. For other purposes, the underlying TDE table (`tde_table`) is probably more useful.
        """
        cde_tables = []
        if self.tde_table is not None:
            # get the subtables
            self.tde_subtables = self.tde_table.subtables
            # adjust the CDE Table heading from TDE results
            self.heading = self.tde_table.title_row if self.tde_table.title_row is not None else []

            if self.tde_subtables:
                for table in self.tde_subtables:
                    cde_tables.append(self._create_cde_table(table))

            else:
                cde_tables = [self._create_cde_table(self.tde_table)]
        return cde_tables

    def _create_cde_table(self, tde_table, assign_document=True):
        """
        Creates a CDE Table from a TDE table. A CDE table is a list of cells, so this returns a list
        of list of Cell objects, which is then used for parsing.
        """
        cde_tables = []
        document = None
        if assign_document:
            document = self.document
        for category_table in self._category_tables(tde_table):
            cde_table = []
            for cell in category_table:
                cde_cell = Cell.from_tdecell(cell, models=self.models, document=document)
                cde_table.append(cde_cell)
            cde_tables.append(cde_table)
        return cde_tables

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

    def _parse_table(self, parser, cde_table):
        """
        Parses a table. The model and the category table have to be provided.

        :param parser: parser to use for parsing of one row of the category table
        :param cde_table: list of Cell objects
        :return: Yields one result at a time
        """
        if hasattr(parser, 'parse_cell'):
            for cde_cell in cde_table:
                # print(cde_cell.tagged_tokens)
                log.debug(parser)
                results = parser.parse_cell(cde_cell)
                for result in results:
                    if result.serialize() != {}:
                        # yield {parser.model.__name__: result.serialize()}
                        # adding of the row/column header categories to the record for potential merging later
                        result.table_row_categories = ' '.join(cde_cell.row_categories)
                        result.table_col_categories = ' '.join(cde_cell.col_categories)
                        yield result

    @property
    def records(self):
        table_records = ModelList()
        caption_records = self.caption.records
        for table in self.cde_tables:
            table_records.extend(self._records_for_cde_tables(table, caption_records))
        return table_records

    def _records_for_cde_tables(self, cde_tables, caption_records=None):
        """
        Get the records for the given TDE Table
        The function works via the following steps:

        - Step 1: The records are parsed from each cell using the parsers for each model
        - Step 2: Consolidate records with matching rows or columns
        - Step 3: Any strict subsets are removed from this list
        - Step 4: Consolidate records globally throughout the table
        - Step 5: Remove any subsets
        - Step 6: Merge in any records from the caption

        :param table: Input TableDataExtractor object
        :type table: TableDataExtractor.Table
        :param ModelList caption_records: Any records found in the caption for this table
        :return: A list of records found in this table
        :rtype: ModelList of BaseModels
        """
        if not caption_records:
            caption_records = ModelList()

        # Step 1
        table_records = ModelList()
        for model in self._streamlined_models:
            for parser in model.parsers:
                for cde_table in cde_tables:
                    for record in self._parse_table(parser, cde_table):
                        if not record.is_empty:
                            table_records.append(record)

        # Step 2
        self._consolidate_by_row_col(table_records)

        # Step 3
        table_records.remove_subsets(strict=True)

        # Step 4
        self._consolidate(table_records)

        # Step 5
        table_records.remove_subsets()

        # Step 6
        caption_records = ModelList(*[c for c in caption_records if c.required_fulfilled])
        table_records = self._merge(table_records, caption_records)

        return table_records

    def _category_tables(self, table):
        """
        Yields the category table and row category tables for a given TableDataExtractor table.
        :param table: Input TableDataExtractor object
        :type table: TableDataExtractor.Table
        :return: list of category tables (python lists)
        """
        yield table.category_table
        while table.row_categories is not None:
            yield table.row_categories.category_table
            table = table.row_categories

    def _consolidate_by_row_col(self, records):
        """
        Merge records depending on the row and column that they were found in.
        The given list of records is mutated by this function.

        :param ModelList(BaseModel) records: The records to be consolidated
        """
        # Create a dictionaries where the keys are the column and row headers.
        col_first = {}
        row_first = {}
        for record in records:
            col_key = ' '.join(record.table_col_categories)
            row_key = ' '.join(record.table_row_categories)
            if col_key in col_first.keys():
                col_first[col_key].append(record)
            else:
                col_first[col_key] = ModelList(record)
            if row_key in row_first.keys():
                row_first[row_key].append(record)
            else:
                row_first[row_key] = ModelList(record)

        # Consolidate for each row/column
        for _, records in six.iteritems(row_first):
            self._consolidate(records)
        for _, records in six.iteritems(col_first):
            self._consolidate(records)

    def _consolidate(self, records, contextual=False):
        """
        Function to consolidate a given list of records. The records are split into
        a number of segments, where each segment contains only records of a certain 'parent' type
        and any record not of that type that could be merged into it based on type information (child records).

        All child records are first merged into the parent records, then the parent records are merged with each other.

        :param ModelList(BaseModel) records: The list of models that is to be consolidated.
        :param bool contextual: Whether to only merge in contextual fields or to merge in all fields.
        """
        function_name = 'merge_all'
        if contextual:
            function_name = 'merge_contextual'
        segmented_records = {}
        # A dictionary with a Model class as the key, and
        # [A list of all records contained in `records` of that type,
        #  a list of all instances of the submodels contained in `records`]

        all_models = {}
        # A dictionary with a Model class as a key and a list of all submodels of that
        # model as the value.

        # Populate the all_models dictionary and initialise the segmented_records dictionary
        for model in self._streamlined_models:
            flattened_model = list(model.flatten())
            all_models[model] = flattened_model
            segmented_records[model] = [ModelList(), ModelList()]

        # Create the segmented_records dictionary
        for record in records:
            if not hasattr(record, '_merged_in'):
                record._merged_in = []
            for root_model, submodels in six.iteritems(all_models):
                if isinstance(record, root_model):
                    segmented_records[root_model][0].append(record)
                elif type(record) in submodels:
                    segmented_records[root_model][1].append(record)

        # Do all the actual merging
        record_set = set()
        for model_type, segment in six.iteritems(segmented_records):
            # Merge all records of the parent type with all records of the child type
            for record_of_type in segment[0]:
                for record_of_subtype in segment[1]:
                    if model_type not in record_of_subtype._merged_in:
                        if getattr(record_of_type, function_name)(record_of_subtype):
                            record_of_subtype._merged_in.append(model_type)

            # Merge all records of the parent type with other records of the parent type
            i = 0
            records_of_type = segment[0]
            while i < len(records_of_type):
                j = 0
                while j < len(records_of_type):
                    if i != j and not records_of_type[i].is_subset(records_of_type[j]):
                        getattr(records_of_type[i], function_name)(records_of_type[j])
                    j += 1
                i += 1
            record_set.update(records_of_type)

        final_records = ModelList(*list(record_set))
        final_records.remove_subsets()
        return final_records

    def _merge(self, records_1, records_2):
        """
        Merge in records from records_2 into records_1.

        .. note::

            This function both mutates and returns records_1

        :param ModelList(BaseModel) records_1: The records into which records_2 will be merged.
        :param ModelList(BaseModel) records_2: The records that will be merged into records_1.
        :return: The merged list
        :rtype: ModelList(BaseModel)
        """
        for record in records_1:
            for other_record in records_2:
                record.merge_contextual(other_record)
        records_1.extend(records_2)
        return records_1

    def _remove_unfulfilled(self, records):
        """
        Remove any records where any non-contextual required fields is not fulfilled.

        :param ModelList(BaseModel) records: The list of records from where records with unfulfilled non-contextual, required fields will be removed.
        :return: The cleaned list of records.
        :rtype: ModelList(BaseModel)
        """
        new_records = ModelList()
        for record in records:
            if record.noncontextual_required_fulfilled:
                new_records.append(record)
        return new_records

    @property
    def elements(self):
        elements = []
        for table in self.cde_tables:
            for subtable in table:
                for cell in subtable:
                    elements.append(cell)
        elements.append(self.caption)
        return elements
