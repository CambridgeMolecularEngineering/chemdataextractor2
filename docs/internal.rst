******************************************
New Group Members
******************************************

.. contents::

.. _section_contributing_code:

Contributing Your Code
=================================

The current stable release (version 2.0.0) can be found at https://github.com/CambridgeMolecularEngineering/chemdataextractor.git.

As you are joining the Molecular Engineering Group to work with ChemDataExtractor,
you will almost certainly need to make a number of changes to the source code for your particular use case.
To do this, all developers have their own development branch of the
private `chemdataextractor-development <https://github.com/CambridgeMolecularEngineering/chemdataextractor-development.git>`_ repository.
Please note that the development repository is private. This is so that your work is not made available in advance of any publications and
so that our group-wide API Keys are not made publically available. Making your work publically available may prevent you
from publishing your work at a later date.

You will need to have your own github account. Go to `GitHub <https://github.com>`_ and set up an account if you do not
already have one.
We also recommend signing up for the `Github Student Pack <https://education.github.com/pack>`_ in order to get unlimited
private repositories, simply sign up with your *@cam* email address.

Next, contact either Callum Court (cc889@cam.ac.uk) or Ed Beard (ejb207@cam.ac.uk) with your github username requesting a development branch on the private repository.
You will then be confirmed as a collaborator on the project, enabling you to create a development branch.
You will also be invited to join the discussion on the
`ChemDataExtractor Developers Slack group <https://chemdataextractor-dev.slack.com>`_, this is a forum for all developers of ChemDataExtractor to discuss upcoming meetings,
functionality ideas and general performance enhancements.

Cloning the Repository
-------------------------

Once your github account is marked as a collaborator on the project, you will be able to clone the private repository to your local machine::

    $ git clone https://github.com/CambridgeMolecularEngineering/chemdataextractor-development.git


Creating a Development Branch
----------------------------------

To create a new branch `cd` into the `chemdataextractor-development` folder and type::

    $ git checkout -b [name_of_your_new_branch]

.. note:: As a general standard, please ensure your branch name is your CRSID, in all lower case. Any extra branches not obeying this rule could be removed without warning.

Next you can switch to work on your new branch::

    $ git checkout [name_of_your_new_branch]

Then push the branch on github::

    $ git push origin [name_of_your_new_branch]

You are now able to edit the source and commit/push to your local branch as you please.

Pushing to Master
-------------------------

We encourage you to push your code to master whenever you make material changes to your code.
This helps to ensure that the development branches never become too disimilar from the master.
All new code should be fully tested and documented in line with the testing and style guidelines outlined in the following sections.


Testing
--------------

Tests are small scripts written to ensure that a new bit of code is behaving as it should.
It's very common for someone to add a few lines to one part of some software, only for it to unexpectedly break some functionality elsewhere in the code.
The inclusion of automated tests helps you to find these cases early and drastically reduce the time spent troubleshooting. Tests can broadly be broken down into two categories:

    1. **Unit Tests**: Independent code snippets that test one feature of your software
    2. **System Tests**: End-to-end or larger tests that check the whole software pipeline


.. rubric:: Unit Tests

ChemDataExtactor Unit Tests are built using the `python unittest <https://docs.python.org/2/library/unittest.html>`_ package.

Whilst writing new functionality, you should create a class for each function to be tested which should inherit from  `unittest.TestCase`,
and populate this class with test functions. Each function should test a specific aspect of the code, and should be subdivided into 3 sections:

    1. Declaration: Initialising the input and the expected output.
    2. Testing: Running the input through the software to get the test output.
    3. Assertion: Check or ``assert()`` that the test output is the same as the expected output.

For example, let's test the melting point parser in ``chemdataextractor.parse.mp.py``::

    import unittest
    from lxml import etree

    from chemdataextractor.doc.text import Sentence, Paragraph
    from chemdataextractor.parse.mp import mp_phrase

    class TestParseMp(unittest.TestCase):
        def test_mp1(self):

            # Declaration
        s = Sentence('Colorless solid (81% yield, 74.8 mg, 0.22 mmol); mp 77.2â-77.5 Â°C.')
        expected = '<mp_phrase><mp><value>77.2-77.5</value><units>Â°C</units></mp></mp_phrase>'

        # Testing
        result = next(mp_phrase.scan(s.tagged_tokens))[0]

        #Assertion
        self.assertEqual(expected, etree.tostring(result, encoding='unicode'))

Here you can see `s` is declared as the input sentence object.
`expected` is a string representation of the anticipated XML output.
The input is then fed into the function to be tested, `mp_phrase`,
and the output of this checked against `expected` using the `assertEqual()` function.
Assert functions are used by `unittest` to determine whether a test has passed or failed - `assertEqual()` passes a test when it's two arguments are the same,
but there is a whole suite of them that are worth checking out.

