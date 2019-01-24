*********************
Getting Started
*********************

.. contents::

The ChemDataExtractor Toolkit
=================================

The ChemDataExtractor toolkit is an advanced natural language processing pipeline for extracting chemical property
information from the scientific literature. A full description of the theory behind the toolkit can be found in the
original paper:

*Swain, M. C., & Cole, J. M. "ChemDataExtractor: A Toolkit for Automated Extraction of Chemical Information from the Scientific Literature", J. Chem. Inf. Model. 2016, 56 (10), pp 1894--1904 10.1021/acs.jcim.6b00207*.

and the associated website https://chemdataextractor.org.

The general process for extracting information from scientific text is as follows:

1. Break a document down into its consituent elements (Title, Paragraphs, Sentences, Tables, Figures...)
2. Tokenize the text to isolate individual tokens
3. Apply Part-of-speech tagging to identify the semantic role of each token
4. Detect Chemical Named Entites using machine learning
5. Parse text and tables with nested rules to identify chemical relationships
6. Resolve the interdependencies between the different elements
7. Output a set of mutually consistent chemical records

This pipeline enables ChemDataExtractor to extract chemical information in a completely domain-independent manner.

Installation
=================================

To get up and running with ChemDataExtractor, you will need to install the python toolkit and then download the
necessary data files.
There are a few different ways to download and install the ChemDataExtractor toolkit.

.. rubric:: Option 1. Using conda

This method is recommended for all Windows users, as well as beginners on all platforms who don't already have Python
installed. Anaconda Python is a self-contained Python environment that is particularly useful for scientific
applications.

Start by installing `Miniconda <https://conda.io/miniconda.html>`_, which includes a complete Python distribution and the
conda package manager, or Anaconda, which additionally includes many pre-installed packages, including NumPy and
Matplotlib. Choose the Python 3.5 version, unless you have a particular reason why you must use Python 2.7.

Once installed, at the command line, run::

    $ conda install -c chemdataextractor chemdataextractor

This command installs the chemdataextractor package from the chemdataextractor conda channel.

.. rubric:: Option 2. Using pip

If you already have Python installed, it's easiest to install the ChemDataExtractor package using pip. At the command line, run::

    $ pip install ChemDataExtractor

On Windows, this will require the Microsoft Visual C++ Build Tools to be installed. If you don't already have pip installed, you can install it using ``get-pip.py``.

.. rubric:: Option 3. Download the Latest Release

Alternatively, download the latest release manually from github or the ChemDataExtractor website and install it yourself by running::

    $ cd chemdataextractor
    $ python setup.py install

The ``setup.py`` command will install ChemDataExtractor in your site-packages folder so it is automatically available to all your python scripts.

You can also get the latest release by cloning the git source code repository from https://github.com/CambridgeMolecularEngineering/chemdataextractor/.

.. rubric:: Getting the Data Files

