# -*- coding: utf-8 -*-
"""
Readers for Elsevier XML files.

jm2111

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ..scrape.clean import Cleaner
from .markup import XmlReader
from lxml import etree
import six
import re

from ..scrape import BLOCK_ELEMENTS

class CleanerElsevier(Cleaner):
    """Some modifications for cleaning Elsevier XML documents"""
    def __init__(self, **kwargs):
        super(CleanerElsevier, self).__init__(**kwargs)

    def __call__(self, doc):
        """Clean the document."""
        if hasattr(doc, 'getroot'):
            doc = doc.getroot()

        if self.fix_whitespace:
            # Ensure newlines around block elements
            for el in doc.iterdescendants():
                if el.tag in BLOCK_ELEMENTS:
                    el.tail = (el.tail or '') + '\n'
                    previous = el.getprevious()
                    parent = el.getparent()
                    if previous is None:
                        parent.text = (parent.text or '') + '\n'
                    else:
                        previous.tail = (previous.tail or '') + '\n'

        # Remove elements that match kill_xpath
        if self.kill_xpath:
            for el in doc.xpath(self.kill_xpath, namespaces=self.namespaces):
                parent = el.getparent()
                # We can't kill the root element!
                if parent is None:
                    continue
                if el.tail:
                    previous = el.getprevious()
                    if previous is None:
                        parent.text = (parent.text or '') + el.tail
                    else:
                        previous.tail = (previous.tail or '') + el.tail
                parent.remove(el)

        # Collect all the allowed elements
        to_keep = [el for el in doc.xpath(self.allow_xpath, namespaces=self.namespaces)] if self.allow_xpath else []

        # Replace elements that match strip_xpath with their contents
        if self.strip_xpath:
            for el in doc.xpath(self.strip_xpath, namespaces=self.namespaces):
                # Skip if allowed by allow_xpath
                if el in to_keep:
                    continue
                parent = el.getparent()
                previous = el.getprevious()
                # We can't strip the root element!
                if parent is None:
                    continue
                # Append the text to previous tail (or parent text if no previous), ensuring newline if block level
                if el.text and isinstance(el.tag, six.string_types):
                    if previous is None:
                        parent.text = (parent.text or '') + el.text
                    else:
                        previous.tail = (previous.tail or '') + el.text
                # Append the tail to last child tail, or previous tail, or parent text, ensuring newline if block level
                if el.tail:
                    if len(el):
                        last = el[-1]
                        last.tail = (last.tail or '') + el.tail
                    elif previous is None:
                        parent.text = (parent.text or '') + el.tail
                    else:
                        previous.tail = (previous.tail or '') + el.tail
                index = parent.index(el)
                parent[index:index+1] = el[:]

        # Collapse whitespace down to a single space or a single newline
        if self.fix_whitespace:
            for el in doc.iter():
                if el.text is not None:
                    # changed by jm2111 for elsevier, we don't need newline characters
                    el.text = re.sub(r'\s*\n\s*', ' ', el.text)
                    el.text = re.sub(r'[ \t]+', ' ', el.text)
                    el.text = re.sub(r'\s+', ' ', el.text)
                if el.tail is not None:
                    # changed by jm2111 for elsevier, we don't need newline characters
                    el.tail = re.sub(r'\s*\n\s*', ' ', el.tail)
                    el.tail = re.sub(r'[ \t]+', ' ', el.tail)
                    el.tail = re.sub(r'\s+', ' ', el.tail)

# Override default cleaner
clean = CleanerElsevier()

# XML stripper that removes the taggs around numbers in chemical formulas
strip_els_xml = CleanerElsevier(strip_xpath='.//ce:inf | .//ce:italic | .//ce:sup')


def elsevier_xml_whitespace(document):
    """ Remove whitespace in xml.text or xml.tails for all elements, if it is only whitespace """
    # selects all tags and checks if the text or tail are spaces
    for el in document.xpath('//*'):
        if str(el.text).isspace():
            el.text = ''
        if str(el.tail).isspace():
            el.tail = ''
    # DEBUG, check the document
    # print(etree.tostring(document, pretty_print=True))
    # sys.exit()
    return document

class ElsevierXmlReader(XmlReader):
    """Reader for Elsevier XML documents."""

    cleaners = [clean, elsevier_xml_whitespace, strip_els_xml]

    etree.FunctionNamespace("http://www.elsevier.com/xml/svapi/article/dtd").prefix = 'default'
    etree.FunctionNamespace("http://www.elsevier.com/xml/bk/dtd").prefix = 'bk'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/cals/dtd").prefix = 'cals'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/dtd").prefix = 'ce'
    etree.FunctionNamespace("http://www.elsevier.com/xml/ja/dtd").prefix = 'ja'
    etree.FunctionNamespace("http://www.w3.org/1998/Math/MathML").prefix = 'mml'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/struct-aff/dtd").prefix = 'sa'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/struct-bib/dtd").prefix = 'sb'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/table/dtd").prefix = 'tb'
    etree.FunctionNamespace("http://www.w3.org/1999/xlink").prefix = 'xlink'
    etree.FunctionNamespace("http://www.elsevier.com/xml/xocs/dtd").prefix = 'xocs'
    etree.FunctionNamespace("http://purl.org/dc/elements/1.1/").prefix = 'dc'
    etree.FunctionNamespace("http://purl.org/dc/terms/").prefix = 'dcterms'
    etree.FunctionNamespace("http://prismstandard.org/namespaces/basic/2.0/").prefix = 'prism'
    etree.FunctionNamespace("http://www.w3.org/2001/XMLSchema-instance").prefix = 'xsi'

    root_css = 'default|full-text-retrieval-response'
    title_css = 'dc|title'
    heading_css = 'ce|section-title'
    table_css = 'ce|table'
    table_caption_css = 'ce|table ce|caption'
    table_head_row_css = 'cals|thead cals|row'
    table_body_row_css = 'cals|tbody cals|row'
    table_cell_css = 'ce|entry'
    figure_css = 'ce|figure'
    figure_caption_css = 'ce|figure ce|caption'
    reference_css = 'ce|cross-refs'
    citation_css = 'ce|bib-reference'
    ignore_css = 'xocs|ref-info, default|scopus-eid, xocs|normalized-srctitle,' \
                 'xocs|eid, xocs|hub-eid, xocs|normalized-first-auth-surname,' \
                 'xocs|normalized-first-auth-initial, xocs|refkeys,' \
                 'xocs|attachment-eid, xocs|attachment-type,' \
                 'ja|jid, ce|given-name, ce|surname, ce|affiliation, ce|cross-refs, ce|cross-ref,' \
                 'ce|grant-sponsor, ce|grant-number, prism|copyright,' \
                 'xocs|pii-unformatted, xocs|ucs-locator, ce|copyright,' \
                 'prism|publisher, xocs|copyright-line, xocs|cp-notice,' \
                 'dc|description'

    def detect(self, fstring, fname=None):
        """Elsevier document detection based on string found in xml"""
        if fname and not fname.endswith('.xml'):
            return False
        if b'xmlns="http://www.elsevier.com/xml/svapi/article/dtd"' in fstring:
            return True
        return False
