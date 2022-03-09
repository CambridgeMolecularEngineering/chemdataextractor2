=================================
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

        $ sphinx-build -b html docs docs/_build/html

However, it is encouraged to set up a Sphinx Run configuration in the IDE you are using for development. It is very easy to do in Pycharm,
where you can run sphinx within the same Python virtual environment you are using for the development of ChemDataExtractor.

The ``conf.py`` file is used to set-up internal sphinx parameters. Change it with caution!
