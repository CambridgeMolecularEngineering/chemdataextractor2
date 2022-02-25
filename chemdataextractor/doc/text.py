# -*- coding: utf-8 -*-
"""
Text-based document elements.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractproperty
import collections
import logging
import re
from pprint import pprint
from deprecation import deprecated
import unicodedata

import six

from ..model.base import ModelList
from ..nlp.lexicon import ChemLexicon, Lexicon
from ..nlp.cem import IGNORE_PREFIX, IGNORE_SUFFIX, SPECIALS, SPLITS, CiDictCemTagger, CsDictCemTagger, CrfCemTagger
from ..nlp.new_cem import CemTagger
from ..nlp.abbrev import ChemAbbreviationDetector
from ..nlp.tag import NoneTagger, POS_TAG_TYPE, NER_TAG_TYPE
from ..nlp.pos import ChemCrfPosTagger, CrfPosTagger, ApPosTagger, ChemApPosTagger
# from ..nlp.tokenize import ChemSentenceTokenizer, ChemWordTokenizer, regex_span_tokenize, SentenceTokenizer, WordTokenizer, FineWordTokenizer, ChemTokWordTokenizer, SpacyTokenizer
from ..nlp.tokenize import BertWordTokenizer, ChemSentenceTokenizer, regex_span_tokenize, SentenceTokenizer, WordTokenizer
from ..text import CONTROL_RE
from ..utils import memoized_property, python_2_unicode_compatible, first
from .element import BaseElement
from ..parse.definitions import specifier_definition
from ..parse.cem import chemical_name, cem_phrase
from ..parse.quantity import construct_quantity_re
from ..model.model import Compound, NmrSpectrum, IrSpectrum, UvvisSpectrum, MeltingPoint, GlassTransition


log = logging.getLogger(__name__)
cem_tagger = CemTagger()


@python_2_unicode_compatible
class BaseText(BaseElement):
    """Abstract base class for a text Document Element."""
    taggers = []
    """
    A list of :class:`~chemdataextractor.nlp.tag.BaseTagger` instances. This is a list of taggers
    that will be called by ChemDataExtractor to assign tags to each of the tokens in this element.
    """

    def __init__(self, text, word_tokenizer=None, lexicon=None, abbreviation_detector=None, pos_tagger=None, ner_tagger=None, taggers=None, **kwargs):
        """
        .. note::

            If intended as part of a :class:`~chemdataextractor.doc.document.Document`,
            an element should either be initialized with a reference to its containing document,
            or its :attr:`document` attribute should be set as soon as possible.
            If the element is being passed in to a :class:`~chemdataextractor.doc.document.Document`
            to initialise it, the :attr:`document` attribute is automatically set
            during the initialisation of the document, so the user does not need to worry about this.

        :param str text: The text contained in this element.
        :param WordTokenizer word_tokenizer: (Optional) Word tokenizer for this element.
        :param Lexicon lexicon: (Optional) Lexicon for this element. The lexicon stores all the occurences of unique words and can provide
            Brown clusters for the words.
        :param AbbreviationDetector abbreviation_detector: (Optional) The abbreviation detector for this element.
        :param BaseTagger pos_tagger: (Optional) The part of speech tagger for this element.
        :param BaseTagger ner_tagger: (Optional) The named entity recognition tagger for this element.
        :param Document document: (Optional) The document containing this element.
        :param str label: (Optional) The label for the captioned element, e.g. Table 1 would have a label of 1.
        :param Any id: (Optional) Some identifier for this element. Must be equatable.
        :param list[chemdataextractor.models.BaseModel] models: (Optional) A list of models for this element to parse.
            If the element is part of another element (e.g. a :class:`~chemdataextractor.doc.text.Sentence`
            inside a :class:`~chemdataextractor.doc.text.Paragraph`), or is part of a :class:`~chemdataextractor.doc.document.Document`,
            this is set automatically to be the same as that of the containing element, unless manually set otherwise.
        """
        if not isinstance(text, six.text_type):
            raise TypeError('Text must be a unicode string')
        super(BaseText, self).__init__(**kwargs)
        self._text = text
        self.word_tokenizer = word_tokenizer if word_tokenizer is not None else self.word_tokenizer
        self.lexicon = lexicon if lexicon is not None else self.lexicon
        self.abbreviation_detector = abbreviation_detector if abbreviation_detector is not None else self.abbreviation_detector
        if taggers is not None and len(taggers) != 0:
            self.taggers = taggers

    def __repr__(self):
        return '%s(id=%r, references=%r, text=%r)' % (self.__class__.__name__, self.id, self.references, self._text)

    def __str__(self):
        return self._text

    @property
    def text(self):
        """The raw text :class:`str` for this passage of text."""
        return self._text

    @abstractproperty
    def word_tokenizer(self):
        """The :class:`~chemdataextractor.nlp.tokenize.WordTokenizer` used by this element."""
        return

    @abstractproperty
    def lexicon(self):
        """The :class:`~chemdataextractor.nlp.lexicon.Lexicon` used by this element."""
        return

    @property
    def pos_tagger(self):
        """The part of speech tagger used by this element. A subclass of :class:`~chemdataextractor.nlp.tag.BaseTagger`"""
        for tagger in reversed(self.taggers):
            if tagger.can_tag(POS_TAG_TYPE):
                return tagger

    @pos_tagger.setter
    @deprecated(deprecated_in="2.1", details="Deprecated due to the introduction of taggers API. Consult the migration guide for more information.")
    def pos_tagger(self, value):
        if not value.can_tag(POS_TAG_TYPE):
            value.tag_type = POS_TAG_TYPE
        self.taggers.append(value)

    @property
    def ner_tagger(self):
        """The named entity recognition tagger used by this element. A subclass of :class:`~chemdataextractor.nlp.tag.BaseTagger`"""
        for tagger in reversed(self.taggers):
            if tagger.can_tag(NER_TAG_TYPE):
                return tagger

    @ner_tagger.setter
    @deprecated(deprecated_in="2.1", details="Deprecated due to the introduction of taggers API. Consult the migration guide for more information.")
    def ner_tagger(self, value):
        if not value.can_tag(NER_TAG_TYPE):
            value.tag_type = NER_TAG_TYPE
        self.taggers.append(value)

    @abstractproperty
    def tokens(self):
        """A list of :class:`RichToken` s for this object."""
        return

    @abstractproperty
    def tags(self):
        """
        A list of tags corresponding to each of the tokens in the object.
        For information on what each of the tags can be, check the documentation on
        the specific :attr:`ner_tagger` and :attr:`pos_tagger` used for this class.
        """
        return

    @abstractproperty
    def definitions(self):
        """
        A list of all specifier definitions
        """
        return

    @abstractproperty
    def chemical_definitions(self):
        """A list of all chemical label definitiond
        """
        return

    def serialize(self):
        """
        Convert self to a dictionary. The key 'type' will contain
        the name of the class being serialized, and the key 'content' will contain
        a serialized representation of :attr:`text`, which is a :class:`str`
        """
        data = {'type': self.__class__.__name__, 'content': self.text}
        return data

    def _repr_html_(self):
        return self.text


class Text(collections.Sequence, BaseText):
    """A passage of text, comprising one or more sentences."""

    sentence_tokenizer = ChemSentenceTokenizer()
    word_tokenizer = BertWordTokenizer()
    lexicon = ChemLexicon()
    abbreviation_detector = ChemAbbreviationDetector()
    taggers = [ChemCrfPosTagger(), cem_tagger]

    def __init__(self, text, sentence_tokenizer=None, word_tokenizer=None, lexicon=None, abbreviation_detector=None, pos_tagger=None, ner_tagger=None, parsers=None, **kwargs):
        """
        .. note::

            If intended as part of a :class:`~chemdataextractor.doc.document.Document`,
            an element should either be initialized with a reference to its containing document,
            or its :attr:`document` attribute should be set as soon as possible.
            If the element is being passed in to a :class:`~chemdataextractor.doc.document.Document`
            to initialise it, the :attr:`document` attribute is automatically set
            during the initialisation of the document, so the user does not need to worry about this.

        :param str text: The text contained in this element.
        :param SentenceTokenizer sentence_tokenizer: (Optional) Sentence tokenizer for this element.
            Default :class:`~chemdataextractor.nlp.tokenize.ChemSentenceTokenizer`.
        :param WordTokenizer word_tokenizer: (Optional) Word tokenizer for this element.
            Default :class:`~chemdataextractor.nlp.tokenize.ChemWordTokenizer`.
        :param Lexicon lexicon: (Optional) Lexicon for this element. The lexicon stores all the occurences of unique words and can provide
            Brown clusters for the words. Default :class:`~chemdataextractor.nlp.lexicon.ChemLexicon`
        :param AbbreviationDetector abbreviation_detector: (Optional) The abbreviation detector for this element.
            Default :class:`~chemdataextractor.nlp.abbrev.ChemAbbreviationDetector`.
        :param BaseTagger pos_tagger: (Optional) The part of speech tagger for this element.
            Default :class:`~chemdataextractor.nlp.pos.ChemCrfPosTagger`.
        :param BaseTagger ner_tagger: (Optional) The named entity recognition tagger for this element.
            Default :class:`~chemdataextractor.nlp.cem.CemTagger`
        :param Document document: (Optional) The document containing this element.
        :param str label: (Optional) The label for the captioned element, e.g. Table 1 would have a label of 1.
        :param Any id: (Optional) Some identifier for this element. Must be equatable.
        :param list[chemdataextractor.models.BaseModel] models: (Optional) A list of models for this element to parse.
            If the element is part of another element (e.g. a :class:`~chemdataextractor.doc.text.Sentence`
            inside a :class:`~chemdataextractor.doc.text.Paragraph`), or is part of a :class:`~chemdataextractor.doc.document.Document`,
            this is set automatically to be the same as that of the containing element, unless manually set otherwise.
        """
        super(Text, self).__init__(text, word_tokenizer=word_tokenizer, lexicon=lexicon, abbreviation_detector=abbreviation_detector, pos_tagger=pos_tagger, ner_tagger=ner_tagger, parsers=None, **kwargs)
        self.sentence_tokenizer = sentence_tokenizer if sentence_tokenizer is not None else self.sentence_tokenizer

    def __getitem__(self, index):
        return self.sentences[index]

    def __len__(self):
        return len(self.sentences)

    def set_config(self):
        """ Load settings from configuration file

        .. note:: Called when Document instance is created
        """

        if self.document is None:
            pass
        else:
            c = self.document.config
            if 'SENTENCE_TOKENIZER' in c.keys():
                self.sentence_tokenizer = eval(c['SENTENCE_TOKENIZER'])()
            if 'WORD_TOKENIZER' in c.keys():
                self.word_tokenizer = eval(c['WORD_TOKENIZER'])()
            if 'POS_TAGGER' in c.keys():
                self.pos_tagger = eval(c['POS_TAGGER'])()
            if 'NER_TAGGER' in c.keys():
                self.ner_tagger = eval(c['NER_TAGGER'])()
            if 'LEXICON' in c.keys():
                self.lexicon = eval(c['LEXICON'])()
            if 'PARSERS' in c.keys():
                raise(DeprecationWarning('Manually setting parsers deprecated, any settings from config files for this will be ignored.'))

    @memoized_property
    def sentences(self):
        """A list of :class:`Sentence` s that make up this text passage."""
        sents = self.sentence_tokenizer.get_sentences(self)
        for sent in sents:
            sent.document = self.document
        return sents

    @property
    def elements(self):
        return self.sentences

    def _sentences_from_spans(self, spans):
        sents = []
        for span in spans:
            sent = Sentence(
                text=self.text[span[0]:span[1]],
                start=span[0],
                end=span[1],
                word_tokenizer=self.word_tokenizer,
                lexicon=self.lexicon,
                abbreviation_detector=self.abbreviation_detector,
                pos_tagger=self.pos_tagger,
                ner_tagger=self.ner_tagger,
                document=self.document,
                models=self.models,
                taggers=self.taggers
            )
            sents.append(sent)
        return sents

    @property
    def raw_sentences(self):
        """A list of :class:`str` for the sentences that make up this text passage."""
        return [sentence.text for sentence in self.sentences]

    @property
    def tokens(self):
        return [sent.tokens for sent in self.sentences]

    @property
    def raw_tokens(self):
        """A list of :class:`str` representations for the tokens of each sentence in this text passage."""
        return [sent.raw_tokens for sent in self.sentences]

    @property
    def pos_tagged_tokens(self):
        """A list of (:class:`Token` token, :class:`str` tag) tuples for each sentence in this text passage."""
        return [sent.pos_tagged_tokens for sent in self.sentences]

    @property
    def pos_tags(self):
        """A list of :class:`str` part of speech tags for each sentence in this text passage."""
        return [sent.pos_tags for sent in self.sentences]

    @property
    def unprocessed_ner_tagged_tokens(self):
        """
        A list of (:class:`Token` token, :class:`str` named entity recognition tag)
        from the text.

        No corrections from abbreviation detection are performed.
        """
        return [sent.unprocessed_ner_tagged_tokens for sent in self.sentences]

    @property
    def unprocessed_ner_tags(self):
        """
        A list of :class:`str` unprocessed named entity tags for the tokens in this sentence.

        No corrections from abbreviation detection are performed.
        """
        return [sent.unprocessed_ner_tags for sent in self.sentences]

    @property
    def ner_tagged_tokens(self):
        """
        A list of (:class:`Token` token, :class:`str` named entity recognition tag)
        from the text.
        """
        return [sent.ner_tagged_tokens for sent in self.sentences]

    @property
    def ner_tags(self):
        """
        A list of named entity tags corresponding to each of the tokens in the object.
        For information on what each of the tags can be, check the documentation on
        the specific :attr:`ner_tagger` used for this object.
        """
        return [sent.ner_tags for sent in self.sentences]

    @property
    def cems(self):
        """
        A list of all Chemical Entity Mentions in this text as :class:`chemdataextractor.doc.text.span`
        """
        return [cem for sent in self.sentences for cem in sent.cems]

    @property
    def definitions(self):
        """
        Return a list of tagged definitions for each sentence in this text passage
        """
        return [definition for sent in self.sentences for definition in sent.definitions]

    @property
    def chemical_definitions(self):
        """
        Return a list of tagged definitions for each sentence in this text passage
        """
        return [definition for sent in self.sentences for definition in sent.chemical_definitions]

    @property
    @deprecated(deprecated_in="2.1", details="Deprecated due to the introduction of RichTokens, and is now just an alias for .tokens.")
    def tagged_tokens(self):
        """
        A list of lists of :class:`~chemdataextractor.doc.text.RichToken` instances found in the text.
        """
        return [sent.tagged_tokens for sent in self.sentences]

    @property
    def tags(self):
        return [sent.tags for sent in self.sentences]

    @property
    def abbreviation_definitions(self):
        """
        A list of all abbreviation definitions in this Document. Each abbreviation is in the form
        (:class:`str` abbreviation, :class:`str` long form of abbreviation, :class:`str` ner_tag)
        """
        return [ab for sent in self.sentences for ab in sent.abbreviation_definitions]

    @property
    def records(self):
        """All records found in the object, as a list of :class:`~chemdataextractor.model.base.BaseModel`."""
        return ModelList(*[r for sent in self.sentences for r in sent.records])

    def __add__(self, other):
        if type(self) == type(other):
            merged = self.__class__(
                text=self.text + other.text,
                id=self.id or other.id,
                references=self.references + other.references,
                sentence_tokenizer=self.sentence_tokenizer,
                word_tokenizer=self.word_tokenizer,
                lexicon=self.lexicon,
                abbreviation_detector=self.abbreviation_detector,
                pos_tagger=self.pos_tagger,
                ner_tagger=self.ner_tagger,
            )
            return merged
        return NotImplemented


class Title(Text):

    def __init__(self, text, **kwargs):
        super(Title, self).__init__(text, **kwargs)
        self.models = []

    def _repr_html_(self):
        return '<h1 class="cde-title">' + self.text + '</h1>'


class Heading(Text):

    def __init__(self, text, **kwargs):
        super(Heading, self).__init__(text, **kwargs)
        self.models = []
        # default_parsers = [CompoundHeadingParser(), ChemicalLabelParser()]

    def _repr_html_(self):
        return '<h2 class="cde-title">' + self.text + '</h2>'


class Paragraph(Text):

    def __init__(self, text, **kwargs):
        super(Paragraph, self).__init__(text, **kwargs)
        # default_parsers = [CompoundParser(), ChemicalLabelParser(), NmrParser(), IrParser(), UvvisParser(), MpParser(),
        #        TgParser(), ContextParser()]
        self.models = []

    def _repr_html_(self):
        return '<p class="cde-paragraph">' + self.text + '</p>'


class Footnote(Text):

    def __init__(self, text, **kwargs):
        super(Footnote, self).__init__(text, **kwargs)
        # default_parsers = [ContextParser(), CaptionContextParser()]
        self.models = []

    def _repr_html_(self):
        return '<p class="cde-footnote">' + self.text + '</p>'


class Citation(Text):
    taggers = [ChemCrfPosTagger(), NoneTagger(tag_type=NER_TAG_TYPE)]
    abbreviation_detector = None
    # TODO: Citation parser
    # TODO: Store number/label

    def _repr_html_(self):
        return '<p class="cde-citation">' + self.text + '</p>'


class Caption(Text):

    def __init__(self, text, **kwargs):
        super(Caption, self).__init__(text, **kwargs)
        self.models = []
        # default_parsers = [CompoundParser(), ChemicalLabelParser(), CaptionContextParser()]

    def _repr_html_(self):
        return '<caption class="cde-caption">' + self.text + '</caption>'

    @property
    def definitions(self):
        return [definition for sent in self.sentences for definition in sent.definitions]


class Sentence(BaseText):
    """A single sentence within a text passage."""

    word_tokenizer = BertWordTokenizer()
    lexicon = ChemLexicon()
    abbreviation_detector = ChemAbbreviationDetector()
    taggers = [ChemCrfPosTagger(), cem_tagger]

    def __init__(self, text, start=0, end=None, word_tokenizer=None, lexicon=None, abbreviation_detector=None, pos_tagger=None, ner_tagger=None, **kwargs):
        """
        .. note::

            If intended as part of a :class:`chemdataextractor.doc.document.Document`,
            an element should either be initialized with a reference to its containing document,
            or its :attr:`document` attribute should be set as soon as possible.
            If the element is being passed in to a :class:`chemdataextractor.doc.document.Document`
            to initialise it, the :attr:`document` attribute is automatically set
            during the initialisation of the document, so the user does not need to worry about this.

        :param str text: The text contained in this element.
        :param int start: (Optional) The starting index of the sentence within the containing element. Default 0.
        :param int end: (Optional) The end index of the sentence within the containing element. Defualt None
        :param WordTokenizer word_tokenizer: (Optional) Word tokenizer for this element.
            Default :class:`~chemdataextractor.nlp.tokenize.ChemWordTokenizer`.
        :param Lexicon lexicon: (Optional) Lexicon for this element. The lexicon stores all the occurences of unique words and can provide
            Brown clusters for the words. Default :class:`~chemdataextractor.nlp.lexicon.ChemLexicon`
        :param AbbreviationDetector abbreviation_detector: (Optional) The abbreviation detector for this element.
            Default :class:`~chemdataextractor.nlp.abbrev.ChemAbbreviationDetector`.
        :param BaseTagger pos_tagger: (Optional) The part of speech tagger for this element.
            Default :class:`~chemdataextractor.nlp.pos.ChemCrfPosTagger`.
        :param BaseTagger ner_tagger: (Optional) The named entity recognition tagger for this element.
            Default :class:`~chemdataextractor.nlp.cem.CemTagger`
        :param Document document: (Optional) The document containing this element.
        :param str label: (Optional) The label for the captioned element, e.g. Table 1 would have a label of 1.
        :param Any id: (Optional) Some identifier for this element. Must be equatable.
        :param list[chemdataextractor.models.BaseModel] models: (Optional) A list of models for this element to parse.
            If the element is part of another element (e.g. a :class:`~chemdataextractor.doc.text.Sentence`
            inside a :class:`~chemdataextractor.doc.text.Paragraph`), or is part of a :class:`~chemdataextractor.doc.document.Document`,
            this is set automatically to be the same as that of the containing element, unless manually set otherwise.
        """
        self.models = []
        super(Sentence, self).__init__(text, word_tokenizer=word_tokenizer, lexicon=lexicon, abbreviation_detector=abbreviation_detector, pos_tagger=pos_tagger, ner_tagger=ner_tagger, **kwargs)
        #: The start index of this sentence within the text passage.
        self.start = start
        #: The end index of this sentence within the text passage.
        self.end = end if end is not None else len(text)

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__, self._text, self.start, self.end)

    @memoized_property
    def tokens(self):
        tokens = self.word_tokenizer.get_word_tokens(self)
        for token in tokens:
            token.text = "".join(ch for ch in token.text if unicodedata.category(ch)[0] != "C")
        return tokens

    def _tokens_for_spans(self, spans):
        toks = [RichToken(
            text=self.text[span[0]:span[1]],
            start=span[0] + self.start,
            end=span[1] + self.start,
            lexicon=self.lexicon,
            sentence=self
        ) for span in spans]
        return toks

    @property
    def raw_tokens(self):
        """A list of :class:`str` representations for the tokens in the object."""
        return [token.text for token in self.tokens]

    @memoized_property
    def pos_tagged_tokens(self):
        """A list of (:class:`Token` token, :class:`str` tag) tuples for each sentence in this sentence."""
        # log.debug('Getting pos tags')
        return [(token.text, token.pos_tag) for token in self.tokens]

    @property
    def pos_tags(self):
        """A list of :class:`str` part of speech tags for each sentence in this sentence."""
        return [token[1] for token in self.pos_tagged_tokens]

    @memoized_property
    def unprocessed_ner_tagged_tokens(self):
        """
        A list of (:class:`Token` token, :class:`str` named entity recognition tag)
        from the text.

        No corrections from abbreviation detection are performed.
        """
        # log.debug('Getting unprocessed_ner_tags')
        return [(token.text, token.ner_tag) for token in self.tokens]

    @memoized_property
    def unprocessed_ner_tags(self):
        """
        A list of :class:`str` unprocessed named entity tags for the tokens in this sentence.

        No corrections from abbreviation detection are performed.
        """
        return [token[1] for token in self.unprocessed_ner_tagged_tokens]

    @memoized_property
    def abbreviation_definitions(self):
        """
        A list of all abbreviation definitions in this Document. Each abbreviation is in the form
        (:class:`str` abbreviation, :class:`str` long form of abbreviation, :class:`str` ner_tag)
        """
        abbreviations = []
        if self.abbreviation_detector:
            # log.debug('Detecting abbreviations')
            ners = self.unprocessed_ner_tags
            for abbr_span, long_span in self.abbreviation_detector.detect_spans(self.raw_tokens):
                abbr = self.raw_tokens[abbr_span[0]:abbr_span[1]]
                long = self.raw_tokens[long_span[0]:long_span[1]]
                # Check if long is entirely tagged as one named entity type
                long_tags = ners[long_span[0]:long_span[1]]
                unique_tags = set([tag[2:] for tag in long_tags if tag is not None])
                tag = long_tags[0][2:] if None not in long_tags and len(unique_tags) == 1 else None
                abbreviations.append((abbr, long, tag))
        return abbreviations

    @memoized_property
    def ner_tagged_tokens(self):
        """
        A list of (:class:`Token` token, :class:`str` named entity recognition tag)
        from the sentence.
        """
        return list(zip(self.raw_tokens, self.ner_tags))

    @memoized_property
    def ner_tags(self):
        """
        A list of named entity tags corresponding to each of the tokens in the object.
        For information on what each of the tags can be, check the documentation on
        the specific :attr:`ner_tagger` used for this object.
        """
        # log.debug('Getting ner_tags')
        ner_tags = self.unprocessed_ner_tags
        abbrev_defs = self.document.abbreviation_definitions if self.document else self.abbreviation_definitions
        # Ensure abbreviation entity matches long entity
        # TODO: This is potentially a performance bottleneck?
        for i in range(0, len(ner_tags)):
            for abbr, long, ner_tag in abbrev_defs:
                if abbr == self.raw_tokens[i:i+len(abbr)]:
                    old_ner_tags = ner_tags[i:i+len(abbr)]
                    ner_tags[i] = 'B-%s' % ner_tag if ner_tag is not None else None
                    ner_tags[i+1:i+len(abbr)] = ['I-%s' % ner_tag if ner_tag is not None else None] * (len(abbr) - 1)
                    # Remove ner tags from brackets surrounding abbreviation
                    if i > 1 and self.raw_tokens[i-1] == '(':
                        ner_tags[i-1] = None
                    if i < len(self.raw_tokens) - 1 and self.raw_tokens[i+1] == ')':
                        ner_tags[i+1] = None
                    if not old_ner_tags == ner_tags[i:i+len(abbr)]:
                        log.debug('Correcting abbreviation tag: %s (%s): %s -> %s' % (' '.join(abbr), ' '.join(long), old_ner_tags, ner_tags[i:i+len(abbr)]))
        # TODO: Ensure abbreviations in brackets at the end of an entity match are separated and the brackets untagged
        # Hydrogen Peroxide (H2O2)
        # Tungsten Carbide (WC)
        # TODO: Filter off alphanumerics from end (1h) (3) (I)
        # May need more intelligent
        return ner_tags

    @memoized_property
    def cems(self):
        """
        A list of all Chemical Entity Mentions in this text as :class:`~chemdataextractor.doc.text.Span`
        """
        # log.debug('Getting cems')
        spans = []
        # print(self.text.encode('utf8'))
        for result in chemical_name.scan(self.tokens):
            # parser scan yields (result, startindex, endindex) - we just use the indexes here
            tokens = self.tokens[result[1]:result[2]]
            start = tokens[0].start
            end = tokens[-1].end
            # Adjust boundaries to exclude disallowed prefixes/suffixes
            currenttext = self.text[start-self.start:end-self.start].lower()
            for prefix in IGNORE_PREFIX:
                if currenttext.startswith(prefix):
                    # print('%s removing %s' % (currenttext, prefix))
                    start += len(prefix)
                    break
            for suffix in IGNORE_SUFFIX:
                if currenttext.endswith(suffix):
                    # print('%s removing %s' % (currenttext, suffix))
                    end -= len(suffix)
                    break
            # Adjust boundaries to exclude matching brackets at start and end
            currenttext = self.text[start-self.start:end-self.start]
            for bpair in [('(', ')'), ('[', ']')]:
                if len(currenttext) > 2 and currenttext[0] == bpair[0] and currenttext[-1] == bpair[1]:
                    level = 1
                    for k, char in enumerate(currenttext[1:]):
                        if char == bpair[0]:
                            level += 1
                        elif char == bpair[1]:
                            level -= 1
                        if level == 0 and k == len(currenttext) - 2:
                            start += 1
                            end -= 1
                            break

            # If entity has been reduced to nothing by adjusting boundaries, skip it
            if start >= end:
                continue

            currenttext = self.text[start-self.start:end-self.start]

            # Do splits
            split_spans = []
            comps = list(regex_span_tokenize(currenttext, '(-|\+|\)?-to-\(?|···|/|\s)'))
            if len(comps) > 1:
                for split in SPLITS:
                    if all(re.search(split, currenttext[comp[0]:comp[1]]) for comp in comps):
                        # print('%s splitting %s' % (currenttext, [currenttext[comp[0]:comp[1]] for comp in comps]))
                        for comp in comps:
                            span = Span(text=currenttext[comp[0]:comp[1]], start=start+comp[0], end=start+comp[1])
                            # print('SPLIT: %s - %s' % (currenttext, repr(span)))
                            split_spans.append(span)
                        break
                else:
                    split_spans.append(Span(text=currenttext, start=start, end=end))
            else:
                split_spans.append(Span(text=currenttext, start=start, end=end))

            # Do specials
            for split_span in split_spans:
                for special in SPECIALS:
                    m = re.search(special, split_span.text)
                    if m:
                        # print('%s special %s' % (split_span.text, m.groups()))
                        for i in range(1, len(m.groups()) + 1):
                            span = Span(text=m.group(i), start=split_span.start+m.start(i), end=split_span.start+m.end(i))
                            # print('SUBMATCH: %s - %s' % (currenttext, repr(span)))
                            spans.append(span)
                        break
                else:
                    spans.append(split_span)
        return spans

    @memoized_property
    def definitions(self):
        """
        Return specifier definitions from this sentence

        A definition consists of:
        a) A definition -- The quantitity being defined e.g. "Curie Temperature"
        b) A specifier -- The symbol used to define the quantity e.g. "Tc"
        c) Start -- The index of the starting point of the definition
        d) End -- The index of the end point of the definition

        :return: list -- The specifier definitions
        """
        defs = []
        tokens = self.tokens
        for result in specifier_definition.scan(tokens):
            definition = result[0]
            start = result[1]
            end = result[2]
            new_def = {
                       'definition': first(definition.xpath('./phrase/text()')),
                       'specifier': first(definition.xpath('./specifier/text()')),
                       'tokens': tokens[start:end],
                       'start': start,
                       'end': end}
            defs.append(new_def)
        return defs

    @memoized_property
    def chemical_definitions(self):
        """Return a list of chemical entity mentions and their associated label
        """
        cem_defs = []
        tokens = self.tokens
        for result in cem_phrase.scan(tokens):
            tree = result[0]
            start = result[1]
            end = result[2]
            name = first(tree.xpath('./compound/names/text()'))
            label = first(tree.xpath('./compound/labels/text()'))
            if name and label:
                cem_def = {
                    'name': name,
                    'label': label,
                    'start': start,
                    'end': end
                }
                cem_defs.append(cem_def)
        return cem_defs

    @memoized_property
    def tags(self):
        tags = self.pos_tags
        for i, tag in enumerate(self.ner_tags):
            if tag is not None:
                tags[i] = tag
        return tags

    @property
    @deprecated(deprecated_in="2.1", details="Deprecated due to the introduction of RichTokens, and is now just an alias for .tokens.")
    def tagged_tokens(self):
        """
        A list of :class:`~chemdataextractor.doc.text.RichToken` instances found in the text.

        """
        return self.tokens

    def _assign_tags(self, tag_type):
        """
        Assign tags for each token, with some intelligence with regards to which method to use for tagging.
        See :class:`~chemdataextractor.nlp.tag.BaseTagger` and :ref:`this guide<creating_taggers>` for more information.
        """
        for tagger in reversed(self.taggers):
            if tagger.can_tag(tag_type):
                tags = None
                if hasattr(tagger, "batch_tag_for_type") and tagger.can_batch_tag(tag_type) and self.document is not None:
                    self.document._batch_assign_tags(tagger, tag_type)
                elif hasattr(tagger, "tag_for_type"):
                    tags = tagger.tag_for_type(self.tokens, tag_type)
                elif hasattr(tagger, "batch_tag") and self.document is not None:
                    self.document._batch_assign_tags(tagger, tag_type)
                else:
                    if hasattr(tagger, "tag"):
                        tags = tagger.tag(self.tokens)
                    else:
                        tags = tagger.legacy_tag(self.raw_tokens)
                if tags is not None:
                    for index, tag in enumerate(tags):
                        self.tokens[index]._tags[tag_type] = tag[1]
                break

    @property
    def quantity_re(self):
        return construct_quantity_re(*self._streamlined_models)

    @property
    def records(self):
        """All records found in the object, as a list of :class:`~chemdataextractor.model.base.BaseModel`."""
        records = ModelList()
        seen_labels = set()
        for model in self._streamlined_models:
            for parser in model.parsers:
                if hasattr(parser, 'parse_sentence'):
                    for record in parser.parse_sentence(self):
                        p = record.serialize()
                        if record.is_empty:  # TODO: Potential performance issues?
                            continue
                        # Skip duplicate records
                        if record in records:
                            continue
                        # Skip just labels that have already been seen (bit of a hack)
                        if (isinstance(record, Compound) and 'Compound' in p.keys() and all(k in {'labels', 'roles'} for k in p['Compound'].keys()) and
                          set(record.labels).issubset(seen_labels)):
                            continue
                        if isinstance(record, Compound):
                            seen_labels.update(record.labels)
                            # This could be super slow if we find lots of things
                            found = False
                            for seen_record in records:
                                if (isinstance(seen_record, Compound)
                                  and (not set(record.names).isdisjoint(seen_record.names)
                                       or not set(record.labels).isdisjoint(seen_record.labels))):
                                    seen_record.names = sorted(list(set(seen_record.names).union(record.names)))
                                    seen_record.labels = sorted(list(set(seen_record.labels).union(record.labels)))
                                    seen_record.roles = sorted(list(set(seen_record.roles).union(record.roles)))
                                    found = True
                            if found:
                                continue
                        elif hasattr(record, 'compound') and record.compound is not None:
                            seen_labels.update(record.compound.labels)
                        records.append(record)
        i = 0
        length = len(records)
        while i < length:
            j = 0
            while j < length:
                if i != j:
                    records[j].merge_all(records[i])
                j += 1
            i += 1
        return records

    def __add__(self, other):
        if type(self) == type(other):
            merged = self.__class__(
                text=self.text + other.text,
                start=self.start,
                end=None,
                id=self.id or other.id,
                references=self.references + other.references,
                word_tokenizer=self.word_tokenizer,
                lexicon=self.lexicon,
                abbreviation_detector=self.abbreviation_detector,
                pos_tagger=self.pos_tagger,
                ner_tagger=self.ner_tagger,
            )
            return merged
        return NotImplemented


class Cell(Sentence):
    """Data cell for tables. One row of the category table"""
    # It appears that using different tokenizers/taggers is making the cem recognition worse.
    # This is also consistent with the use of the regular expressions etc we have defined so far.
    # word_tokenizer = FineWordTokenizer()
    # pos_tagger = NoneTagger()
    # ner_tagger = NoneTagger()


    def __init__(self, *args, **kwargs):
        super(Cell, self).__init__(*args, **kwargs)
        self.data = None
        self.row_categories = None
        self.col_categories = None
        self.is_tde_cell = False
        self.data_sent = None
        self.row_categories_sents = None
        self.col_categories_sents = None

    @classmethod
    def from_tdecell(cls, tde_cell, document=None, **kwargs):
        # Have the spacing between the cells contain characters that will never be found
        # so that the system doesn't become confused because it found some number in the heading
        # that it confuses as a power for a unit.
        separator = '🙃🙃🙃🙃'
        cell_separator = ';'
        text = ' '.join([tde_cell[0], separator, cell_separator.join(tde_cell[1]), separator, cell_separator.join(tde_cell[2])])
        cell = cls(text, document=document, **kwargs)
        cell.data = tde_cell[0]
        cell.row_categories = tde_cell[1]
        cell.col_categories = tde_cell[2]
        cell.data_sent = Sentence(cell.data)
        cell.row_categories_sents = [Sentence(cell_text) for cell_text in cell.row_categories]
        cell.col_categories_sents = [Sentence(cell_text) for cell_text in cell.col_categories]
        cell.is_tde_cell = True
        cell.document = document

        # Doing it this way means that a lot of RichTokens are shared between the sub-elements, resulting
        # in tagging being only done once per RichToken, which is faster.
        tokens = cell.data_sent.tokens
        separator_token = RichToken(separator, 0, 0, cls.lexicon, cell)
        tokens.append(separator_token)

        for row_category_sent in cell.row_categories_sents:
            cell_separator = RichToken(separator, 0, 0, cls.lexicon, cell)
            tokens.extend(row_category_sent.tokens)
            tokens.append(cell_separator)

        if cell.row_categories_sents:
            tokens = tokens[:-1]

        separator_token = RichToken(separator, 0, 0, cls.lexicon, cell)
        tokens.append(separator_token)
        for col_category_sent in cell.col_categories_sents:
            cell_separator = RichToken(separator, 0, 0, cls.lexicon, cell)
            tokens.extend(col_category_sent.tokens)
            tokens.append(cell_separator)

        if cell.col_categories_sents:
            tokens = tokens[:-1]

        for token in tokens:
            token.sentence = cell

        cell._tokens = tokens

        return cell

    @memoized_property
    def abbreviation_definitions(self):
        """Empty list. Abbreviation detection is disabled within table cells."""
        return []

    @property
    def records(self):
        """Empty list. Individual cells don't provide records, this is handled by the parent Table."""
        return []

    @property
    def elements(self):
        elements = []
        # if self.data_sent is not None:
        #     elements.append(self.data_sent)
        #     elements.extend(self.row_categories_sents)
        #     elements.extend(self.col_categories_sents)
        return elements