In order to function, ChemDataExtractor requires a variety of data files, such as machine learning models, dictionaries, and word clusters. Get these by running::

    $ cde data download`

This will download all the necessary data files to the data directory. Run::

    $ cde data where

to see where this is.

.. rubric:: Updating

Upgrade your installation to the latest version at any time using conda or pip, matching the method you used originally to install it. For conda, run::

    $ conda update -c chemdataextractor chemdataextractor

For pip, run::

    $ pip install --upgrade ChemDataExtractor

Either way, always remember to download any new data files after doing this::

    $ cde data download

Reading a Document
=================================

Most commonly, you want to pass an entire document file to ChemDataExtractor. ChemDataExtractor comes with a number of built-in Document readers that can read HTML, PDF and XML files. These readers are responsible for detecting the different elements of a document and recompiling them into a single consistent document structure::

    >>> from chemdataextractor import Document
    >>> f = open('paper.html', 'rb')
    >>> doc = Document.from_file(f)

Each reader will be tried in turn until one is successfully able to read the file. If you know exactly which readers you want to use, it is possible to specify a list as an optional parameter::

    >>> f = open('rsc_article.html', 'rb')
    >>> doc = Document.from_file(f, readers=[RscHtmlReader()])

.. note:: Always open files in binary mode by using the 'rb' parameter.

Alternatively, you can load a document into ChemDataExtractor by passing it some text::

    >>> doc = Document('UV-vis spectrum of 5,10,15,20-Tetra(4-carboxyphenyl)porphyrin in Tetrahydrofuran (THF).')

At present, the available readers are:
    * AcsHtmlReader - For ACS HTML articles
    * RscHtmlReader - For RSC HTML articles
    * NlmXmlReader - For NLM/JATS XML (e.g. from PubMed Central)
    * UsptoXmlReader - For patent XML from the US Patent Office
    * CsspHtmlReader - For ChemSpider SyntheticPages
    * XmlReader - Generic XML
    * HtmlReader - Generic HTML
    * PdfReader - Generic PDF
    * PlainTextReader - Generic plain text

The HTML and XML readers can determine document structure such as headings, paragraphs, and tables with high accuracy. However, this is much harder to achieve with the PDF and plain text readers.

More information about document readers can be found in the :ref:`section_advanced_topics`.

.. rubric:: Document Elements

Once read, documents are represented by a single linear stream of `element` objects. This stream is now independent of the initial document type or the source::

    >>> doc.elements
    [Title('A very important scientific article'),
    Heading('Abstract'),
    Paragraph('The first paragraph of text...'),
    ...]

Element types include Title, Heading, Paragraph, Citation, Table, Figure, Caption and Footnote. You can retrieve a specific element by its index within the document::

    >>> para = doc.elements[14]
    >>> para
    Paragraph('1,4-Dibromoanthracene was prepared from 1,4-diaminoanthraquinone. 1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.')

You can also get the individual sentences of a paragraph::

    >>> para.sentences
    [Sentence('1,4-Dibromoanthracene was prepared from 1,4-diaminoanthraquinone.', 0, 65),
    Sentence('1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.', 66, 135)]

Or, the individual tokens::

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

as well as a list of individual chemical entity mentions (CEMs) of the document::

    >>> doc.cems
    [Span('5,10,15,20-Tetra(4-carboxyphenyl)porphyrin', 19, 61),
     Span('THF', 82, 85),
     Span('Tetrahydrofuran', 65, 80)]

Each mention is returned as a ``Span``, which contains the mention text, as well as the start and end character offsets within the containing document element.

You can also output the abbreviations found in the document::

    >>> doc.abbreviation_definitions
    [([u'THF'], [u'Tetrahydrofuran'], u'CM')]

The *records* method, combines all the chemical mentions, abbreviations and properties found each chemical entity (see :ref:`examples`)::

    >>> doc.records
    [<Compound>, <Compound>]
    >>> doc.records[0].serialize()
    {'names': ['5,10,15,20-Tetra(4-carboxyphenyl)porphyrin']}
    >>> doc.records[1].serialize()
    {'names': ['Tetrahydrofuran', 'THF']}


.. rubric:: Which file formats are best?

While ChemDataExtractor supports documents in a wide variety of formats, some are better suited for extraction than others. If there is an HTML or XML version available, that is normally the best choice.

Wherever possible, avoid using the PDF version of a paper or patent. At best, the text will be interpretable, but it is extremely difficult to reliably distinguish between headings, captions and main body text. At worst, the document will just consist of a scanned image of each page, and it won't be possible to extract any of the text at all. You can get some idea of what ChemDataExtractor can see in a PDF by looking at the result of copying-and-pasting from the document.

For scientific articles, most publishers offer a HTML version alongside the PDF version. Normally, this will open as a page in your web browser. Just choose "Save As..." and ensure the selected format is "HTML" or "Page Source" to save a copy of the HTML file to your computer.

Most patent offices provide XML versions of their patent documents, but these can be hard to find. Two useful resources are the USPTO Bulk Data Download Service and the EPO Open Patent Services API.

.. rubric:: More information

The :ref:`section_advanced_topics` section provides more detailed instructions for advanced ChemDataExtractor functionality.


.. _section_advanced_topics:

Advanced Topics
=================================

Document Readers
-------------------------

The document readers present in the ``chemdataextractor.reader`` package are a set of tools for identifying the elements of scientific documents.
The HTML and XML from each publisher is slightly different, meaning we once again need multiple different readers.
New users are often confused about the structure of these readers, and so this section attempts to explain their functionality more clearly.

As an example, lets look at the ``chemdataextractor.reader.rsc.RscHtmlReader`` class::

    class RscHtmlReader(HtmlReader):
        """Reader for HTML documents from the RSC."""

        cleaners = [clean, replace_rsc_img_chars, space_references]

        root_css = '#wrapper, html'
        title_css = 'h1, .title_heading'
        heading_css = 'h2, h3, h4, h5, h6, .a_heading, .b_heading, .c_heading, .c_heading_indent, .d_heading, .d_heading_indent'
        citation_css = 'span[id^="cit"]'
        table_css = 'div[class="rtable__wrapper"]'
        table_caption_css = 'div[class="table_caption"]'
        table_id_css = 'span[id^="tab"]::attr("id")'
        table_head_row_css = 'thead'
        table_body_row_css = 'tr'
        table_footnote_css = '.table_caption + table tfoot tr th .sup_inf'
        reference_css = 'small sup a, a[href^="#cit"], a[href^="#fn"], a[href^="#tab"]'
        figure_css = '.image_table'
        figure_caption_css = '.graphic_title'
        figure_label_css = 'span[id^="fig"]::attr("id")'
        ignore_css = '.table_caption + table, .left_head, sup span.sup_ref, ' \
                     'a[href^="#fn"], .PMedLink, p[class="header_text"], ' \
                     'a[href^="#tab"], span[class="sup_ref"]'

As you can see, we have a number of `CSS Selectors <https://www.w3schools.com/css/css_intro.asp>`_ that are used to select particular elements from an RSC HTML document.
Here, the variable names are important, and must follow the format ``<element_name>_css``, as this tells the ``BaseReader`` what to name the selected element.

