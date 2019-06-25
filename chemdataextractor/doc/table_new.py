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
from tabledataextractor import TrivialTable as TrivialTdeTable
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

        if self.tde_table is not None:
            # get the subtables
            self.tde_subtables = self.tde_table.subtables
            # adjust the CDE Table heading from TDE results
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

    def _parse_table(self, parser, category_table):
        """
        Parses a table. The model and the category table have to be provided.

        :param parser: parser to use for parsing of one row of the category table
        :param category_table: list, output of TableDataExtractor
        :return: Yields one result at a time
        """
        for cell in category_table:
            if hasattr(parser, 'parse_cell'):
                log.debug(parser)
                cde_cell = Cell(cell[0] + ' ' + ' '.join(cell[1]) + ' ' + ' '.join(cell[2]), models=self.models)
                results = parser.parse_cell(cde_cell)
                for result in results:
                    # [print(res) for res in result]
                    if result.serialize() != {}:
                        # yield {parser.model.__name__: result.serialize()}
                        yield result

    def _merge_partial_records(self, partial_table_records):
        """
        Merges partial records found in different rows of the table, based on the 'contextual' flags.
        A 'shared_element' is defined below based on which the merging will be performed.
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
                            if hasattr(record_i, field) and not  record_i.__getattribute__(field) and record_i.fields[field].contextual:
                                record.__setitem__(field, record_j.__getattribute__(field))
                                record_update = True
                                updated_records.append(i)
                                updated_records.append(j)
                    # update record_j until we have the full record
                    # this is for the case that the contextual elements are in record_i
                    if not record_update:
                        record = copy.deepcopy(record_j)
                        for field in sym_diff:
                            if hasattr(record_j, field) and not record_j.__getattribute__(field) and record_j.fields[field].contextual:
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
        table_records = []
        caption_records = self.caption.records
        if self.tde_subtables:
            for subtable in self.tde_subtables:
                table_records.extend(self._records_for_tde_table(subtable, caption_records))
        elif not self.tde_subtables and self.tde_table is not None:
            table_records.extend(self._records_for_tde_table(self.tde_table, caption_records))
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

        :param records: All individual model records that have been found beforehand
        :return: updated records, where nested models are merged into their parents
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

        return updated

    def _delete_unmet_nested_models(self, record):
        """
        Deletes nested records from a record if the requirements of its submodel have not been met.
        For example:
            A (requires B) >
            B (doesn't require C) >
            C (requires D) >
            D
         If D is not present, C will be deleted from the model. This has to be done at this stage, after merging
         of the nested records, because if, alternatively, only full models were used for merging, none of the models
         would be merged, as they are all 'required_fulfilled = False' before merging.

        :param record: Record to be processed
        """

        for field in record.fields:
            if isinstance(record.fields[field], ModelType) and not record.fields[field].required:

                    subrecord = record.__getattribute__(field)
                    if subrecord is None:
                        continue

                    for subfield in subrecord.fields:
                        if isinstance(subrecord.fields[subfield], ModelType):

                            if subrecord.__getattribute__(subfield) is not None:
                                if not subrecord.__getattribute__(subfield).required_fulfilled:
                                    log.debug("Deletion, position 1, field: {}".format(field))
                                    log.debug("Before deletion: {}".format(record.serialize()))
                                    record.__delattr__(field)
                                    log.debug("After deletion: {}".format(record.serialize()))
                                elif subrecord.__getattribute__(subfield).required_fulfilled:
                                    self._delete_unmet_nested_models(subrecord)

                            elif subrecord.__getattribute__(subfield) is None and subrecord.fields[subfield].required:
                                log.debug("Deletion, position 2, field: {}".format(field))
                                log.debug("Before deletion: {}".format(record.serialize()))
                                record.__delattr__(field)
                                log.debug("After deletion: {}".format(record.serialize()))

            elif isinstance(record.fields[field], ModelType) and record.fields[field].required:
                subrecord = record.__getattribute__(field)
                if subrecord is not None:
                    self._delete_unmet_nested_models(subrecord)

    def _fill_compound(self, records):
        """
        Compound in-table interdependency resolution.

        Fills all records that have been/will be extracted without a'compound', with the compound of the first previous
        model, if the compound was found before. Will only fill each model type once, to preserve order.

        :param records: records to work on
        :return: resolved reco
        """

        temp_comp = None
        filled_models = []

        for i, record_i in enumerate(records):
            if 'compound' in record_i.fields and record_i.compound:
                print(filled_models)
                print(record_i.serialize())
                temp_comp = record_i.compound
                filled_models = []
            else:
                continue

            for j, record_j in enumerate(records):
                if 'compound' in record_j.fields and not record_j.compound and \
                        record_j.fields['compound'].contextual and \
                        record_j.__class__.__name__ not in filled_models:
                    print("     ", record_j.serialize())
                    record_j.compound = temp_comp
                    filled_models.append(record_j.__class__.__name__)

    def _records_for_tde_table(self, table, caption_records=None):
        """
        Returns the records for a particular TableDataExtractor Table object.

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

        # 1. COLLECTING OF PARTIAL SINGLE-MODEL RECORDS
        for model in self._streamlined_models:
            for parser in model.parsers:
                for category_table in self._category_tables(table):
                    for record in self._parse_table(parser, category_table):
                        partial_table_records.append(record)

        # merging-in the 'compound' from the caption
        for model in self._streamlined_models:
            for record in partial_table_records:
                # add caption compound if necessary, and append to record
                if 'compound' in model.fields \
                        and not record.compound \
                        and caption_compounds \
                        and model.compound.contextual:
                    # the first compound from the caption is used by default
                    record.compound = caption_compounds[0]

        print("AFTER 1")
        for r in partial_table_records:
            print(r.serialize())

        # 2. MERGING OF PARTIAL SINGLE-MODEL TABLE RECORDS
        partial_table_records_merged = self._merge_partial_records(partial_table_records)

        # print("AFTER 2")
        # for r in partial_table_records_merged:
        #     print(r.serialize())

        # 3. CHECK IF ALL THE SINGLE-MODEL REQUIREMENTS (EXCEPT FOR NESTED SUBMODELS) ARE SATISFIED
        for model in self._streamlined_models:
            for record in partial_table_records_merged:
                requirements = True

                # check if all required elements are present, do not check for requirement if the field is
                # of 'ModelType', this will be checked later, after merging of nested models
                unmet_requirements = []
                for field in model.fields:
                    if not isinstance(model.fields[field], ModelType) and model.fields[field].required and hasattr(record, field) and not record.__getattribute__(field):
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
                    single_model_records.append(record)

        # print("AFTER 3")
        # for r in single_model_records:
        #     print(r.serialize())

        # 3b merging-in the 'compound' from a different model (compound in-table interdependency resolution)
        self._fill_compound(single_model_records)

        # 4. MERGE ALL SINGLE-MODEL RECORDS BASED ON THE HIERARCHY OF SUBMODELS
        merged_model_records = self._merge_nested_models(single_model_records)

        # print("AFTER 4")
        # for r in merged_model_records:
        #     print(r.serialize())

        # 5. CHECK IF ALL THE ELEMENTS OF THE FINAL RECORDS HAVE BEEN SATISFIED
        for model in self.models:
            for record in merged_model_records:

                # check if record is of the correct class
                if record.__class__.__name__ != model.__name__:
                    continue

                requirements = True
                duplicate = False
                unmet_requirements = []

                # manual check, only for the main (outermost) record, to catch the situation if only the
                # 'compound' is missing
                for field in model.fields:
                    if model.fields[field].required and not record.__getattribute__(field):
                        unmet_requirements.append(field)
                        requirements = False

                # using the model built-in check, this will check nested models properly
                if not record.required_fulfilled:
                    requirements = False

                # delete nested models that are not required but have required submodels that are not found
                # see the docstring of this function for further explanations
                self._delete_unmet_nested_models(record)

                # check if unknown fields from a different model are present
                for field in record.fields:
                    if field not in model.fields:
                        requirements = False

                # check if record is subset of another record already found in table_records
                for rec in table_records:
                    if record.is_subset(rec):
                        requirements = False
                        duplicate = True

                # finally, append to table records if the requirements have been met
                if requirements:
                    table_records.append(record)

                # also append to table records if all elements but the compound have been met
                elif not requirements and not duplicate \
                        and len(unmet_requirements) == 1 and unmet_requirements[0] == 'compound':
                    table_records.append(record)

        # 6. ADD RECORDS FOUND IN THE CAPTION
        caption_records = [c for c in caption_records if c.contextual_fulfilled]
        table_records += caption_records

        # print("AFTER 6")
        # for r in table_records:
        #     print(r.serialize())


        # 7. merge Compound records with any shared name/label
        len_l = len(table_records)
        log.debug(table_records)
        i = 0
        while i < (len_l - 1):
            for j in range(i + 1, len_l):

                r = table_records[i]
                other_r = table_records[j]
                r_compound, other_r_compound = None, None

                if hasattr(r, 'compound'):
                    r_compound = r.compound
                elif isinstance(r, Compound):
                    r_compound = r

                if hasattr(other_r, 'compound'):
                    other_r_compound = other_r.compound
                elif isinstance(other_r, Compound):
                    other_r_compound = other_r

                if not r_compound or not other_r_compound:
                    continue

                # Strip whitespace and lowercase to compare names
                rnames_std = {''.join(n.split()).lower() for n in r_compound.names}
                onames_std = {''.join(n.split()).lower() for n in other_r_compound.names}

                # Clashing labels, don't merge
                if len(set(r_compound.labels) - set(other_r_compound.labels)) > 0 and len(set(other_r_compound.labels) - set(r_compound.labels)) > 0:
                    continue

                if any(n in rnames_std for n in onames_std) or any(l in r_compound.labels for l in other_r_compound.labels):
                    # merging of 'Compound' records
                    # this is only good if both records are `Compound`, otherwise we can't just remove the records
                    if isinstance(r, Compound) and isinstance(other_r, Compound):
                        table_records.pop(j)
                        table_records.pop(i)
                        table_records.append(r)
                        len_l -= 1
                        i -= 1
                        break

                    # merging of 'compound' if the record is not of 'Compound' type
                    else:
                        new_c = r_compound.merge(other_r_compound)

                        if not isinstance(r, Compound):
                            r.compound = new_c
                        elif isinstance(r, Compound):
                            table_records.pop(i)
                            table_records.append(new_c)

                        if not isinstance(other_r, Compound):
                            other_r.compound = new_c
                        elif isinstance(other_r, Compound):
                            table_records.pop(j)
                            table_records.append(new_c)

                        break
            i += 1

        # print("AFTER 7")
        # for r in table_records:
        #     print(r.serialize())

        return table_records