@python_2_unicode_compatible
class Span(object):
    """A text span within a sentence."""

    def __init__(self, text, start, end):
        """
        :param str text: The text contained by this span.
        :param int start: The start offset of this token in the original text.
        :param int end: The end offsent of this token in the original text.
        """
        self.text = text
        """The :class:`str` text content of this span."""
        self.start = start
        """The :class:`int` start offset of this token in the original text."""
        self.end = end
        """The :class:`int` end offset of this token in the original text."""

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__, self.text, self.start, self.end)

    def __str__(self):
        return self.text

    def __eq__(self, other):
        """Span objects are equal if the source text is equal, and the start and end indices are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.text == other.text and self.start == other.start and self.end == other.end

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.text, self.start, self.end))

    @property
    def length(self):
        """The :class:`int` offset length of this span in the original text."""
        return self.end - self.start


class Token(Span):
    """A single token within a sentence. Corresponds to a word, character, punctuation etc."""

    def __init__(self, text, start, end, lexicon):
        """
        :param str text: The text contained by this token.
        :param int start: The start offset of this token in the original text.
        :param int end: The end offset of this token in the original text.
        :param Lexicon lexicon: The lexicon which contains this token.
        """
        super(Token, self).__init__(text, start, end)
        #: The lexicon for this token.
        self.lexicon = lexicon
        self.lexicon.add(text)

    @property
    def lex(self):
        """The corresponding :class:`chemdataextractor.nlp.lexicon.Lexeme` entry in the Lexicon for this token."""
        return self.lexicon[self.text]


class RichToken(Token):
    """
    :class:`~chemdataextractor.doc.text.RichToken` provides a flexible way to store properties related to tokens.
    :class:`~chemdataextractor.doc.text.RichToken` instances hold a reference to the parent sentence they come from, and if the user
    desires a certain tag, the parent sentence is called and its taggers used to tag
    the sentence on demand. This structure means that tokens are tagged *if and only if*
    the user requires them. These tags are then cached by the :class:`~chemdataextractor.doc.text.RichToken` so that any single token
    is only ever tagged once.

    Such tags can be accessed either via dot syntax (:python:`token.ner_tag`) or
    via dictionary syntax (:python:`token['ner_tag']`). To maintain compatibility with
    the return value for :meth:`~chemdataextractor.doc.text.Sentence.tagged_tokens` from previous
    versions of ChemDataExtractor, the keys of :python:`0` and :python:`1` are reserved for the
    text of the token and the combined NER and PoS tags, respectively. Furthermore, any properties
    included in the :class:`~chemdataextractor.doc.text.Token` class are reserved as well.

    .. note::

        By default, ChemDataExtractor provides, and assumes that calling :python:`.ner_tag` and
        :python:`.pos_tag` on a :class:`~chemdataextractor.doc.text.RichToken`
        will not fail, which should be taken into account when setting the :python:`taggers` property on any
        :class:`~chemdataextractor.doc.text.BaseText` subclasses.
    """

    def __init__(self, text, start, end, lexicon, sentence):
        super(RichToken, self).__init__(text, start, end, lexicon)
        self.sentence = sentence
        self._tags = {}

    @classmethod
    def _from_token(cls, token, sentence):
        rich_token = cls(text=token.text,
                         start=token.start,
                         end=token.end,
                         lexicon=token.lexicon,
                         sentence=sentence)
        return rich_token

    @property
    def legacy_pos_tag(self):
        pos_tag = self[POS_TAG_TYPE]
        ner_tag = self[NER_TAG_TYPE]
        if ner_tag is not None and ner_tag != "O":
            return ner_tag
        else:
            return pos_tag

    def __getitem__(self, key):
        if key == 0:
            return self.text
        elif key == 1:
            return self.legacy_pos_tag
        elif isinstance(key, str):
            return self.__getattr__(key)
        else:
            raise IndexError("Key" + str(key) + " is out of bounds for this token.")

    def __getattr__(self, name):
        if name in self._tags.keys():
            return self._tags[name]
        else:
            self.sentence._assign_tags(name)
            if name not in self._tags.keys():
                raise AttributeError(name + " is not a supported tag type for the sentence: " + str(self.sentence) + str(self.sentence.taggers) + str(type(self.sentence))
                                     + str(self._tags) + str(self))
            return self._tags[name]