These elements are found by examining the HTML. For example, if you find a paper from the RSC web pages, open the HTML version,
then right-click and chose "view page source" you will be able to see the raw HTML. If you are unfamiliar with HTML and CSS I recommend going through
the `TutorialsPoint HTML tutorial <https://www.tutorialspoint.com/html/>`_ and `CSS tutorial <https://www.tutorialspoint.com/css/>`_.

It should also be mentioned that these Readers override the element variables from the base ``HTMLReader`` class.
Similarly, if you want to analyse an XML document, you should override from the ``XMLReader`` class.
I first recommend using the base readers, to see how they perform, then write a new reader if you have to.

Scraping Structured Data
----------------------------

ChemDataExtractor contains a ``scrape`` package for extracting structured information from HTML and XML files. This is most useful for obtaining bibliographic data, but can be used for any kind of data that has been marked up with HTML or XML tags in source documents.

.. rubric:: Included Scrapers

ChemDataExtractor comes with ready-made scraping tools for web pages on the RSC and ACS web sites, as wells as for XML files in the NLM JATS format as used by PubMed Central and others::

    >>> from chemdataextractor.scrape import Selector
    >>> from chemdataextractor.scrape.pub.rsc import RscHtmlDocument
    >>>
    >>> htmlstring = open('rsc_example.html').read()
    >>> sel = Selector.from_text(htmlstring)
    >>> scrape = RscHtmlDocument(sel)
    >>> print(scrape.publisher)
    'Royal Society of Chemistry'
    >>> scrape.serialize()
    {'publisher': 'Royal Society of Chemistry', 'language': 'en', 'title': 'The Title'}

.. rubric:: Custom Scrapers

As an example, here is a very simple HTML file that we want to scrape some data from::

    <html>
      <head>
        <title>Example document</title>
        <meta name="citation_publication_date" content="2016-10-03">
      </head>
      <body>
        <p class="abstract">Abstract goes here...</p>
        <p class="para">Another paragraph here...</p>
      </body>
    </html>

**Defining an Entity**

To use the ``scrape`` package, we define an ``Entity`` that contains ``Fields`` that describe how to extract the desired content in a `declarative fashion <https://www.wikiwand.com/en/Declarative_programming>`_::

    from chemdataextractor.scrape import Entity

    class ExampleDocument(Entity):
        title = StringField('title')
        abstract = StringField('.abstract')
        date_published = DateTimeField('meta[name="citation_publication_date"]::attr("content")')

Each field uses a `CSS selector <https://developer.mozilla.org/en-US/docs/Learn/CSS/Introduction_to_CSS/Selectors>`_ to describe where to find the data in the document.

**XPath Expressions**

It is possible to use XPath expressions instead of CSS selectors, if desired. Just add the parameter ``xpath=True`` to the field arguments::

    date_published = DateTimeField('//meta[@name="citation_publication_date"]/@content', xpath=True)

**Processors**

Processors perform transformations on the extracted text.

.. rubric:: The Selector

The ``Selector`` is inspired by the `Scrapy <https://scrapy.org/>`_ text mining tool.
It provides a convenient unified interface for 'selecting' parts of XML and HTML documents for extraction.
``Entity`` classes make use of it behind the scenes, but for simple cases, it can be quicker and easier to use it directly to extract information.

Create a selector from a file::

    >>> htmlstring = open('rsc_example.html').read()
    >>> sel = Selector.from_text(htmlstring)

Now, instead of passing the selector to an Entity, you can query it with CSS::

    >>> sel.css('head')