Note this is just one simple test of the function.
You should include multiple different tests, with many different cases to prove that the function works as expected.

.. warning:: One single test of a simple case is not enough for your code to pass through the code review.

.. rubric::  System Tests

System tests are used to check the entire software pipeline is behaving correctly for specific examples.
They can be useful for identifying things overlooked by the unit tests, or bugs that occur when different units of the software interface with each other.
You should only really need to write them when you want to check how your code interacts with something else, or if you find a different example that hasn't already been included in a whole-system test.
System tests can be longer and require larger processing power than unit tests, but also don't need to be run as frequently - just running them before a major commit will be enough in most cases.

.. rubric:: Submitting and Running Your Tests

As outlined in the :ref:`section_contributing_code` section, whenever you have completed a new section of code,
or updated the functionality of old code, you can create a pull request asking for this code to be made permanent on the master branch.
All tests will automatically be run on any code uploaded to GitHub.
Your pull requests to the master will only be merged once all of these have passed.
This includes any new tests, which must be provided alongside the new code.
If the tests pass, and the code reviewer has no comments or change requests, your code will be merged.

.. note:: Passing all tests is not the only requirement for new commits to be successfull merged, your code must also follow the :ref:`section_style_guidelines`.

You should thoroughly check that your code is ready to be committed by running all tests in advance.
It is quicker for you, and the code reviewer, to complete pull requests if you have tested your code in advance.

You can perform tests using the `PyTest <https://docs.pytest.org/en/latest/>`_ package. To install it, run::

  $ pip install -U pytest

Then simply ``cd`` into the folder you wish to test. and in the command line and run `$ pytest`. All tests beginning with the prefix 'test' in their filename will be run.
Alternatively if you're using the PyCharm IDE, you can run tests individually inside your working environment.

As of ChemDataExtractor 2.1, there are a few deprecated APIs that are heavily called within the tests. It can get annoying to have lots of warnings in the tests, so we recommend running pytest with the option ``-W ignore::DeprecationWarning`` to ignore the deprecation warnings. These tests will be rewritten in the future, when these features are removed, but are still included now as they ensure that even the deprecated APIs function correctly.

As we are all very busy, it may take some time for pull requests to be fully merged.


.. rubric:: Conventions

For this project each file in `chemdataextractor` should be partnered with an appropriate test file in the `chemdataextractor.tests` folder.
Make sure the name of each file follows the format ``test_<cdedirectory>_<cdefile>.py``, to emulate the file structure used in the main
body of code - this makes it easier to troubleshoot where in the code something has gone wrong when a test fails.
There should be separate folders for unit tests and system tests.

.. note:: **Testing Tips!**

    * The *golden rule* of testing is **put time in now, save time later**.
        Well tested code makes the debugging process much more bearable and can give you reassurance that your code is doing what it's supposed to.

    * Where possible write tests in parallel with your code development.
        This makes it a lot easier to cover all potential problems at the time when you encounter them. It also makes it more likely that your code will be accepted.

Documentation
---------------------

You are expected to contribute to the documentation of the code.
As a minimum, you will have to document all the functionality you are adding to the code, as explained in :ref:`documenting_code`.
This will mainly include writing adequate :ref:`docstrings` and :ref:`boilerplates` that will be automatically included into generated `html` documentation using Sphinx.
Write the docstrings and boilerplates in ``rst`` language, for best visual appearance in the documentation.

Modify the appropriate ``.rst`` files to ensure that your code shows up in the documentation.



.. _section_style_guidelines:

Style Guidelines
---------------------

In general, please try to follow the `PEP8 style guide <https://www.python.org/dev/peps/pep-0008/>`_, but the most important rule is **BE CONSISTENT**.
It makes it much easier for everyone reading your code to follow along if it is consistently formatted and well documented.
It will also be easier for you to come back to old code if you followed these guidelines from the beginning.
Therefore, please try to do documentation and testing as you go, rather than at the end of a development cycle.
Of course, there are always cases where the style guide has not been followed.
If you find these cases, then you are very welcome to reformat the code and submit a pull-request outlining the changes.
If you have a particular reason for not following the guidelines, you must provide an explanation in the code review stage.

.. _boilerplates:

.. rubric:: Boilerplates

At the start of each new file you create within `chemdataextractor`, please place the following boilerplate::

    # -*- coding: utf-8 -*-
    """
    <File description>  # e.g. Generic boilerplate example

    .. codeauthor:: name <email>  # e.g. ..codeauthor:: Callum Court <cc889@cam.ac.uk>

    """

Use the ``rst`` language for more sophisticated descriptions and usage examples. This will be automatically included in the documentation.

.. _docstrings:

.. rubric::  Docstrings

