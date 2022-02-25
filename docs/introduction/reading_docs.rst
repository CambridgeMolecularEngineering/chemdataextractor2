=================================
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

ChemDataExtractor will only find records for models that you are interested in, so you should first set the type of records you want::

    >>> doc.models = [Compound]

You can then call the *records* method, which combines all the chemical mentions, abbreviations and properties found each chemical entity (see :ref:`examples`).

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