This returns a ``SelectorList``, meaning you can chain queries. Call ``extract()`` or ``extract_first()`` on the returned ``SelectorList`` to get the extracted content::

    >>> sel.css('head').css('title').extract_first()
    'Example document'
    >>> sel.css('p')
    ['Abstract goes here...', 'Another paragraph here...']



Cleaners
---------------

You will see in the above code that we have specified a number of cleaners.
Cleaners attempt to fix systematic formatting errors in the HTML/XML.
A classic problem is spacing around references. For example some HTML may look like:

.. code-block:: html

    <div>
        <p>This is a result that was retrieved from
            <a><sup><span class=sup_ref>[1]</span><sup></a>.
        </p>
    </div>

When parsing, ChemDataExtractor will output::

    Paragraph(text='This a result that was retrieved from[1].',...)

So we need a cleaner whose job is to put a space between text and references.
In the ``RscHtmlReader`` class we specify a list of cleaners to act on the text::

    cleaners = [clean, replace_rsc_img_chars, space_references]

and the corresponding ``space_references`` cleaner looks like::

    def space_references(document):
        """Ensure a space around reference links, so there's a gap when they are removed."""
        for ref in document.xpath('.//a/sup/span[@class="sup_ref"]'):
            a = ref.getparent().getparent()
            if a is not None:
                atail = a.tail or ''
                if not atail.startswith(')') and not atail.startswith(',') and not atail.startswith(' '):
                    a.tail = ' ' + atail
        return document

Note that we don't explicitly need to call the cleaner as this is handled by the ``BaseReader`` class.


Chemical Records
-----------------

ChemDataExtractor processes each document element separately to extract the chemical information,
and then merges data together from every element in the document to produce a single record for each unique chemical entity.

Consider this simple document as an example::

    >>> from chemdataextractor.doc import Document, Heading, Paragraph
    >>> doc = Document(
        Heading('5,10,15,20-Tetra(4-carboxyphenyl)porphyrin (3).'),
        Paragraph('m.p. 90°C.'),
        Paragraph('Melting points were measured in Tetrahydrofuran (THF).'),
        )

Get the records for each element using the records property::

    >>> doc[0].records.serialize()
    [{'labels': ['3'], 'names': ['5,10,15,20-Tetra(4-carboxyphenyl)porphyrin']}]
    >>> doc[1].records.serialize()
    [{'melting_points': [{'units': '°C', 'value': '90'}]}]
    >>> doc[2].records.serialize()
    [{'names': ['Tetrahydrofuran', 'THF']}, {'melting_points': [{'solvent': 'Tetrahydrofuran'}]}]

Due to the data interdependencies between the different document elements,
each isn't so useful individually. Instead, it's normally much more useful to get the combined records for the entire document::

    >>> doc.records.serialize()
    [{'names': ['Tetrahydrofuran', 'THF']},
     {'labels': ['3'],
      'names': ['5,10,15,20-Tetra(4-carboxyphenyl)porphyrin']
      'melting_points': [{
        'solvent': 'Tetrahydrofuran',
        'units': '°C',
        'value': '90'
      }],
    }]

ChemDataExtractor has merged the information from all the elements into two unique chemical records.


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

All taggers have a ``tag`` method that takes a list of token strings and returns a list of (token, tag) tuples:

    >>> from chemdataextractor.nlp.pos import ChemCrfPosTagger
    >>> cpt = ChemCrfPosTagger()
    >>> cpt.tag(['1H', 'NMR', 'spectra', 'were', 'recorded', 'on', 'a', '300', 'MHz', 'BRUKER', 'DPX300', 'spectrometer', '.'])
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


Command Line Interface
----------------------------

ChemDataExtractor includes a command line tool that can be accessed by typing ``cde`` at a command prompt.

.. rubric:: Using the Command Line

On a Mac, open the **Terminal** app, which you can find by searching or by looking in the **Utilities** folder in the **Applications** folder.

On Windows, use the **Command Prompt** or **PowerShell**.

For each of the commands below, type or paste the command, then press **Return** to run it.

For any command, add ``--help`` to the end to get information on how to use it.

.. rubric:: Downloading Data Files

In order to function, ChemDataExtractor requires a variety of data files, such as machine learning models, dictionaries, and word clusters.

Data commands:

    * ``cde data download``: Download data files.
    * ``cde data clean``: Prune data that is no longer required.
    * ``cde data list``: List active data packages.
    * ``cde data where``: Print path to data directory.

.. rubric:: Extracting Data

