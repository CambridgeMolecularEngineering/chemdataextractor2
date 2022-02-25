# -*- coding: utf-8 -*-
"""
Document model.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from abc import ABCMeta, abstractproperty
from pprint import pprint
import collections
import io
import json
import logging
import copy

import six

from ..utils import python_2_unicode_compatible
from .text import Paragraph, Citation, Footnote, Heading, Title, Caption, RichToken
from .element import CaptionedElement
from .table import Table
from .figure import Figure
from .meta import MetaData
from ..errors import ReaderError
from ..model.base import ModelList
from ..model.model import Compound
from ..text import get_encoding
from ..config import Config
from ..parse.cem import chemical_name


log = logging.getLogger(__name__)


@python_2_unicode_compatible
class BaseDocument(six.with_metaclass(ABCMeta, collections.Sequence)):
    """Abstract base class for a Document."""

    def __repr__(self):
        return '<%s: %s elements>' % (self.__class__.__name__, len(self))

    def __str__(self):
        return '<%s: %s elements>' % (self.__class__.__name__, len(self))

    def __getitem__(self, index):
        return self.elements[index]

    def __len__(self):
        return len(self.elements)

    @abstractproperty
    def elements(self):
        """Return a list of document elements."""
        return []

    @abstractproperty
    def records(self):
        """Chemical records that have been parsed from this Document."""
        return []


class Document(BaseDocument):
    """A document to extract data from. Contains a list of document elements."""
    # TODO: Add a usage example here in the documentation.

    def __init__(self, *elements, **kwargs):
        """Initialize a Document manually by passing one or more Document elements (Paragraph, Heading, Table, etc.)

        Strings that are passed to this constructor are automatically wrapped into Paragraph elements.

        :param list[chemdataextractor.doc.element.BaseElement|string] elements: Elements in this Document.
        :keyword Config config: (Optional) Config file for the Document.
        :keyword list[BaseModel] models: (Optional) Models that the Document should extract data for.
        """
        self._elements = []
        for element in elements:
            # Convert raw text to Paragraph elements
            if isinstance(element, six.text_type):
                element = Paragraph(element)
            elif isinstance(element, six.binary_type):
                # Try guess encoding if byte string
                encoding = get_encoding(element)
                log.warning('Guessed bytestring encoding as %s. Use unicode strings to avoid this warning.', encoding)
                element = Paragraph(element.decode(encoding))
            element.document = self
            self._elements.append(element)
        if 'config' in kwargs.keys():
            self.config = kwargs['config']
        else:
            self.config = Config()
        if 'models' in kwargs.keys():
            self.models = kwargs['models']
        else:
            self._models = []

        # Sets parameters from configuration file
        for element in elements:
            if callable(getattr(element, 'set_config', None)):
                element.set_config()
        log.debug('%s: Initializing with %s elements' % (self.__class__.__name__, len(self.elements)))

    def add_models(self, models):
        """
        Add models to all elements.

        Usage::

            d = Document.from_file(f)
            d.set_models([myModelClass1, myModelClass2,..])

        Arguments::
            models -- List of model classes

        """
        log.debug("Setting models")
        self._models.extend(models)
        for element in self.elements:
            if callable(getattr(element, 'add_models', None)):
                element.add_models(models)
            # print(element.models)
        return

    @property
    def models(self):
        return self._models

    @models.setter
    def models(self, value):
        self._models = value
        for element in self.elements:
            element.models = value

    @classmethod
    def from_file(cls, f, fname=None, readers=None):
        """Create a Document from a file.

        Usage::

            with open('paper.html', 'rb') as f:
                doc = Document.from_file(f)

        .. note::

            Always open files in binary mode by using the 'rb' parameter.

        :param f: A file-like object or path to a file.
        :type f: file or str
        :param str fname: (Optional) The filename. Used to help determine file format.
        :param list[chemdataextractor.reader.base.BaseReader] readers: (Optional) List of readers to use. If not set, Document will try all default readers,
            which are :class:`~chemdataextractor.reader.acs.AcsHtmlReader`, :class:`~chemdataextractor.reader.rsc.RscHtmlReader`,
            :class:`~chemdataextractor.reader.nlm.NlmXmlReader`, :class:`~chemdataextractor.reader.uspto.UsptoXmlReader`,
            :class:`~chemdataextractor.reader.cssp.CsspHtmlReader`, :class:`~chemdataextractor.elsevier.ElsevierXmlReader`,
            :class:`~chemdataextractor.reader.markup.XmlReader`, :class:`~chemdataextractor.reader.markup.HtmlReader`,
            :class:`~chemdataextractor.reader.pdf.PdfReader`, and :class:`~chemdataextractor.reader.plaintext.PlainTextReader`.
        """
        if isinstance(f, six.string_types):
            f = io.open(f, 'rb')
        if not fname and hasattr(f, 'name'):
            fname = f.name
        return cls.from_string(f.read(), fname=fname, readers=readers)

    @classmethod
    def from_string(cls, fstring, fname=None, readers=None):
        """Create a Document from a byte string containing the contents of a file.

        Usage::

            contents = open('paper.html', 'rb').read()
            doc = Document.from_string(contents)

        .. note::

            This method expects a byte string, not a unicode string (in contrast to most methods in ChemDataExtractor).

        :param bytes fstring: A byte string containing the contents of a file.
        :param str fname: (Optional) The filename. Used to help determine file format.
        :param list[chemdataextractor.reader.base.BaseReader] readers: (Optional) List of readers to use. If not set, Document will try all default readers,
            which are :class:`~chemdataextractor.reader.acs.AcsHtmlReader`, :class:`~chemdataextractor.reader.rsc.RscHtmlReader`,
            :class:`~chemdataextractor.reader.nlm.NlmXmlReader`, :class:`~chemdataextractor.reader.uspto.UsptoXmlReader`,
            :class:`~chemdataextractor.reader.cssp.CsspHtmlReader`, :class:`~chemdataextractor.elsevier.ElsevierXmlReader`,
            :class:`~chemdataextractor.reader.markup.XmlReader`, :class:`~chemdataextractor.reader.markup.HtmlReader`,
            :class:`~chemdataextractor.reader.pdf.PdfReader`, and :class:`~chemdataextractor.reader.plaintext.PlainTextReader`.
        """
        if readers is None:
            from ..reader import DEFAULT_READERS
            readers = DEFAULT_READERS

        if isinstance(fstring, six.text_type):
            raise ReaderError('from_string expects a byte string, not a unicode string')

        for reader in readers:
            # Skip reader if we don't think it can read file
            if not reader.detect(fstring, fname=fname):
                continue
            try:
                d = reader.readstring(fstring)
                log.debug('Parsed document with %s' % reader.__class__.__name__)
                return d
            except ReaderError:
                pass
        raise ReaderError('Unable to read document')

    @property
    def elements(self):
        """
        A list of all the elements in this document. All elements subclass from :class:`~chemdataextractor.doc.element.BaseElement`,
        and represent things such as paragraphs or tables, and can be found in :mod:`chemdataextractor.doc.figure`,
        :mod:`chemdataextractor.doc.table`, and :mod:`chemdataextractor.doc.text`.
        """
        return self._elements

    # TODO: memoized_property?
    @property
    def records(self):
        """
        All records found in this Document, as a list of :class:`~chemdataextractor.model.base.BaseModel`.
        """
        log.debug("Getting chemical records")
        records = ModelList()  # Final list of records -- output
        head_def_record = None  # Most recent record from a heading, title or short paragraph
        head_def_record_i = None # Element index of head_def_record
        last_product_record = None
        title_record = None # Records found in the title

        # Main loop, over all elements in the document
        for i, el in enumerate(self.elements):
            log.debug("Element %d, type %s" %(i, str(type(el))))
            last_id_record = None

            # FORWARD INTERDEPENDENCY RESOLUTION -- Updated model parsers to reflect defined entities
            # 1. Find any defined entities in the element e.g. "Curie Temperature, Tc"
            # 2. Update the relevant models
            element_definitions = el.definitions
            chemical_defs = el.chemical_definitions

            for model in el._streamlined_models:
                if hasattr(model, 'is_id_only'):
                    model.update(chemical_defs)
                else:
                    model.update(element_definitions)

            el_records = el.records
            # Save the title compound
            if isinstance(el, Title):
                if len(el_records) == 1 and isinstance(el_records[0], Compound) and el_records[0].is_id_only:
                    title_record = el_records[0]  # TODO: why the first only?

            # Reset head_def_record unless consecutive heading with no records
            if isinstance(el, Heading) and head_def_record is not None:
                if not (i == head_def_record_i + 1 and len(el.records) == 0):
                    head_def_record = None
                    head_def_record_i = None

            # Paragraph with single sentence with single ID record considered a head_def_record
            if isinstance(el, Paragraph) and len(el.sentences) == 1:
                if len(el_records) == 1 and isinstance(el_records[0], Compound) and el_records[0].is_id_only:
                    head_def_record = el_records[0]
                    head_def_record_i = i

            # Paragraph with multiple sentences
            # We assume that if the first sentence of a paragraph contains only 1 ID Record, we can treat it as a header definition record, unless directly proceeding a header def record
            elif isinstance(el, Paragraph) and len(el.sentences) > 0:
                if not (isinstance(self.elements[i - 1], Heading) and head_def_record_i == i - 1):
                    first_sent_records = el.sentences[0].records
                    if len(first_sent_records) == 1 and isinstance(first_sent_records[0], Compound) and first_sent_records[0].is_id_only:
                        sent_record = first_sent_records[0]
                        if sent_record.names:
                           longest_name = sorted(sent_record.names, key=len)[0]
                        if sent_record.labels or (sent_record.names and len(longest_name) > len(el.sentences[0].text) / 2):  # TODO: Why do the length check? Maybe to make sure that the sentence mostly refers to a compound?
                            head_def_record = sent_record
                            head_def_record_i = i

            #: BACKWARD INTERDEPENDENCY RESOLUTION BEGINS HERE
            for record in el_records:
                if isinstance(record, MetaData):
                    continue
                if isinstance(record, Compound):
                    # Keep track of the most recent compound record with labels
                    if isinstance(el, Paragraph) and record.labels:
                        last_id_record = record
                    # # Keep track of the most recent compound 'product' record
                    if record.roles and 'product' in record.roles:
                        last_product_record = record

                    # Heading records with compound ID's
                    if isinstance(el, Heading) and (record.labels or record.names):
                        head_def_record = record
                        head_def_record_i = i
                        # If 2 consecutive headings with compound ID, merge in from previous
                        if i > 0 and isinstance(self.elements[i - 1], Heading):
                            prev = self.elements[i - 1]
                            if (len(el.records) == 1 and record.is_id_only and len(prev.records) == 1 and
                                isinstance(prev.records[0], Compound) and prev.records[0].is_id_only and not (record.labels and prev.records[0].labels) and
                                    not (record.names and prev.records[0].names)):
                                record.names.update(prev.records[0].names)
                                record.labels.update(prev.records[0].labels)
                                record.roles.update(prev.records[0].roles)

                # Unidentified records -- those without compound names or labels
                if record.is_unidentified:
                    if hasattr(record, 'compound'):
                        # We have property values but no names or labels... try merge those from previous records
                        if isinstance(el, Paragraph) and (head_def_record or last_product_record or last_id_record or title_record):
                            # head_def_record from heading takes priority if the heading directly precedes the paragraph ( NOPE: or the last_id_record has no name)
                            if head_def_record_i and head_def_record_i + 1 == i: # or (last_id_record and not last_id_record.names)):
                                if head_def_record:
                                    record.compound = head_def_record
                                elif last_id_record:
                                    record.compound = last_id_record
                                elif last_product_record:
                                    record.compound = last_product_record
                                elif title_record:
                                    record.compound = title_record
                            else:
                                if last_id_record:
                                    record.compound = last_id_record
                                elif head_def_record:
                                    record.compound = head_def_record
                                elif last_product_record:
                                    record.compound = last_product_record
                                elif title_record:
                                    record.compound = title_record
                        else:
                            # Consider continue here to filter records missing name/label...
                            pass
                if record not in records:
                    log.debug(record.serialize())
                    records.append(record)

        # for record in records:
        #     for contextual_record in contextual_records:
        #         # record.merge_contextual(contextual_record)
        #         contextual_record.merge_contextual(record)
        #         if not contextual_record.is_contextual:
        #             print("No longer contextual:", contextual_record)
        #             records.append(contextual_record)
        #             contextual_records.remove(contextual_record)
        #     log.debug(records.serialize())

        # Merge abbreviation definitions
        for record in records:
            compound = None
            if hasattr(record, 'compound'):
                compound = record.compound
            elif isinstance(record, Compound):
                compound = record
            if compound is not None:
                for short, long_, entity in self.abbreviation_definitions:
                    if entity == 'CM':
                        name = ' '.join(long_)
                        abbrev = ' '.join(short)
                        if compound.names:
                            if name in compound.names and abbrev not in compound.names:
                                compound.names.add(abbrev)
                            if abbrev in compound.names and name not in compound.names:
                                compound.names.add(name)

        # Merge Compound records with any shared name/label
        len_l = len(records)
        log.debug(records)
        i = 0
        while i < (len_l - 1):
            j = i + 1
            while j < len_l:
                r = records[i]
                other_r = records[j]
                r_compound = None
                if isinstance(r, Compound):
                    r_compound = r
                elif hasattr(r, 'compound') and isinstance(r.compound, Compound):
                    r_compound = r.compound
                other_r_compound = None
                if isinstance(other_r, Compound):
                    other_r_compound = other_r
                elif hasattr(other_r, 'compound') and isinstance(other_r.compound, Compound):
                    other_r_compound = other_r.compound
                if r_compound and other_r_compound:
                    # Strip whitespace and lowercase to compare names
                    r_names = r_compound.names
                    if r_names is None:
                        r_names = []

                    other_r_names = other_r_compound.names
                    if other_r_names is None:
                        other_r_names = []

                    rnames_std = {''.join(n.split()).lower() for n in r_names}
                    onames_std = {''.join(n.split()).lower() for n in other_r_names}

                    # Clashing labels, don't merge
                    if (r_compound.labels is not None and
                        other_r_compound.labels is not None and
                        len(r_compound.labels - other_r_compound.labels) > 0 and len(other_r_compound.labels - r_compound.labels) > 0):
                        j += 1
                        continue

                    if (r_compound.labels is not None and
                        other_r_compound.labels is not None and
                        rnames_std is not None and
                        onames_std is not None and
                        (any(n in rnames_std for n in onames_std) or any(l in r_compound.labels for l in other_r_compound.labels))):
                        r_compound.merge(other_r_compound)
                        other_r_compound.merge(r_compound)
                        if isinstance(r, Compound) and isinstance(other_r, Compound):
                            records.pop(j)
                            records.pop(i)
                            records.append(r_compound)
                            len_l -= 1
                            i -= 1
                        break
                j += 1
            i += 1

        i = 0
        length = len(records)
        while i < length:
            j = 0
            while j < length:
                if i != j:
                    records[j].merge_contextual(records[i])
                j += 1
            i += 1

        # print("\n\n\nAFTER:")
        # pprint(records.serialize())

        # clean up records
        cleaned_records = ModelList()
        for record in records:
            if (self.models and type(record) in self.models) or not self.models:
                record._clean()
                # print("\nCLEANEDRECORD:", record.required_fulfilled, record not in cleaned_records)
                # pprint(record.serialize())
                if record.required_fulfilled and record not in cleaned_records:
                        cleaned_records.append(record)

        cleaned_records.remove_subsets()

        # Reset updatables
        for el in self.elements:
            for model in el._streamlined_models:
                model.reset_updatables()

        # Append contextual records if they've filled required fields
        # for record in contextual_records:
        #     if record.required_fulfilled:
        #         records.append(record)

        return cleaned_records

    def get_element_with_id(self, id):
        """
        Get element with the specified ID. If one is not found, None is returned.

        :param id: Identifier to search for.
        :returns: Element with specified ID
        :rtype: BaseElement or None
        """
        """Return the element with the specified ID."""
        # Should we maintain a hashmap of ids to make this more efficient? Probably overkill.
        # TODO: Elements can contain nested elements (captions, footnotes, table cells, etc.)
        return next((el for el in self.elements if el.id == id), None)

    @property
    def figures(self):
        """
        A list of all :class:`~chemdataextractor.doc.figure.Figure` elements in this Document.
        """
        return [el for el in self.elements if isinstance(el, Figure)]

    @property
    def tables(self):
        """
        A list of all :class:`~chemdataextractor.doc.table.Table` elements in this Document.
        """
        return [el for el in self.elements if isinstance(el, Table)]

    @property
    def citations(self):
        """
        A list of all :class:`~chemdataextractor.doc.text.Citation` elements in this Document.
        """
        return [el for el in self.elements if isinstance(el, Citation)]

    @property
    def footnotes(self):
        """
        A list of all :class:`~chemdataextractor.doc.text.Footnote` elements in this Document.

        .. note::

            Elements (e.g. Tables) can contain nested Footnotes which are not taken into account.
        """
        # TODO: Elements (e.g. Tables) can contain nested Footnotes
        return [el for el in self.elements if isinstance(el, Footnote)]

    @property
    def titles(self):
        """
        A list of all :class:`~chemdataextractor.doc.text.Title` elements in this Document.
        """
        return [el for el in self.elements if isinstance(el, Title)]

    @property
    def headings(self):
        """
        A list of all :class:`~chemdataextractor.doc.text.Heading` elements in this Document.
        """
        return [el for el in self.elements if isinstance(el, Heading)]

    @property
    def paragraphs(self):
        """
        A list of all :class:`~chemdataextractor.doc.text.Paragraph` elements in this Document.
        """
        return [el for el in self.elements if isinstance(el, Paragraph)]

    @property
    def captions(self):
        """
        A list of all :class:`~chemdataextractor.doc.text.Caption` elements in this Document.
        """
        return [el for el in self.elements if isinstance(el, Caption)]

    @property
    def captioned_elements(self):
        """
        A list of all :class:`~chemdataextractor.doc.element.CaptionedElement` elements in this Document.
        """
        return [el for el in self.elements if isinstance(el, CaptionedElement)]

    @property
    def metadata(self):
        """Return metadata information
        """
        return [el for el in self.elements if isinstance(el, MetaData)][0]


    @property
    def abbreviation_definitions(self):
        """
        A list of all abbreviation definitions in this Document. Each abbreviation is in the form
        (:class:`str` abbreviation, :class:`str` long form of abbreviation, :class:`str` ner_tag)
        """
        return [ab for el in self.elements for ab in el.abbreviation_definitions]

    @property
    def ner_tags(self):
        """
        A list of all Named Entity Recognition tags in this Document.
        If a word was found not to be a named entity, the named entity tag is None,
        and if it was found to be a named entity, it can have either a tag of 'B-CM' for a beginning of a
        mention of a chemical or 'I-CM' for the continuation of a mention.
        """
        return [n for el in self.elements for n in el.ner_tags]

    @property
    def cems(self):
        """
        A list of all Chemical Entity Mentions in this document as :class:`~chemdataextractor.doc.text.Span`
        """
        return list(set([n for el in self.elements for n in el.cems]))

    @property
    def definitions(self):
        """
        Return a list of all recognised definitions within this Document
        """
        # TODO: What's the type of this?
        return list([defn for el in self.elements for defn in el.definitions])

    def serialize(self):
        """
        Convert Document to Python dictionary. The dictionary will always contain the key 'type', which will be 'document',
        and the key 'elements', which contains a dictionary representation of each of the elements of the document.
        """
        # Serialize fields to a dict
        elements = []
        for element in self.elements:
            elements.append(element.serialize())
        data = {'type': 'document', 'elements': elements}
        return data

    def to_json(self, *args, **kwargs):
        """Convert Document to JSON string. The content of the JSON will be equivalent
        to that of :meth:`serialize`.
        The document itself will be under the key 'elements',
        and there will also be the key 'type', which will always be 'document'.
        Any arguments for :func:`json.dumps` can be passed into this function."""
        return json.dumps(self.serialize(), *args, **kwargs)

    def _repr_html_(self):
        html_lines = ['<div class="cde-document">']
        for element in self.elements:
            html_lines.append(element._repr_html_())
        html_lines.append('</div>')
        return '\n'.join(html_lines)

    def _batch_assign_tags(self, tagger, tag_type):
        """
        Batch assign all the tags for a certain tag type.
        This is called by the :class:`Sentence` class when it encounters
        a token without tags of a given tag type, and the tagger for that
        tag type implements the `batch_tag` method.

        See :ref:`this guide<creating_taggers>` for more details.
        """
        elements = copy.copy(self.elements)

        all_tokens = []
        for element in elements:
            if element.elements is not None:
                elements.extend(element.elements)
            if hasattr(element, "tokens") and tagger in element.taggers:
                if len(element.tokens) and isinstance(element.tokens[0], RichToken) and tag_type not in element.tokens[0]._tags.keys():
                    all_tokens.append(element.tokens)

        if hasattr(tagger, "batch_tag_for_type"):
            tag_results = tagger.batch_tag_for_type(all_tokens, tag_type)
        else:
            tag_results = tagger.batch_tag(all_tokens)

        for tag_result in tag_results:
            for token, tag in tag_result:
                token._tags[tag_type] = tag


