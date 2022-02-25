===========================
Natural Language Processing
===========================

ChemDataExtractor also includes state of the art Natural Language Processing (NLP) facilities, as described here.

Tokenization
-----------------

.. rubric:: Sentence Tokenization

Use the ``sentences`` property on a text-based document element to perform sentence segmentation::

    >>> from chemdataextractor.doc import Paragraph
    >>> para = Paragraph('1,4-Dibromoanthracene was prepared from 1,4-diaminoanthraquinone. 1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.')
    >>> para.sentences
    [Sentence('1,4-Dibromoanthracene was prepared from 1,4-diaminoanthraquinone.', 0, 65),
     Sentence('1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.', 66, 135)]

Each sentence object is a document element in itself, and additionally contains the start and end character offsets within it's parent element.

.. rubric:: Word Tokenization

Use the ``tokens`` property to get the word tokens::

    >>> para.tokens
    [[Token('1,4-Dibromoanthracene', 0, 21),
      Token('was', 22, 25),
      Token('prepared', 26, 34),
      Token('from', 35, 39),
      Token('1,4-diaminoanthraquinone', 40, 64),
      Token('.', 64, 65)],
     [Token('1H', 66, 68),
      Token('NMR', 69, 72),
      Token('spectra', 73, 80),
      Token('were', 81, 85),
      Token('recorded', 86, 94),
      Token('on', 95, 97),
      Token('a', 98, 99),
      Token('300', 100, 103),
      Token('MHz', 104, 107),
      Token('BRUKER', 108, 114),
      Token('DPX300', 115, 121),
      Token('spectrometer', 122, 134),
      Token('.', 134, 135)]]

This also works on an individual sentence::

    >>> para.sentences[0].tokens
    [Token('1,4-Dibromoanthracene', 0, 21),
     Token('was', 22, 25),
     Token('prepared', 26, 34),
     Token('from', 35, 39),
     Token('1,4-diaminoanthraquinone', 40, 64),
     Token('.', 64, 65)]

There are also ``raw_sentences`` and ``raw_tokens`` properties that return strings instead of ``Sentence`` and ``Token`` objects.

.. rubric:: Using Tokenizers Directly

All tokenizers have a ``tokenize`` method that takes a text string and returns a list of tokens::

    >>> from chemdataextractor.nlp.tokenize import ChemWordTokenizer
    >>> cwt = ChemWordTokenizer()
    >>> cwt.tokenize('1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.')
    ['1H', 'NMR', 'spectra', 'were', 'recorded', 'on', 'a', '300', 'MHz', 'BRUKER', 'DPX300', 'spectrometer', '.']

There is also a ``span_tokenize`` method that returns the start and end offsets of the tokens in terms of the characters in the original string::

    >>> cwt.span_tokenize('1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.')
    [(0, 2), (3, 6), (7, 14), (15, 19), (20, 28), (29, 31), (32, 33), (34, 37), (38, 41), (42, 48), (49, 55), (56, 68), (68, 69)]


Part-of-speech Tagging
---------------------------

ChemDataExtractor contains a chemistry-aware Part-of-speech tagger. Use the ``pos_tagged_tokens`` property on a document element to get the tagged tokens::

    >>> s = Sentence('1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.')
    >>> s.pos_tagged_tokens
    [('1H', 'NN'),
     ('NMR', 'NN'),
     ('spectra', 'NNS'),
     ('were', 'VBD'),
     ('recorded', 'VBN'),
     ('on', 'IN'),
     ('a', 'DT'),
     ('300', 'CD'),
     ('MHz', 'NNP'),
     ('BRUKER', 'NNP'),
     ('DPX300', 'NNP'),
     ('spectrometer', 'NN'),
     ('.', '.')]

.. rubric:: Using Taggers Directly

All taggers have a ``tag`` method that takes a list of :class:`~chemdataextractor.doc.text.RichToken` instances and returns a list of (token, tag) tuples. For more information on how to use these taggers directly, see the documentation for :class:`~chemdataextractor.nlp.BaseTagger`.

Lexicon
------------

As ChemDataExtractor processes documents, it adds each unique word that it encounters to the ``Lexicon`` as a ``Lexeme``.
Each ``Lexeme`` stores various word features, so they don't have to be re-calculated for every occurrence of that word.

You can access the Lexeme for a token using the ``lex`` property:

    >>> s = Sentence('Sulphur and Oxygen.')
    >>> s.tokens[0]
    Token('Sulphur', 0, 7)
    >>> s.tokens[0].lex.normalized
    'sulfur'
    >>> s.tokens[0].lex.is_hyphenated
    False
    >>> s.tokens[0].lex.cluster
    '11011101100110'

Abbreviation Detection
---------------------------

Abbreviation detection is done using a method based on the algorithm in Schwartz & Hearst 2003::

    >>> p = Paragraph(u'Dye-sensitized solar cells (DSSCs) with ZnTPP = Zinc tetraphenylporphyrin.')
    >>> p.abbreviation_definitions
    [([u'ZnTPP'], [u'Zinc', u'tetraphenylporphyrin'], u'CM'),
     ([u'DSSCs'], [u'Dye', u'-', u'sensitized', u'solar', u'cells'], None)]

Abbreviation definitions are returned as tuples containing the abbreviation,
the long name, and an entity tag. The entity tag is ``CM`` if the abbreviation is for a chemical entity, otherwise it is ``None``.