To run ChemDataExtractor on a document, use::

    cde extract <path>

where ``path`` is the path to an input file in HTML, XML or PDF format. This will write the output to the console. It is also possible to specify an output file using the ``-o`` option::

    cde extract <path> -o results.json

This will create a file called ``results.json`` containing the extraction results. Currently, it is only possible to use ChemDataExtractor in its default configuration via the command line interface. For customization, use the Python API.

.. rubric:: Reading Documents

ChemDataExtractor processes each document input into a consistent internal format. To see what this looks like, run::

    cde read <path>

where ``path`` is the path to an input file in HTML, XML or PDF format. This will output a list of document elements.

.. rubric:: Tokenization

The first stage in the natural language processing pipeline is tokenization. First, text is split on sentence boundaries. To run the sentence tokenizer on a document, run::

    cde tokenize sentences <path>

This will output each sentence on a new line.

Each sentence is then split into individual word tokens. To do this, run::

    cde tokenize words <path>

This returns an output with further spaces inserted between each token in each sentence line.

.. rubric:: Part-of-Speech Tagging

ChemDataExtractor contains a part-of-speech (POS) tagger that has been trained specifically for chemistry text::

    cde pos tag <path>

The output consists of tokens followed by a forward slash and then their POS tag.


Regular Expressions
---------------------------

Regular expressions are an important tool in the Natural Language Processing toolbox.
They are special strings that can be used to match sub-strings for the purpose of searching, splitting or grouping text.
Regular expressions appear frequently in ChemDataExtractor, most commonly in the chemical property parsers that will be outlined in the next section.
Below, we provide a number of useful links for information on Regular Expressions.

If you are unfamiliar with Regular Expressions, I recommend going through the `TutorialsPoint Python Regular Expressions tutorial <https://www.tutorialspoint.com/python/python_reg_expressions.htm>`_.