At the bare minimum, all functions should have a docstring containing:
    * A short description of the functionality
    * Input parameters, if applicable
    * Any outputs
    * Any exceptions thrown

An example might be::

    def from_string(self, fstring, fname=None, readers=None):
            """
            Create a Document from a byte string containing the contents of a file.

            Usage::

                contents = open('paper.html', 'rb').read()
                doc = Document.from_string(contents)

            .. note::

                This method expects a byte string, not a unicode string (in contrast to most methods in ChemDataExtractor).

            :param bytes fstring: A byte string containing the contents of a file.
            :param string fname: (Optional) The filename. Used to help determine file format.
            :param list[chemdataextractor.reader.base.BaseReader] readers: (Optional) List of readers to use.

            :raises: ReaderError: If specified readers are not found

            .. codeauthor:: Callum Court <cc889@cam.ac.uk>

            """

Other information, such as a usage example or helpful notes are encouraged, since they will be automatically added to documentation.
Use the ``rst`` language to add whatever you find useful.

There is no limit to function length. However, if you find functions becoming very big then it may be best to try and break it down into smaller units.

.. warning:: For your code to be added to the master branch a minimum of documentation will be required:

    * **boilerplates and docstrings** for new modules, functions and classes, containing enough information for someone else to use your code and to understand the purpose of the new modules/functions/classes
    * the new modules, functions and classes have to be **visible in the html documentation**


.. rubric:: Linting

A good practice to ensure your code is correctly formatted is to run `PyLint <https://www.pylint.org>`_ over your code and check that no warnings or errors are returned.
There are also a number of useful auto-formatters for the PEP8 style guide, such as `autopep8 <https://github.com/hhatto/autopep8>`_ or `yapf <https://github.com/google/yapf#installation>`_
(Note that yapf follows the google python style guide by default).
These tools can be configured to run automatically when new updates are applied.


Web-Scraping
=================================

The codebase contains scrapers that retrieve structured information from the webpages of the RSC, ACS, UPSTO, Elsevier, Wiley and Springer.
Most projects require ChemDataExtractor to be run on a very large corpus of papers, and as such, web-scraping tools must be used to source a relevant dataset.
You will also find that some scrapers are not provided as standard within the source code. This is because some journals require us to have a group-specific API Key.
If you require access to one of these publishers, please contact Callum Court (cc889), Ed Beard (ejb207) or Dr. Jacqui Cole (jmc61) and we will give you the neccessary access.

.. note:: At the current time, we ask students not to perform any web-scraping of the ACS webpages. Doing so will result in the entire local network being barred from accessing the ACS

Creating a new scraper
---------------------------------

In general, is good practice to try and create a web scraper yourself.
As this gives you a deeper understanding of how the scrape package works. Here are some general guidelines.

There are typically two stages in the web-scraping process:

    1. Finding the DOIs of relevant articles
    2. Retrieving HTML or XML versions of those files

Finding a relevant set of DOIs can be done in two main ways:

.. rubric:: 1. Query based searching

In this method you submit keywords to the publishers and get all the DOIs returned from their search platform.
For example, to use ChemDataExtractor to query the RSC search pages, you might use something similar to::

    from chemdataextractor.scrape.pub.rsc import RscSearchScraper()

    query_text = "Aspirin"
    scrape = RscSearchScraper().run(query_text)
    results = scrape.serialize()  # JSON style search results

    articles = results["articles"]
    for article in articles:
        print(article["doi"])

.. rubric:: 2. Entire Journal searching

You may instead be interested in searching papers from an entire journal.
To retrieve DOIs for a known journal the best option is to use the `CrossRef API <https://github.com/fabiobatalha/crossrefapi>`_::

    from crossref.restful import Works

    journal_title = 'Physica B: Condensed Matter'
    prefix = '10.1016'. # Elsevier
    save_file_name = 'physb_dois.txt'

    # create the works object
    works = Works()
    w1 = works.query()

    # Filter the results
    w1 = w1.filter(prefix=prefix, container_title=journal_title)

    print("Total results: %s" % str(w1.count()))

    # Save dois to file
    with open(save_file_name, 'w') as f:
    for idx, item in enumerate(w1):
        doi = item['DOI']
        print(idx, doi)
        f.write('https://api.elsevier.com/content/article/doi/' + doi + '\n')

To the download the HTML articles we can simply use the `requests package <http://docs.python-requests.org/en/master/>`_ to retrieve the files via their URL.

Each journal/publisher is different, and so you will likely have to write multiple different tools to get papers from multiple sources.

Getting Help
==================

If you are completely lost or have a seemingly unsolvable problem with ChemDataExtractor,
first post in the `Slack developers group <https://chemdataextractor-dev.slack.com>`_, and someone else will try to help you with your problem.
If you find a bug that needs to be fixed, please mark the bug as an issue on the Github repository.
