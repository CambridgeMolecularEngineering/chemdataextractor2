# -*- coding: utf-8 -*-
"""
Table document elements v2.0

.. codeauthor: Juraj Mavračić <jm2111@cam.ac.uk>

.. codeauthor: Callum Court <cc889@cam.ac.uk>

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
from ..model.model import Compound
from ..model.base import ModelList, ModelType

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
            #: TableDataExtractor `Table` object. Can pass any kwargs into TDE directly
            self.tde_table = TdeTable(table_data, **kwargs)
            self.tde_subtables = self.tde_table.subtables

            # adjust the CDE heading from TDE results
            self.heading = self.tde_table.title_row if self.tde_table.title_row is not None else []

        except (TDEError, TypeError) as e:
            log.error("TableDataExtractor error: {}".format(e))
            self.tde_subtables = []
            self.tde_table = None
            self.heading = None

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
                log.debug(parser)
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

        contextual_records = ModelList()
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
                        record = copy.deepcopy(record_i)
                        for field in sym_diff:
                            if not record_i.__getattribute__(field) and record_i.fields[field].contextual:
                                record.__setitem__(field, record_j.__getattribute__(field))
                                record_update = True
                                updated_records.append(i)
                                updated_records.append(j)
                    # update record_j until we have the full record
                    # this is for the case that the contextual elements are in record_i
                    if not record_update:
                        record = copy.deepcopy(record_j)
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
            #if i not in updated_records and record_i not in contextual_records:
                log.debug("Record outside i = {}: {}".format(i, record_i.serialize()))
                contextual_records.append(record_i)

        return contextual_records

    @property
    def records(self):
        table_records = []
        caption_records = self.caption.records
        if self.tde_subtables:
            for subtable in self.tde_subtables:
                table_records.extend(self._records_for_tde_table(subtable, caption_records))
        elif not self.tde_subtables:
            table_records.extend(self._records_for_tde_table(self.tde_table, caption_records))
        return table_records

    def _category_tables(self, table):
        """
        Yields the category table and row category tables for a given TableDataExtractor table.
        :param table:
        :type table: TableDataExtractor.Table
        :return: list of category tables (python lists)
        """
        yield table.category_table
        while table.row_categories is not None:
            yield table.row_categories.category_table
            table = table.row_categories

    def _merge_nested_models(self, records):
        """
        Merges nested records based on models.

        Algorithm:

            1. for every record, check if the corresponding model has a 'ModelType' field
            2. if yes, and the field is empty, loop through all the records and associate the record that has:
              a) the same name as the 'ModelType' field,
              b) the same shared element, for example 'compound',
                 to the outer record field. Don't copy the records, but just use referencing. In that way many-level
                 nested models are supported automatically

        :param records: All the individual model records that have been found beforehand
        :return: updated records, where nested models are merged
        """

        #: field based on which merging is done
        shared_element = 'compound'

        # updated record list
        updated = ModelList()

        # a record that is on this list has already been merged into a bigger one and cannot be merged again
        # for each outer model type there is a list of merged records that have already been included in
        # that particular model type
        merged_records = dict()
        for record in records:
            model_name = record.__class__.__name__
            merged_records[model_name] = []

        for i, record_i in enumerate(records):
            for field in record_i.fields:
                if isinstance(record_i.fields[field], ModelType):
                    submodel_name = record_i.fields[field].model_name
                    model_name = record_i.__class__.__name__

                    for j, record_j in enumerate(records):
                        if j not in merged_records[model_name] and \
                                record_i.__getattribute__(field) is None and \
                                record_j.__class__.__name__ == submodel_name and \
                                shared_element in record_i.fields and shared_element in record_j.fields and \
                                record_i.__getattribute__(shared_element) == record_j.__getattribute__(shared_element):

                            record_i.__setitem__(field, record_j)
                            merged_records[model_name].append(j)

            log.debug(u"{}: {}".format(i, record_i.serialize()))
            updated.append(record_i)
        log.debug(u"Merged nested models: {}".format(merged_records))

        # print(merged_records)
        # print("Merged records:")
        # for i, rec in enumerate(updated):
        #     print(i, rec.serialize())
        # print("\n===============================================================================================\n")

        return updated

    def _records_for_tde_table(self, table, caption_records=None):
        """
        :param table: Input TDE table for which we want to obtain the records
        :type table: TableDataExtractor.Table
        :param caption_records:
        :return:
        """

        # get the compounds from the caption
        if not caption_records:
            caption_records = ModelList()
        log.debug(caption_records.serialize())
        caption_compounds = []
        for record in caption_records:
            if isinstance(record, Compound):
                caption_compounds += [record]

        #: complete table records
        table_records = ModelList()
        #: complete single-model records - not merged with submodels
        single_model_records = ModelList()
        #: partial records for non-full models
        partial_table_records = ModelList()


        #print("Collecting partial records.")
        for model in self._streamlined_models:
            #print("model", model)

            for parser in model.parsers:
                #print("parser", parser)

                for category_table in self._category_tables(table):
                    #print("category_table", category_table)

                    for record in self._parse_table(parser, category_table):

                        # add caption compound if necessary, and append to record
                        if 'compound' in model.fields \
                                and not record.compound \
                                and caption_compounds \
                                and model.compound.contextual:
                            record.compound = caption_compounds[0]  # the first compound from the caption is used by default

                        #print(record.serialize())
                        partial_table_records.append(record)

        # the partial records are merged
        partial_table_records_merged = self._merge_partial_records(partial_table_records)

        # print("\n")
        # for record in partial_table_records_merged:
        #     print(record.serialize())
        # print("\n")

        # a check is performed to see if all the 'required' elements of the merged table records are satisfied
        for model in self._streamlined_models:

            # print("MODEL: {}".format(model))
            # print(model.fields)

            for record in partial_table_records_merged:
                requirements = True

                # check if all required elements are present, do not check for requirement if the field is
                # of 'ModelType', this will be checked later, after merging of nested models
                unmet_requirements = []
                for field in model.fields:
                    if not isinstance(model.fields[field], ModelType) and \
                            model.fields[field].required and \
                            not record.__getattribute__(field):
                        unmet_requirements.append(field)
                        requirements = False

                # check if record is of the correct class
                if record.__class__.__name__ != model.__name__:
                    requirements = False

                # check if unknown elements from a different model are present
                for field in record.fields:
                    if field not in model.fields:
                        requirements = False

                if requirements:
                    #print(record.serialize())
                    single_model_records.append(record)

                # TODO This should be impossible considering that 'ModelType' fields are not taken into consideration
                # add the record if only the compound is missing
                elif not requirements and len(unmet_requirements) == 1 and unmet_requirements[0] == 'compound':
                    single_model_records.append(record)

        print("\n\n")

        # for rec in single_model_records:
        #     print(rec.serialize(), "\n")

        merged_model_records = self._merge_nested_models(single_model_records)

        # for rec in merged_model_records:
        #     print(rec.serialize())

        # TODO: Check if all the elements of the records have been satisfied

        for model in self.models:
            for record in merged_model_records:
                requirements = True
                unmet_requirements = []

                # check if record is of the correct class
                if record.__class__.__name__ != model.__name__:
                    requirements = False

                # check if all required fields are present
                for field in model.fields:
                    if model.fields[field].required and field in record.fields and not record.__getattribute__(field):
                        unmet_requirements.append(field)
                        requirements = False

                # TODO If it is a field check deeper, recursively, for as long as the field is required
                # TODO Check if this has already been done? Why don't we have records with the current run?
                    

                # check if unknown fields from a different model are present
                for field in record.fields:
                    if field not in model.fields:
                        requirements = False

                # finally, append to table records if the requirements have been met
                if requirements:
                    table_records.append(record)

                # also append to table records if all elements but the compound have been met
                elif not requirements and len(unmet_requirements) == 1 and unmet_requirements[0] == 'compound':
                    table_records.append(record)



        # Addition of the caption records
        caption_records = [c for c in caption_records if c.contextual_fulfilled]
        table_records += caption_records

        # Merge Compound records with any shared name/label
        # TODO: Copy/pasted from document.py, probably should be moved out somewhere
        len_l = len(table_records)
        log.debug(table_records)
        i = 0
        while i < (len_l - 1):
            for j in range(i + 1, len_l):
                r = table_records[i]
                other_r = table_records[j]
                if isinstance(r, Compound) and isinstance(other_r, Compound):
                    # Strip whitespace and lowercase to compare names
                    rnames_std = {''.join(n.split()).lower() for n in r.names}
                    onames_std = {''.join(n.split()).lower() for n in other_r.names}

                    # Clashing labels, don't merge
                    if len(set(r.labels) - set(other_r.labels)) > 0 and len(set(other_r.labels) - set(r.labels)) > 0:
                        continue

                    if any(n in rnames_std for n in onames_std) or any(l in r.labels for l in other_r.labels):
                        table_records.pop(j)
                        table_records.pop(i)
                        table_records.append(r.merge(other_r))
                        len_l -= 1
                        i -= 1
                        break
            i += 1

        return table_records



