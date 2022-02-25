*********************
Introduction
*********************

.. toctree::
   :maxdepth: 1
   :caption: Learn More:
   :hidden:

   introduction/reading_docs
   introduction/finding_records
   introduction/new_property
   introduction/scraping
   introduction/nlp
   introduction/cli
   introduction/contributing

The ChemDataExtractor Toolkit
=================================

The ChemDataExtractor(CDE) toolkit is an advanced natural language processing pipeline for extracting chemical property
information from the scientific literature. The theory behind the toolkit can be found in the following papers:

Original paper outlining the CDE workflow:

*Swain, M. C., & Cole, J. M. "ChemDataExtractor: A Toolkit for Automated Extraction of Chemical Information from the Scientific Literature", J. Chem. Inf. Model. 2016, 56 (10), pp 1894--1904 10.1021/acs.jcim.6b00207*.

Paper describing the Snowball algorithm:

*Court, C. J., & Cole, J. M. (2018). Auto-generated materials database of Curie and Néel temperatures via semi-supervised relationship extraction. Scientific data, 5, 180111. 10.1038/sdata.2018.111*

Paper describing the enhancements made in CDE 2.0 and TableDataExtractor:

*TO BE ADDED*

Paper describing the new Named Entity Recognition system:

*TO BE ADDED*

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

.. note:: A Python version earlier than 3.8 must be used with ChemDataExtractor.

.. rubric:: Option 1. Using pip

If you already have Python installed, it's easiest to install the ChemDataExtractor package using pip. At the command line, run::

    $ pip install chemdataextractor2

On Windows, this will require the Microsoft Visual C++ Build Tools to be installed. If you don't already have pip installed, you can install it using ``get-pip.py``.

.. rubric:: Option 2. Download the Latest Release

Alternatively, download the latest release manually from github or the ChemDataExtractor website and install it yourself by running::

    $ cd chemdataextractor
    $ python setup.py install

The ``setup.py`` command will install ChemDataExtractor in your site-packages folder so it is automatically available to all your python scripts.

You can also get the latest release by cloning the git source code repository from https://github.com/CambridgeMolecularEngineering/chemdataextractor2/.

.. rubric:: Getting the Data Files

In order to function, ChemDataExtractor requires a variety of data files, such as machine learning models, dictionaries, and word clusters. While previous versions of ChemDataExtractor required you to run a command to download these files, version 2.1 and above will automatically download only those files which are necessary when required by ChemDataExtractor, so you do not need to run any commands to download data. To disable this option, you should set::

    chemdataextractor.data.AUTO_DOWNLOAD = False

To check where the files are and how many files have been downloaded, run::

    $ cde data where


.. rubric:: Updating

Upgrade your installation to the latest version at any time using conda or pip, matching the method you used originally to install it. For conda, run::

    $ conda update -c chemdataextractor chemdataextractor

For pip, run::

    $ pip install --upgrade ChemDataExtractor


"Where do I find...?"
-----------------------------

The most common questions about ChemDataExtractor usually involve trying to find functionality or asking where best to put new functionality.
Below is a list of the general roles each of the packages perform:

    * ``biblio``: Misc tools for parsing bibliographic information such as bibtex files, author names etc.
    * ``cli``: Command line interfact tools
    * ``doc``: Logic for reading/creating documents. That is, splitting documents down into its various elements
    * ``model``: Tools for model representation
    * ``nlp``: Tools for performing the NLP stages, such as POS tagging, Word clustering, CNER, Abbreviation detection
    * ``parse``: Chemical property parsers
    * ``reader``: Document readers
    * ``relex``: Anything related to Snowball
    * ``scrape``: Scrapers for the various data sources
    * ``text``: Useful tools for processing text




































