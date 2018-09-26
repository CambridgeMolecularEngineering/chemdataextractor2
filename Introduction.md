# An introduction to developing with ChemDataExtractor

This document is intended for new students joining the Molecular Engineering Group intending to make use of the ChemDataExtractor toolkit. The sections below provide general advice for using and adapting the toolkit, as well guidelines for contributing to the codebase.

Contents:

1.  [The ChemDataExtractor Toolkit](#1-the-chemdataextractor-toolkit)
1.  [Getting started](#2-getting-started)
    1. [Installation](#21-installation)
    1. [Reading a Document](#22-reading-a-document)
1. [Contributing](#3-contributing-your-code)
    1. [Cloning the Repository](#31-cloning-the-repository)
    1. [Creating a Development Branch](#32-creating-a-development-branch)
    1. [Pushing to Master](#33-pushing-to-master)
1. [Testing](#4-testing)
    1. [Unit Tests](#41-unit-tests)
    1. [System Tests](#42-system-tests)
    1. [Submitting and Running Your Tests](#43-submitting-and-running-your-tests)
    1. [Conventions](#44-conventions)
    1. [Testing Tips](#45-testing-tips)
1. [Style Guidelines](#5-style-guidelines)
1. [Advanced Topics](#6-advanced-topics)
    1. [IDE's or the Command Line](#61-ides-or-the-command-line)
    1. [Web-Scraping](#62-web-scraping)
    1. [Document Readers](#63-document-readers)
    1. [Regular Expressions](#64-regular-expressions)
    1. [Creating a New Property Parser](#65-creating-a-new-property-parser)
    1. ["Where Do I Find...?"](#66-where-do-i-find)
    1. [Getting Help](#67-getting-help)
    

## 1. The ChemDataExtractor Toolkit

The ChemDataExtractor toolkit is an advanced natural language processing pipeline for extracting chemical property information from the scientific literature. A full description of the theory behind the toolkit can be found in the original paper: 

*Swain, M. C., & Cole, J. M. "ChemDataExtractor: A Toolkit for Automated Extraction of Chemical Information from the Scientific Literature",
J. Chem. Inf. Model. 2016, 56 (10), pp 1894--1904 10.1021/acs.jcim.6b00207*.

and the associated website [chemdataextractor.org](https://chemdataextractor.org).

The general process for extracting information from scientific text is as follows:

1. Break a document down into its consituent elements (Title, Paragraphs, Sentences, Tables, Figures...)
2. Tokenize the text to isolate individual tokens
3. Apply Part-of-speech tagging to identify the semantic role of each token
4. Detect Chemical Named Entites using machine learning
5. Parse text and tables with nested rules to identify chemical relationships
6. Resolve the interdependencies between the different elements
7. Output a set of mutually consistent chemical records

This pipeline enables ChemDataExtractor to extract chemical information in a completely domain-independent manner.


## 2. Getting Started
This section outlines the basic installation instructions for ChemDataExtractor. Full documentation can be found [here](https://chemdataextractor.org/documentation).

### 2.1 Installation
To get up and running with ChemDataExtractor, you will need to install the python toolkit and then download the neccessary data files.
There are a few different ways to download and install the ChemDataExtractor toolkit.

**Option 1: Using conda**

This method is recommended for all Windows users, as well as beginners on all platforms who don't already have Python installed. Anaconda Python is a self-contained Python environment that is particularly useful for scientific applications.

Start by installing [Miniconda](https://conda.io/miniconda.html), which includes a complete Python distribution and the conda package manager, or Anaconda, which additionally includes many pre-installed packages, including NumPy and Matplotlib. Choose the Python 3.5 version, unless you have a particular reason why you must use Python 2.7.

Once installed, at the command line, run:

```$ conda install -c chemdataextractor chemdataextractor```

This command installs the chemdataextractor package from the chemdataextractor conda channel.

**Option 2: Using pip**

If you already have Python installed, it's easiest to install the ChemDataExtractor package using pip. At the command line, run:

```$ pip install ChemDataExtractor```

On Windows, this will require the Microsoft Visual C++ Build Tools to be installed. If you don't already have pip installed, you can install it using get-pip.py.

**Option 3: Download the Latest Release**

Alternatively, download the latest release manually from github or the ChemDataExtractor website and install it yourself by running:

```$ cd chemdataextractor
$ python setup.py install
```

The setup.py command will install ChemDataExtractor in your site-packages folder so it is automatically available to all your python scripts.

You can also get the unstable development version by cloning the git source code repository from [here](https://github.com/mcs07/chemdataextractor.git).

**Getting the Data Files**

In order to function, ChemDataExtractor requires a variety of data files, such as machine learning models, dictionaries, and word clusters. Get these by running:

```$ cde data download```

This will download all the necessary data files to the data directory. Run 

```$ cde data where``` 

to see where this is.

**Updating**

Upgrade your installation to the latest version at any time using conda or pip, matching the method you used originally to install it. For conda, run:

```$ conda update -c chemdataextractor chemdataextractor```

For pip, run:

```$ pip install --upgrade ChemDataExtractor```

Either way, always remember to download any new data files after doing this:

```$ cde data download```

### 2.2 Reading a Document

Most commonly, you want to pass an entire document file to ChemDataExtractor. ChemDataExtractor comes with a number of built-in Document readers that can read HTML, PDF and XML files. These readers are responsible for detecting the different elements of a document and recompiling them into a single consistent document structure.

```python
>>> f = open('paper.html', 'rb')
>>> doc = Document.from_file(f)
```

Each reader will be tried in turn until one is successfully able to read the file. If you know exactly which readers you want to use, it is possible to specify a list as an optional parameter:

```python
>>> f = open('rsc_article.html', 'rb')
>>> doc = Document.from_file(f, readers=[RscHtmlReader()])
```

**Note: Always open files in binary mode by using the 'rb' parameter.**

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

More information about document readers can be found in the [Advanced Topics](#6-advanced-topics)

**Document Elements**

Once read, documents are represented by a single linear stream of `element` objects. This stream is now independent of the initial document type or the source.

```python
>>> doc.elements
[Title('A very important scientific article'),
 Heading('Abstract'),
 Paragraph('The first paragraph of text...'),
 ...]
 ```
 
Element types include Title, Heading, Paragraph, Citation, Table, Figure, Caption and Footnote. You can retrieve a specific element by its index within the document:

```python
>>> para = doc.elements[14]
>>> para
Paragraph('1,4-Dibromoanthracene was prepared from 1,4-diaminoanthraquinone. 1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.')
```

You can also get the individual sentences of a paragraph:

```python
>>> para.sentences
[Sentence('1,4-Dibromoanthracene was prepared from 1,4-diaminoanthraquinone.', 0, 65),
 Sentence('1H NMR spectra were recorded on a 300 MHz BRUKER DPX300 spectrometer.', 66, 135)]
 ```
 
Or the individual tokens:

```python
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
```

**Which file formats are best?**

While ChemDataExtractor supports documents in a wide variety of formats, some are better suited for extraction than others. If there is an HTML or XML version available, that is normally the best choice.

Wherever possible, avoid using the PDF version of a paper or patent. At best, the text will be interpretable, but it is extremely difficult to reliably distinguish between headings, captions and main body text. At worst, the document will just consist of a scanned image of each page, and it won't be possible to extract any of the text at all. You can get some idea of what ChemDataExtractor can see in a PDF by looking at the result of copying-and-pasting from the document.

For scientific articles, most publishers offer a HTML version alongside the PDF version. Normally, this will open as a page in your web browser. Just choose "Save As..." and ensure the selected format is "HTML" or "Page Source" to save a copy of the HTML file to your computer.

Most patent offices provide XML versions of their patent documents, but these can be hard to find. Two useful resources are the USPTO Bulk Data Download Service and the EPO Open Patent Services API.

**More information**
The [Advanced Topics](#6-advanced-topics) section provides more detailed instructions for advanced ChemDataExtractor functionality.

## 3. Contributing Your Code
The current stable release (version 1.3.0) can be found [here](https://github.com/CambridgeMolecularEngineering/chemdataextractor.git).
As you are joining the Molecular Engineering Group to work with ChemDataExtractor, you will almost certainly need to make a number of changes to the source code for your particular use case. To do this, all developers have their own development branch of the private [chemdataextractor-development](https://github.com/CambridgeMolecularEngineering/chemdataextractor-development.git) repository. Please note that the development repository is private. This is so that your work is not made available in advance of any publications and so that our group-wide API Keys are not made publically available. Making your work publically available may prevent you from publishing your work at a later date.

You will need to have your own github account. Go to [GitHub](https://github.com) and set up an account if you do not already have one. We also recommend signing up for the [Github Student Pack](https://education.github.com/pack) in order to get unlimited private repositories, simply sign up with your *@cam* email address.

Next, contact either Callum Court (cc889@cam.ac.uk) or Ed Beard (ejb207@cam.ac.uk) with your github username requesting a development branch on the private repository. You will then be confirmed as a collaborator on the project, enabling you to create a development branch. You will also be invited to join the discussion on the ChemDataExtractor Developers [Slack group](https://chemdataextractor-dev.slack.com), this is a forum for all developers of ChemDataExtractor to discuss upcoming meetings, functionality ideas and general performance enhancements. 

### 3.1 Cloning the Repository

Once your github account is marked as a collaborator on the project, you will be able to clone the private repository to your local machine.

```$ git clone https://github.com/CambridgeMolecularEngineering/chemdataextractor-development.git```

### 3.2 Creating a Development Branch

To create a new branch `cd` into the `chemdataextractor-development` folder and type:

```$ git checkout -b [name_of_your_new_branch]```

**NOTE: As a general standard, please ensure your branch name is your CRSID, in all lower case. Any extra branches not obeying this rule could be removed without warning.**

Next you can switch to work on your new branch:

```$ git checkout [name_of_your_new_branch]```

Then push the branch on github:

```$ git push origin [name_of_your_new_branch]```

You are now able to edit the source and commit/push to your local branch as you please.

### 3.3 Pushing to Master
We encourage you to push your code to master whenever you make material changes to your code. This helps to ensure that the development branches never become too disimilar from the master. All new code should be fully tested and documented in line with the testing and style guidelines outlined in the following sections.

## 4. Testing
Tests are small scripts written to ensure that a new bit of code is behaving as it should. It's very common for someone to add a few lines to one part of some software, only for it to unexpectedly break some functionality elsewhere in the code. The inclusion of automated tests helps you to find these cases early and drastically reduce the time spent troubleshooting. Tests can broadly be broken down into two categories:

1. ```Unit Tests``` : Independent code snippets that test one feature of your software
2.  ``` System Tests```: End-to-end or larger tests that check the whole software pipeline

### 4.1 Unit Tests
ChemDataExtactor Unit Tests are built using the python [unittest](https://docs.python.org/2/library/unittest.html) package. 

Whilst writing new functionality, you should create a class for each function to be tested which should inherit from  `unittest.TestCase`, and populate this class with test functions. Each function should test a specific aspect of the code, and should be subdivided into 3 sections :

1. Declaration : Initialising the input and the expected output.
2. Testing : Running the input through the software to get the test output.
3. Assertion: Check or ```assert()``` that the test output is the same as the expected output.

For example, let's test the melting point parser in ```chemdataextractor.parse.mp.py```:

```python 
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
  ```
Here you can see `s` is declared as the input sentence object. `expected` is a string representation of the anticipated XML output. The input is then fed into the function to be tested, `mp_phrase`, and the output of this checked against `expected` using the `assertEqual()` function. Assert functions are used by `unittest` to determine whether a test has passed or failed - `assertEqual()` passes a test when it's two arguments are the same, but there is a whole suite of them that are worth checking out.

Note this is just one simple test of the function. You should include multiple different tests, with many different cases to prove that the function works as expected. **One single test of a simple case is not enough for your code to pass through the code review.**

### 4.2 System Tests 
System tests are used to check the entire software pipeline is behaving correctly for specific examples. They can be useful for identifying things overlooked by the unit tests, or bugs that occur when different units of the software interface with each other. You should only really need to write them when you want to check how your code interacts with something else, or if you find a different example that hasn't already been included in a whole-system test. System tests can be longer and require larger processing power than unit tests, but also don't need to be run as frequently - just running them before a major commit will be enough in most cases. 

### 4.3 Submitting and Running Your Tests
As outlined in the [Contributing](#3-contributing-your-code) section, whenever you have completed a new section of code, or updated the functionality of old code, you can create a pull request asking for this code to be made permanent on the master branch. 
All tests will automatically be run on any code uploaded to GitHub. Your pull requests to the master will only be merged once all of these have passed. This includes any new tests, which must be provided alongside the new code. If the tests pass, and the code reviewer has no comments or change requests, your code will be merged. 

**NOTE: Passing all tests is not the only requirement for new commits to be successfull merged, your code must also follow the [Style Guidelines](#5-style-guidelines)**

You should thoroughly check that your code is ready to be committed by running all tests in advance. It is quicker for you, and the code reviewer, to complete pull requests if you have tested your code in advance. 

You can perform tests using the [PyTest](https://docs.pytest.org/en/latest/) package. To install it, run:
 
  ```$ pip install -U pytest```
  
Then simply ``cd`` into the folder you wish to test. and in the command line and run `$ pytest`. All tests beginning with the prefix 'test' in their filename will be run. Alternatively if you're using the PyCharm IDE, you can run tests individually inside your working environment.

As we are all very busy, it may take some time for pull requests to be fully merged.

### 4.4 Conventions
For this project each file in `chemdataextractor` should be partnered with an appropriate test file in the `chemdataextractor.tests` folder. Make sure the name of each file follows the format ``` test_<cdedirectory>_<cdefile>.py```, to emulate the file structure used in the main body of code - this makes it easier to troubleshoot where in the code something has gone wrong when a test fails. There should be separate folders for unit tests and system tests.

### 4.5 Testing Tips!
* The _golden rule_ of testing is **put time in now,  save time later**. 
Well tested code makes the debugging process much more bearable and can give you reassurance that your code is doing what it's supposed to. 

* Where possible write tests in parallel with your code development.
This makes it a lot easier to cover all potential problems at the time when you encounter them. It also makes it more likely that your code will be accepted.


## 5. Style Guidelines
In general, please try to follow the [PEP8 style guide](https://www.python.org/dev/peps/pep-0008/), but the most important rule is **BE CONSISTENT**. It makes it much easier for everyone reading your code to follow along if it is consistently formatted and well documented. It will also be easier for you to come back to old code if you followed these guidelines from the beginning. Therefore, please try to do documentation and testing as you go, rather than at the end of a development cycle. Of course, there are always cases where the style guide has not been followed. If you find these cases, then you are very welcome to reformat the code and submit a pull-request outlining the changes. If you have a particular reason for not following the guidelines, you must provide an explanation in the code review stage. 

## 5.1 Boilerplate
At the start of each new file you create within `chemdataextractor`, please place the following boilerplate:

```python
# -*- coding: utf-8 -*-
"""
<file location>  # e.g. chemdataextractor.my_package.my_file.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

<File description>.  # e.g. Generic boilerplate example

<Author>(<email>). # e.g. Callum Court (cc889@cam.ac.uk)

"""
```

## 5.2 Docstrings
At the bare minimum, all functions should have a docstring containing:
* A short description of the functionality
* Input parameters, if applicable
* Any outputs
* Any exceptions thrown

A good example might be:

```python
def from_string(self, fstring, fname=None, readers=None):
        """Create a Document from a byte string containing the contents of a file.

        Usage::

            contents = open('paper.html', 'rb').read()
            doc = Document.from_string(contents)

        .. note::

            This method expects a byte string, not a unicode string (in contrast to most methods in ChemDataExtractor).

        :param bytes fstring: A byte string containing the contents of a file.
        :param string fname: (Optional) The filename. Used to help determine file format.
        :param list[chemdataextractor.reader.base.BaseReader] readers: (Optional) List of readers to use.
        
        :raises: ReaderError: If specified readers are not found
        """
```
Other information, such as a usage example or helpful notes are encouraged.

There is no limit to function length. However, if you find functions becoming very big then it may be best to try and break it down into smaller units.

## 5.3 Linting
A good practice to ensure your code is correctly formatted is to run [PyLint](https://www.pylint.org) over your code and check that no warnings or errors are returned. There are also a number of useful auto-formatters for the PEP8 style guide, such as [autopep8](https://github.com/hhatto/autopep8) or [yapf](https://github.com/google/yapf#installation) (Note that yapf follows the google python style guide by default). These tools can be configured to run automatically when new updates are applied.

## 6. Advanced Topics

This section provides an overview of some more complex ChemDataExtractor functionality. It also aims to solve common problems encountered when new to the ChemDataExtractor interface.

## 6.1 IDE's or the Command Line
If you prefer programming in via command line, ChemDataExtractor has a neat command line interface, found in the ```chemdataextractor.cli``` package. 

Most commonly, new developers tend to use Integrated Development Environments (IDEs) for python programming. There are many choices of IDE to chose from. The most commonly used in the group is [PyCharm](https://www.jetbrains.com/pycharm/). PyCharm has thousands of useful plugins that will make your development process easier. Including plugins for autoformatting your code to the style guidelines, a powerful debugger and automated git integration. JetBrains also provide free premium subscriptions for students, giving you access to other useful tools.

If you prefer to use a text editor and run your code via the command line then a good alternative option is [Visual Studio Code](https://code.visualstudio.com) from Microsoft. It has all the functionality of Microsoft Visual Studio and many useful extensions.


## 6.2 Web-Scraping
As outlined in the ChemDataExtractor [documentation](http://chemdataextractor.org/docs/scrape), the codebase contains scrapers that retrieve structured information from the webpages of the RSC, ACS, UPSTO, Elsevier, Wiley and Springer. Most projects require ChemDataExtractor to be run on a very large corpus of papers, and as such, web-scraping tools must be used to source a relevant dataset. You will also find that some scrapers are not provided as standard within the source code. This is because some journals require us to have a group-specific API Key. If you require access to one of these publishers, please contact Callum Court (cc889), Ed Beard (ejb207) or Dr. Jacqui Cole (jmc61) and we will give you the neccessary access.

**NOTE: At the current time, we ask students not to perform any web-scraping of the ACS webpages. Doing so will result in the entire local network being barred from accessing the ACS**

**Creating a new scraper**

In general, is good practice to try and create a web scraper yourself. As this gives you a deeper understanding of how the scrape package works. Here are some general guidelines.

There are typically two stages in the web-scraping process:

1. Finding the DOIs of relevant articles
2. Retrieving HTML or XML versions of those files

Finding a relevant set of DOIs can be done in two main ways:

**Query based searching**

In this method you submit keywords to the publishers and get all the DOIs returned from their search platform. For example, to use ChemDataExtractor to query the RSC search pages, you might use something similar to:

```python
from chemdataextractor.scrape.pub.rsc import RscSearchScraper()

query_text = "Aspirin"
scrape = RscSearchScraper().run(query_text)
results = scrape.serialize()  # JSON style search results

articles = results["articles"]
for article in articles:
    print(article["doi"])
```

**Entire Journal searching**

You may instead be interested in searching papers from an entire journal. To retrieve DOIs for a known journal the best option is to use the [CrossRef API](https://github.com/fabiobatalha/crossrefapi).

```python
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
```

To the download the HTML articles we can simply use the [requests](http://docs.python-requests.org/en/master/) package to retrieve the files via their URL. 

Each journal / publisher is different, and so you will likely have to write multiple different tools to get papers from multiple sources.

## 6.3 Document Readers

The document readers present in the ```chemdataextractor.reader``` package are a set of tools for identifying the elements of scientific docucments. The HTML and XML from each publisher is slightly different, meaning we once again need multiple different readers. New users are often confused about the structure of these readers, and so this section attempts to explain their functionality more clearly. 

As an example, lets look at the ```chemdataextractor.reader.rsc.RscHtmlReader``` class.

```python 
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
```

As you can see, we have a number of [CSS Selectors](https://www.w3schools.com/css/css_intro.asp) that are used to select particular elements from an RSC HTML document. Here, the variable names are important, and must follow the format ```<element_name>_css```, as this tells the `BaseReader` what to name the selected element.

These elements are found by examining the HTML. For example, if you find a paper from the RSC web pages, open the HTML version, then right-click and chose "view page source" you will be able to see the raw HTML. If you are unfamiliar with HTML and CSS I recommend going through the [TutorialsPoint HTML tutorial](https://www.tutorialspoint.com/html/) and [CSS tutorial](https://www.tutorialspoint.com/css/).

It should also be mentioned that these Readers override the element variables from the base ```HTMLReader``` class. Similarly, if you want to analyse an XML document, you should override from the ```XMLReader``` class. I first recommend using the base readers, to see how they perform, then write a new reader if you have to.

**Cleaners**

You will see in the above code that we have specified a number of cleaners. Cleaners attempt to fix systematic formatting errors in the HTML/XML. A classic problem is spacing around references. For example some HTML may look like:

```HTML
<div>
	<p>This is a result that was retrieved from
		<a><sup><span class=sup_ref>[1]</span><sup></a>.
	</p>
</div>                                                                                              
```
When parsing, ChemDataExtractor will output:

```Paragraph(text='This a result that was retrieved from[1].',...)```

So we need a cleaner whose job is to put a space between text and references. In the `RscHtmlReader` class we specify a list of cleaners to act on the text.

```cleaners = [clean, replace_rsc_img_chars, space_references]```

and the corresponding `space_references` cleaner looks like:

```python
def space_references(document):
    """Ensure a space around reference links, so there's a gap when they are removed."""
    for ref in document.xpath('.//a/sup/span[@class="sup_ref"]'):
        a = ref.getparent().getparent()
        if a is not None:
            atail = a.tail or ''
            if not atail.startswith(')') and not atail.startswith(',') and not atail.startswith(' '):
                a.tail = ' ' + atail
    return document
```
Note that we don't explictly need to call the cleaner as this is handled by the `BaseReader` class.

## 6.4 Regular Expressions
Regular expressions are an important tool in the Natural Language Processing toolbox. They are special strings that can be used to match sub-strings for the purpose of searching, splitting or grouping text. Regular expressions appear frequently in ChemDataExtractor, most commonly in the chemical property parsers that will be outlined in the next section. Below, we provide a number of useful links for information on Regular Expressions.

If you are unfamiliar with Regular Expressions, I recommend going through the [TutorialsPoint Python Regular Expressions tutorial](https://www.tutorialspoint.com/python/python_reg_expressions.htm).

Python contains a useful regular expressions library ``re`` that also contains extensive documentation [here](https://docs.python.org/3/library/re.html).

Formatting Regular Expressions can be problematic, especially for highly nested groups. Perhaps the most useful tool for dealing with Regular Expressions is [Debuggex](https://www.debuggex.com) which provides a beautiful graphical interface for debugging regular expressions.

## 6.5 Creating a New Property Parser
Depending on your specific use case, you will almost definitely need to add new property parsers to ChemDataExtractor in order to retrieve new properties from scientific text/tables. Here we take you through a simple example of how to create a new parser.

First, we need all the relevant imports
```python
from chemdataextractor import Document
from chemdataextractor.model import Compound
from chemdataextractor.doc import Paragraph, Heading
```

Let's create a simple example document with a single heading followed by a single paragraph that contains a boiling point:

```python
d = Document(
    Heading(u'Synthesis of 2,4,6-trinitrotoluene (3a)'),
    Paragraph(u'The procedure was followed to yield a pale yellow solid (b.p. 240 °C)')
)
```

By default, ChemDataExtractor wont extract the `boiling_point` property. This can be shown by examining the output records.

```python
d.records.serialize()
>>> [{'labels': ['3a'], 'names': ['2,4,6-trinitrotoluene'], 'roles': ['product']}]
```

So we want to create a `boiling_point` property parser.

**Step 1: Defining a new property model**

In ```chemdataextractor.model.py``` you will see all the current property models defined in ChemDataExtractor. You will also see the ```Compound``` class which contains all properties available for a single compound. Each property inherits from ```BaseModel``` and can contain fields that can have different types (```StringType```: a string, ```ModelType```: Another property model, ```ListType```: A list of another type e.g. ```ListType(StringType())``` is a list of strings).

So in ```model.py``` we need to create a ```BoilingPoint``` class and give it some useful fields. In the most simple case, a boiling point has a unit and a value, both of which are string-type arguments.

```python
class BoilingPoint(BaseModel):  # Must inherit from BaseModel
""" A boiling point property"""
    value = StringType()
    units = StringType()
````

If you look around at other properties, you will see that they can have contextual fields (by setting the ```contextual``` parameter to ```True``` inside the field type). Setting this parameter means that global contextual information from other elements of the document will be merged into these records. For example, if your property measurement was performed at a certain temperature, this information could have been given elsewhere in the document (maybe the experimental method section). By telling the model that this information is contextual, the temperature of the measurement will be merged with all relevant records.

Next, we need to add our new property to the ```Compound``` class

```python 
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
```
Note, we make the boiling points have ```ListType``` because a single compound could have multiple boiling points given in the document. 

**Step 2: Writing a Parser**

Now we need to create the logic that actually extracts boiling points from the text. Currently, ChemDataExtractor uses nested rules (called grammars) to extract chemical properties. These parsers are defined in the ```chemdataextractor.parse``` package. For example, have a look at the melting point parser in ```chemdataextractor.parse.mp.py```. This contains a number of statements that are used to define the melting point relationship. 

It seems very complicated at first, but let's break the first statement down into its consituent parts:

```python
prefix = Optional(I('a')).hide() + (Optional(lbrct) + W('Tm') + Optional(rbrct)| R('^m\.?pt?\.?$', re.I) | I('melting') + Optional((I('point') | I('temperature')| I('range'))) | R('^m\.?$', re.I) + R('^pt?\.?$', re.I)).hide() + Optional(lbrct + W('Tm') + rbrct) + Optional(W('=') | I('of') | I('was') | I('is') | I('at')).hide() + Optional(I('in') + I('the') + I('range') + Optional(I('of')) | I('about')).hide()
```

Here, we have created a variable prefix, that contains the logic for identifying the melting point relationship specifier (e.g. the text that makes it clear we are talking about a melting point in the text, such "a melting temperature, Tm, "). The grammar contains several elements, with nested logic. Each token must be assigned an element type, these can be:

* ```I```: A case insensitive word
* ```W```: A case sensitive word
* ```R```: A regular expression rule
* ```T```: A Part-of-Speech tag

Tokens can be joined using the + symbol, and or logic can be formed using the | symbol. 

There are also a number of `ParseElementEnhance` classes that can be used, found in the ```chemdataextractor.parse.elements.py``` file:

* ```Optional```: Matches the contained tokens if they appear, but are not required to form a match
* ```ZeroOrMore```: Matches any number of the contained tokens
* ```Any```: Matches any token e.g. ZeroOrMore(Any()) will match the whole of the text
* ```OneOrMore```: Similar to zero or more, but at least one token is required.
* ```Not```: Looks ahead to disallow a match

Finally, we note that we can hide elements by adding the ```.hide()``` method. This means that when the parser creates the relationship tree, the hidden tokens are not used.

Continuing to look at the melting point parser, we see the follwing line:

```python
units = (W('°') + Optional(R('^[CFK]\.?$')) | W('K\.?'))('units').add_action(merge)
```
This will clearly match any temperature unit, and as such we tag the rule as 'units'. On top of the tags, we can do some post-processing actions to clean up the output. Here, we add the action ```merge```, which joins all tokens without whitespace (° C becomes °C). Other actions include:

* ```join```: Join tokens into a single string with spaces between.
* ```flatten```: Replace all child results with their text contents.

So now we are able to create our own property parsing rules. Create a file ```bp.py``` in the parse package. Some very simple logic for extracting boiling points might be: 

```python 
from chemdataextractor.parse import R, I, W, Optional, merge
from chemdataextractor.parse.base import BaseParser
from chemdataextractor.utils import first


prefix = (R(u'^b\.?p\.?$', re.I) | I(u'boiling') + I(u'point')).hide()
units = (W(u'°') + Optional(R(u'^[CFK]\.?$')))(u'units').add_action(merge)
value = R(u'^\d+(\.\d+)?$')(u'value')
bp = (prefix + value + units)(u'bp')
```
The most important thing to note is that the final phrase (called ```bp```) is now a nested tree, with tags labelling the elements. If we were to reproduce the XML it would look like:
```XML
<bp>
    <value>R(u'^\d+(\.\d+)?$')</value>
    <units>W(u'°') + Optional(R(u'^[CFK]\.?$'))</units>
</bp>
```

Now we have to create the logic for parsing this structure. In the same file, we create the parser class, that inherits from ```BaseParser```

```python
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
```
All parser classes must define:
* A root variable: i.e. the phrase that forms the head of the tree
* An ```interpret``` function: That defines the parsing logic

The ```interpret``` function then creates a new compound (with the model we defined in ```model.py```) and adds a boiling point property. Here, the result parameter is the result of the parsing process. If a tree with root bp is found, we access the value and unit elements using [XPath expressions](https://www.w3schools.com/xml/xpath_syntax.asp).

Finally, we need to tell ChemDataExtractor to parse the paragraphs with our new parser. In ```ChemDataextractor.doc.text``` find the ```Paragraph``` class and add the ```BpParser()``` class to the list of parsers.

```python
class Paragraph(Text):
    parsers = [..., BpParser()]
```

**Step 3: Testing the Parser**

Now we can simply re-run the document through ChemDataExtractor.
```python
d = Document(
    Heading(u'Synthesis of 2,4,6-trinitrotoluene (3a)'),
    Paragraph(u'The procedure was followed to yield a pale yellow solid (b.p. 240 °C)')
)

d.records.serialize()
>>> [{'boiling_points': [{'units': '°C', 'value': '240'}],
  'labels': ['3a'],
  'names': ['2,4,6-trinitrotoluene'],
  'roles': ['product']}]
```
Of course, real world examples are much more complex than this, and a large amount of trial and error is needed to create good parsers. It should also be noted that in this example, the chemical label ('3a') is found using interdependency resolution between the heading and associated paragraph. In some cases you will need to put the chemical labels and names directly into the parser. Rules for chemical entity recognition can be found in ```chemdataextractor.parse.cem.py```.


**Table Parsers**

ChemDataExtractor parses tables in a similar way. In ```chemdataextractor.parse.table.py``` you will find the logic for finding chemical relationships from tables. As an exercise try to write a table parser for the boiling point relationship we just created. You will need to define a way to find boiling points in table headers, then a parser for the cells. Available table parsers can be found in ```chemdataextractor.doc.table.py```.
        
## 6.6 "Where do I find...?"

The most common questions about ChemDataExtractor usually involve trying to find functionality or asking where best to put new functionality. Below is a list of the general roles each of the packages perform:

* ```biblio```: Misc tools for parsing bibliographic information such as bibtex files, author names etc.
* ```cli```: Command line interfact tools
* ```doc```: Logic for reading/creating documents. That is, splitting documents down into its various elements. 
* ```nlp```: Tools for performing the NLP stages, such as POS tagging, Word clustering, CNER, Abbreviation detection
* ```parse```: Chemical property parsers
* ```Reader```: Document readers
* ```scrape```: Scrapers for the various data sources
* ```text```: Useful tools for processing text

If you have new functionality that doesn't fit into one of these categories. You may want to create a new sub-package. Alternatively, if your new functionality is very specific to your own use case, it may be better to have it external to ChemDataExtractor.


## 6.7 Getting Help
If you are completely lost or have a seemingly unsolvable problem with ChemDataExtractor, first post in the [developers group](https://chemdataextractor-dev.slack.com), and someone else will try to help you with your problem. If you find a bug that needs to be fixed, please mark the bug as an issue on the Github repository.

