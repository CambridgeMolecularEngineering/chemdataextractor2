========================
Scraping Structured Data
========================

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
------------

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
