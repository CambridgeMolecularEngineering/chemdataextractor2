# -*- coding: utf-8 -*-
"""
Document elements.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import ABCMeta, abstractproperty
import json
import operator

import six

from ..utils import python_2_unicode_compatible
import logging
log = logging.getLogger(__name__)


@python_2_unicode_compatible
class BaseElement(six.with_metaclass(ABCMeta)):
    """
    Abstract base class for a Document Element.

    :ivar id: (Optional) An identifier for this Element.
    :type id: Any or None
    :ivar list[chemdataextractor.models.BaseModel] models: A list of models that this element will parse
    """

    def __init__(self, document=None, references=None, id=None, models=None, **kwargs):
        """
        .. note::

            If intended as part of a :class:`~chemdataextractor.doc.document.Document`,
            an element should either be initialized with a reference to its containing document,
            or its :attr:`document` attribute should be set as soon as possible.
            If the element is being passed in to a :class:`~chemdataextractor.doc.document.Document`
            to initialise it, the :attr:`document` attribute is automatically set
            during the initialisation of the document, so the user does not need to worry about this.

        :param Document document: (Optional) The document containing this element.
        :param list[Citation] references: (Optional) Any references contained in the element.
        :param Any id: (Optional) An identifier for this element. Must be equatable.
        :param list[chemdataextractor.models.BaseModel] models: (Optional) A list of models for this element to parse.
            If the element is part of another element (e.g. a :class:`~chemdataextractor.doc.text.Sentence`
            inside a :class:`~chemdataextractor.doc.text.Paragraph`), or is part of a :class:`chemdataextractor.doc.document.Document`,
            this is set automatically to be the same as that of the containing element, unless manually set otherwise.
        """
        #: The containing Document
        self._document = document
        self.id = id
        self.references = references if references is not None else []
        if models:
            self.models = models
        else:
            self.models = []
        self._streamlined_models_list = None

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__,)

    def __str__(self):
        return '<%s>' % (self.__class__.__name__,)

    @property
    def document(self):
        """ The :class:`chemdataextractor.doc.document.Document` that this element belongs to. """
        return self._document

    @document.setter
    def document(self, document):
        # Subclasses may need to override this and also assign the document to sub-elements
        self._document = document
        # If we have problems with garbage collection, use a weakref to document to avoid circular references:
        # try:
        #     self._document = weakref.proxy(document)
        # except TypeError:
        #     self._document = document

    @abstractproperty
    def records(self):
        """All records found in this Element, as a :class:`chemdataextractor.model.base.ModelList` of :class:`chemdataextractor.model.base.BaseModel`."""
        return []

    # @abstractmethod  # TODO: Put this back?
    # def serialize(self):
    #     """Convert Element to python dictionary."""
    #     return []

    def add_models(self, models):
        """Set all models on this element
        """
        # print(models)
        log.debug("Setting models on %s" % self)
        self._streamlined_models_list = None
        self.models.extend(models)
        self.models = self.models

    @property
    def models(self):
        return self._models

    @models.setter
    def models(self, value):
        self._models = value
        self._streamlined_models_list = None

    @property
    def _streamlined_models(self):
        if self._streamlined_models_list is None:
            models = set()
            log.debug(self.models)
            for model in self.models:
                models.update(model.flatten(include_inferred=False))
            self._streamlined_models_list = sorted(list(models),
                                                   key=operator.attrgetter('__name__'))
        for model in self._streamlined_models_list:
            for parser in model.parsers:
                parser.model = model
        return self._streamlined_models_list

    def to_json(self, *args, **kwargs):
        """Convert element to JSON string. The content of the JSON will be equivalent
        to that of :meth:`serialize`."""
        return json.dumps(self.serialize(), *args, **kwargs)

    @property
    def elements(self):
        """
        A list of child elements. Returns None by default.
        """
        return None


@python_2_unicode_compatible
class CaptionedElement(BaseElement):
    """
    Document Element with a caption.

    :ivar BaseElement caption: The caption for this element.
    """

    def __init__(self, caption, label=None, **kwargs):
        """
        .. note::

            If intended as part of a :class:`~chemdataextractor.doc.document.Document`,
            an element should either be initialized with a reference to its containing document,
            or its :attr:`document` attribute should be set as soon as possible.
            If the element is being passed in to a :class:`~chemdataextractor.doc.document.Document`
            to initialise it, the :attr:`document` attribute is automatically set
            during the initialisation of the document, so the user does not need to worry about this.

        :param BaseElement caption: The caption for the element.
        :param Document document: (Optional) The document containing this element.
        :param str label: (Optional) The label for the captioned element, e.g. Table 1 would have a label of 1.
        :param Any id: (Optional) Some identifier for this element. Must be equatable.
        :param list[chemdataextractor.models.BaseModel] models: (Optional) A list of models for this element to parse.
            If the element is part of another element (e.g. a :class:`~chemdataextractor.doc.text.Sentence`
            inside a :class:`~chemdataextractor.doc.text.Paragraph`), or is part of a :class:`~chemdataextractor.doc.document.Document`,
            this is set automatically to be the same as that of the containing element, unless manually set otherwise.
        """
        # TODO: docs for label
        self.caption = caption
        self.label = label
        super(CaptionedElement, self).__init__(**kwargs)
        self.caption.document = self.document

    def __repr__(self):
        return '%s(id=%r, references=%r, caption=%r)' % (self.__class__.__name__, self.id, self.references, self.caption.text)

    def __str__(self):
        return self.caption.text

    @property
    def document(self):
        """ The :class:`~chemdataextractor.doc.document.Document` that this element belongs to. """
        return self._document

    @document.setter
    def document(self, document):
        self._document = document
        self.caption.document = document

    @property
    def records(self):
        """All records found in the object, as a list of :class:`~chemdataextractor.model.base.BaseModel`."""
        # This just passes the caption records. Subclasses may wish to extend this.
        return self.caption.records

    @property
    def abbreviation_definitions(self):
        """
        A list of all abbreviation definitions in this Document. Each abbreviation is in the form
        (:class:`str` abbreviation, :class:`str` long form of abbreviation, :class:`str` ner_tag)
        """
        return self.caption.abbreviation_definitions

    @property
    def ner_tags(self):
        """
        A list of all Named Entity Recognition tags in the caption for this element.
        If a word was found not to be a named entity, the named entity tag is None,
        and if it was found to be a named entity, it can have either a tag of 'B-CM' for a beginning of a
        mention of a chemical or 'I-CM' for the continuation of a mention.
        """
        # TODO: Delete this method?
        return self.caption.ner_tags

    @property
    def cems(self):
        """
        A list of all Chemical Entity Mentions in this document as :class:`~chemdataextractor.doc.text.Span`
        """
        return self.caption.cems

    @property
    def definitions(self):
        """Return a list of all specifier definitions in the caption

        Returns:
            list-- The specifier definitions
        """

        return self.caption.definitions

    @property
    def chemical_definitions(self):
        return self.caption.chemical_definitions

    @property
    def models(self):
        return self._models

    @models.setter
    def models(self, value):
        self._models = value
        self.caption.models = value

    def serialize(self):
        """
        Convert self to a dictionary. The key 'type' will contain
        the name of the class being serialized, and the key 'caption' will contain
        a serialized representation of :attr:`caption`, which is a :class:`~chemdataextractor.doc.element.BaseElement`
        """
        data = {'type': self.__class__.__name__, 'caption': self.caption.serialize()}
        return data

    @property
    def elements(self):
        return [self.caption]
