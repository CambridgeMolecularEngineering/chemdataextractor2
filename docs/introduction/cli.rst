=======================
Command Line Interface
=======================

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