Python contains a useful regular expressions library ``re`` that also contains extensive documentation (https://docs.python.org/3/library/re.html).

Formatting Regular Expressions can be problematic, especially for highly nested groups.
Perhaps the most useful tool for dealing with Regular Expressions is `Debuggex <https://www.debuggex.com>`_ which provides a beautiful graphical interface for debugging regular expressions.

Creating a New Property Parser
------------------------------------

Depending on your specific use case, you will almost definitely need to add new property parsers to ChemDataExtractor in order to retrieve new properties from scientific text/tables.
Here we take you through a simple example of how to create a new parser.

First, we need all the relevant imports::

    from chemdataextractor import Document
    from chemdataextractor.model import Compound
    from chemdataextractor.doc import Paragraph, Heading


Let's create a simple example document with a single heading followed by a single paragraph that contains a boiling point::

    d = Document(
        Heading(u'Synthesis of 2,4,6-trinitrotoluene (3a)'),
        Paragraph(u'The procedure was followed to yield a pale yellow solid (b.p. 240 °C)')
    )

By default, ChemDataExtractor wont extract the ``boiling_point`` property. This can be shown by examining the output records::

    >>> d.records.serialize()
    [{'labels': ['3a'], 'names': ['2,4,6-trinitrotoluene'], 'roles': ['product']}]

So we want to create a *boiling_point* property parser.

.. rubric:: Step 1: Defining a new property model

In ``chemdataextractor.model.py`` you will see all the current property models defined in ChemDataExtractor.
You will also see the ``Compound`` class which contains all properties available for a single compound.
Each property inherits from ``BaseModel`` and can contain fields that can have different types
(``StringType``: a string, ``ModelType``: Another property model, ``ListType``: A list of another type e.g. ``ListType(StringType())`` is a list of strings).

So in ``model.py`` we need to create a ``BoilingPoint`` class and give it some useful fields.
In the most simple case, a boiling point has a unit and a value, both of which are string-type arguments::

    class BoilingPoint(BaseModel):  # Must inherit from BaseModel
    """ A boiling point property"""
        value = StringType()
        units = StringType()

If you look around at other properties, you will see that they can have contextual fields (by setting the ``contextual`` parameter to ``True`` inside the field type).
Setting this parameter means that global contextual information from other elements of the document will be merged into these records.
For example, if your property measurement was performed at a certain temperature, this information could have been given elsewhere in the document
(maybe the experimental method section).
By telling the model that this information is contextual, the temperature of the measurement will be merged with all relevant records.

Next, we need to add our new property to the ``Compound`` class::

    class Compound(BaseModel):
        names = ListType(StringType())
        labels = ListType(StringType())
        roles = ListType(StringType())
        nmr_spectra = ListType(ModelType(NmrSpectrum))
        ir_spectra = ListType(ModelType(IrSpectrum))
        uvvis_spectra = ListType(ModelType(UvvisSpectrum))
        melting_points = ListType(ModelType(MeltingPoint))
        glass_transitions = ListType(ModelType(GlassTransition))
        quantum_yields = ListType(ModelType(QuantumYield))
        fluorescence_lifetimes = ListType(ModelType(FluorescenceLifetime))
        electrochemical_potentials = ListType(ModelType(ElectrochemicalPotential))

        # My new properties
        boiling_points = ListType(ModelType(BoilingPoint))

Note, we make the boiling points have ``ListType`` because a single compound could have multiple boiling points given in the document.

.. rubric:: Step 2: Writing a Parser

Now we need to create the logic that actually extracts boiling points from the text.
Currently, ChemDataExtractor uses nested rules (*grammars*) to extract chemical properties.
These parsers are defined in the ``chemdataextractor.parse`` package.
For example, have a look at the melting point parser in ``chemdataextractor.parse.mp.py``.
This contains a number of statements that are used to define the melting point relationship.

It seems very complicated at first, but let's break the first statement down into its constituent parts::

    prefix = Optional(I('a')).hide() + (Optional(lbrct) + W('Tm') + Optional(rbrct)| R('^m\.?pt?\.?$', re.I) | I('melting') + Optional((I('point') | I('temperature')| I('range'))) | R('^m\.?$', re.I) + R('^pt?\.?$', re.I)).hide() + Optional(lbrct + W('Tm') + rbrct) + Optional(W('=') | I('of') | I('was') | I('is') | I('at')).hide() + Optional(I('in') + I('the') + I('range') + Optional(I('of')) | I('about')).hide()

Here, we have created a variable prefix, that contains the logic for identifying the melting point relationship specifier
(e.g. the text that makes it clear we are talking about a melting point in the text, such "a melting temperature, Tm, ").
The grammar contains several elements, with nested logic. Each token must be assigned an element type, these can be:

    * ``I``: A case insensitive word
    * ``W``: A case sensitive word
    * ``R``: A regular expression rule
    * ``T``: A Part-of-Speech tag

Tokens can be joined using the + symbol, and or logic can be formed using the | symbol.

There are also a number of ``ParseElementEnhance`` classes that can be used, found in the ``chemdataextractor.parse.elements.py`` file:

    * ``Optional``: Matches the contained tokens if they appear, but are not required to form a match
    * ``ZeroOrMore``: Matches any number of the contained tokens
    * ``Any``: Matches any token e.g. ``ZeroOrMore(Any())`` will match the whole of the text
    * ``OneOrMore``: Similar to zero or more, but at least one token is required.
    * ``Not``: Looks ahead to disallow a match

Finally, we note that we can hide elements by adding the ``.hide()`` method.
This means that when the parser creates the relationship tree, the hidden tokens are not used.

Continuing to look at the melting point parser, we see the following line::

    units = (W('°') + Optional(R('^[CFK]\.?$')) | W('K\.?'))('units').add_action(merge)

This will clearly match any temperature unit, and as such we tag the rule as 'units'.
On top of the tags, we can do some post-processing actions to clean up the output.
Here, we add the action ``merge``, which joins all tokens without whitespace (° C becomes °C).
Other actions include:

    * ``join``: Join tokens into a single string with spaces between.
    * ``flatten``: Replace all child results with their text contents.

So now we are able to create our own property parsing rules.
Create a file ``bp.py`` in the parse package.
Some very simple logic for extracting boiling points might be::

    from chemdataextractor.parse import R, I, W, Optional, merge
    from chemdataextractor.parse.base import BaseParser
    from chemdataextractor.utils import first


    prefix = (R(u'^b\.?p\.?$', re.I) | I(u'boiling') + I(u'point')).hide()
    units = (W(u'°') + Optional(R(u'^[CFK]\.?$')))(u'units').add_action(merge)
    value = R(u'^\d+(\.\d+)?$')(u'value')
    bp = (prefix + value + units)(u'bp')


The most important thing to note is that the final phrase (called ``bp``) is now a nested tree, with tags labelling the elements.
If we were to reproduce the XML it would look like:

.. code-block:: html

    <bp>
        <value>R(u'^\d+(\.\d+)?$')</value>
        <units>W(u'°') + Optional(R(u'^[CFK]\.?$'))</units>
    </bp>

Now we have to create the logic for parsing this structure.
In the same file, we create the parser class, that inherits from ``BaseParser``::

    class BpParser(BaseParser):
        root = bp

        def interpret(self, result, start, end):
            compound = Compound(
                boiling_points=[
                    BoilingPoint(
                        value=first(result.xpath('./value/text()')),
                        units=first(result.xpath('./units/text()'))
                    )
                ]
            )
            yield compound

All parser classes must define:

    * A root variable: i.e. the phrase that forms the head of the tree
    * An *interpret* function: That defines the parsing logic

The *interpret* function then creates a new compound (with the model we defined in ``model.py``) and adds a boiling point property.
Here, the result parameter is the result of the parsing process. If a tree with root bp is found, we access the value and unit elements
using `XPath expressions <https://www.w3schools.com/xml/xpath_syntax.asp>`_.

Finally, we need to tell ChemDataExtractor to parse the paragraphs with our new parser.
In ``ChemDataextractor.doc.text`` find the ``Paragraph`` class and add the ``BpParser()`` class to the list of parsers::

    class Paragraph(Text):
        parsers = [..., BpParser()]

.. rubric:: Step 3: Testing the Parser

Now we can simply re-run the document through ChemDataExtractor::

    >>> d = Document(
    >>>     Heading(u'Synthesis of 2,4,6-trinitrotoluene (3a)'),
    >>>     Paragraph(u'The procedure was followed to yield a pale yellow solid (b.p. 240 °C)')
    >>>     )

    >>> d.records.serialize()
    [{'boiling_points': [{'units': '°C', 'value': '240'}],
      'labels': ['3a'],
      'names': ['2,4,6-trinitrotoluene'],
      'roles': ['product']}]

Of course, real world examples are much more complex than this, and a large amount of trial and error is needed to create good parsers.
It should also be noted that in this example, the chemical label ('3a') is found using interdependency resolution between the heading and associated paragraph.
In some cases you will need to put the chemical labels and names directly into the parser.
Rules for chemical entity recognition can be found in ``chemdataextractor.parse.cem.py``.


.. rubric:: Table Parsers

ChemDataExtractor parses tables in a similar way. In ``chemdataextractor.parse.table.py`` you will find the logic for finding chemical relationships from tables.
As an exercise try to write a table parser for the boiling point relationship we just created.
You will need to define a way to find boiling points in table headers, then a parser for the cells.
Available table parsers can be found in ``chemdataextractor.doc.table.py``.


ChemDataExtractor REST API
------------------------------------

A web service for programmatically uploading documents to be processed using ChemDataExtractor on our servers.

All endpoints are at constructed by appending to http://chemdataextractor.org/api




"Where do I find...?"
-----------------------------

The most common questions about ChemDataExtractor usually involve trying to find functionality or asking where best to put new functionality.
Below is a list of the general roles each of the packages perform:

    * ``biblio``: Misc tools for parsing bibliographic information such as bibtex files, author names etc.
    * ``cli``: Command line interfact tools
    * ``doc``: Logic for reading/creating documents. That is, splitting documents down into its various elements.
    * ``nlp``: Tools for performing the NLP stages, such as POS tagging, Word clustering, CNER, Abbreviation detection
    * ``parse``: Chemical property parsers
    * ``Reader``: Document readers
    * ``scrape``: Scrapers for the various data sources
    * ``text``: Useful tools for processing text

If you have new functionality that doesn't fit into one of these categories you may want to create a new sub-package.
Alternatively, if your new functionality is very specific to your own use case, it may be better to have it external to ChemDataExtractor.


Contributing
=================================

Contributions of any kind are greatly appreciated!

.. rubric:: Feedback & Discussion

The `Issue Tracker <https://github.com/CambridgeMolecularEngineering/chemdataextractor/issues>`_ is the best place to post any feature ideas,
requests and bug reports. This way, everyone has the opportunity to keep informed of changes and join the discussion on
future plans.

.. rubric:: Contributing Code

If you are able to contribute changes yourself, just fork the source code on GitHub (https://github.com/CambridgeMolecularEngineering/chemdataextractor),
make changes and file a pull request. All contributions are welcome, no matter how big or small.

The following are especially welcome:

* New document readers for patent formats and the website HTML of scientific publishers.
* Improvements to NLP components - tokenization, tagging and entity recognition.
* Parsers for extracting new compound properties.
* New or improved documentation of existing features.

.. rubric:: Quick Guide to Contributing

1. `Fork the ChemDataExtractor repository on GitHub <https://github.com/CambridgeMolecularEngineering/chemdataextractor/fork>`_, then clone your
   fork to your local machine:

    .. code-block:: bash

        git clone https://github.com/<your-username>/ChemDataExtractor.git

2. Install the development requirements:

    .. code-block:: bash

        cd ChemDataExtractor
        pip install -r requirements/development.txt

3. Create a new branch for your changes:

    .. code-block:: bash

        git checkout -b <name-for-branch>

4. Make your changes or additions. Ideally add some tests and ensure they pass by running:

    .. code-block:: bash

        pytest

   The output should show all tests passing.

5. Commit your changes and push to your fork on GitHub:

    .. code-block:: bash

        git add .
        git commit -m "<description-of-changes>"
        git push origin <name-for-branch>

4. `Submit a pull request <https://github.com/CambridgeMolecularEngineering/chemdataextractor/compare/>`_. Then we can discuss your changes and
   merge them into the main ChemDataExtractor repository.

.. rubric:: Tips

* Follow the `PEP8 <https://www.python.org/dev/peps/pep-0008>`_ style guide.
* Include docstrings as described in `PEP257 <https://www.python.org/dev/peps/pep-0257>`_.
* Try and include tests that cover your changes.
* Try to write `good commit messages <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_.
* Read the GitHub help page on `Using pull requests <https://help.github.com/articles/using-pull-requests>`_.


.. _documenting_code:

Documenting Code
--------------------------------------------------

.. sectionauthor:: Juraj Mavračić

Everyone is encouraged to contribute to documentation in the form of tutorial sections, examples and in any other way
that will improve it.

When you are adding a section of documentation to the ``.rst`` files add you name to it, with:

    .. code-block:: rst

        .. sectionauthor:: My Name <my.name@email.com>

If you are adding documentation in the source code (docstrings and boilerplates), the correct form is:

    .. code-block:: rst

        .. codeauthor:: My Name <my.name@email.com>

All new code should be documented in the docstrings of the appropriate modules, functions an classes, using ``.rst`` format.
In this way, documentation will be automatically created using `Sphinx <http://www.sphinx-doc.org/en/stable/>`_ (see :ref:`source_code_docs`).

.. note:: You can add docstrings for a one-line function/object using ``#:``, preceding the definition. This is
    particularly useful for documenting regular expressions in ``chemdataextractor.parse.cem.py``. For example::

        #: Amino acid abbreviations. His removed, too ambiguous
        amino_acid = R('^((Ala|Arg|Asn|Asp|Cys|Glu|Gln|Gly|Ile|Leu|Lys|Met|Phe|Pro|Ser|Thr|Trp|Tyr|Val)-?)+$')

    will create a correct documentation entry.

If you are adding new modules (.py files) to the codebase, make sure they are included in the documentation (check some of the example files in ``docs/source_code_docs/``.
Most importantly, add an ``.. autosummary::`` to ``code_documentation.rst`` and a file describing all the new content of the module (new classes and functions).

.. note:: Private methods are not included by default in the documentation!
    Functions that are decorated and are not members of a class have to be included into the documentation manually with:

    .. code-block:: rst

        .. autofunction:: decorated_function(parameters)

Additional *tutorial-like* content can be added by hand in the appropriate ``.rst`` files.
When you are writing headers in ``.rst``, use the python convention:

    * ``#`` with overline, for parts
    * ``*`` with overline, for chapters
    * ``=``, for sections
    * ``-``, for subsections
    * ``^``, for subsubsections
    * ``"``, for paragraphs

For highlighted paragraph heading that you don't wish to include into the toctree use ``.. rubric:: My heading``.
Check out the source documentation ``.rst`` files for inspiration on how to use ``.rst`` for code-blocks and other features. *It's made to be very simple!*

Parameters for compiling the html documentation with spinx are:

    * command: ``html``
    * input: ``/chemdataextractor-development/docs``
    * output: ``/chemdataextractor-development/docs/_build/html``
    * options: optionally, use ``-a`` and ``-E`` to build the documentation from scratch.
    * working directory: ``/chemdataextractor-development/docs``

So, in the bash shell, from within the working directory you would use:

    .. code-block:: bash

        $ sphinx-build -b html chemdataextractor-development/docs chemdataextractor-development/docs/_build/html

However, it is encouraged to set up a Sphinx Run configuration in the IDE you are using for development. It is very easy to do in Pycharm,
where you can run sphinx within the same Python virtual environment you are using for the development of ChemDataExtractor.

The ``conf.py`` file is used to set-up internal sphinx parameters. Change it with caution!







































