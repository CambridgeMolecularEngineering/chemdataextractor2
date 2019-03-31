# -*- coding: utf-8 -*-
"""
Elsevier XML reader

.. codeauthor:: Callum Court <cc889@cam.ac.uk>


Readers for Elsevier XML files.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import six
from ..scrape.clean import clean, Cleaner
from ..doc.table import Cell, Table
from ..doc.text import Caption
from .markup import XmlReader
from lxml import etree
import re

# XML stripper that removes the tags around numbers in chemical formulas
strip_els_xml = Cleaner(strip_xpath='.//ce:inf | .//ce:italic | .//ce:bold | .//ce:formula | .//mml:* | .//ce:sup', 
                        kill_xpath='.//ce:cross-ref//ce:sup | .//ce:table//ce:sup | .//ce:cross-ref | .//ce:cross-refs')


def fix_elsevier_xml_whitespace(document):
    """ Fix tricky xml tags"""
    # space hsp  and refs correctly
    for el in document.xpath('.//ce:hsp'):
        parent = el.getparent()
        previous = el.getprevious()
        if parent is None:
            continue
        # Append the text to previous tail (or parent text if no previous), ensuring newline if block level
        if el.text and isinstance(el.tag, six.string_types):
            if previous is None:
                if parent.text:
                    if parent.text.endswith(' '):
                        parent.text = (parent.text or '') + '' + el.text
                    else:
                        parent.text = (parent.text or '') + ' ' + el.text
            else:
                if previous.tail:
                    if previous.tail.endswith(' '):
                        previous.tail = (previous.tail or '') + '' + el.text
                    else:
                        previous.tail = (previous.tail or '') + ' ' + el.text
        # Append the tail to last child tail, or previous tail, or parent text, ensuring newline if block level
        if el.tail:
            if len(el):
                last = el[-1]
                last.tail = (last.tail or '') + el.tail
            elif previous is None:
                if el.tail.startswith(' '):
                    parent.text = (parent.text or '') + '' + el.tail
                else:
                    parent.text = (parent.text or '') + ' ' + el.tail
            else:
                if el.tail.startswith(' '):
                    previous.tail = (previous.tail or '') + '' + el.tail
                else:
                    previous.tail = (previous.tail or '') + ' ' + el.tail

        index = parent.index(el)
        parent[index:index + 1] = el[:]
    return document


def els_xml_whitespace(document):
    """ Remove whitespace in xml.text or xml.tails for all elements, if it is only whitespace """
    # selects all tags and checks if the text or tail are spaces
    for el in document.xpath('//*'):
        if str(el.text).isspace():
            el.text = ''
        if str(el.tail).isspace():
            el.tail = ''
    # debug, check the document
    #print(etree.tostring(document, pretty_print=True))
    # sys.exit()
    return document


class ElsevierXmlReader(XmlReader):
    """Reader for Elsevier XML documents."""

    cleaners = [clean, fix_elsevier_xml_whitespace, els_xml_whitespace, strip_els_xml]

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
    table_footnote_css = 'table-wrap-foot p'
    figure_css = 'ce|figure'
    figure_caption_css = 'ce|figure ce|caption'
    figure_label_css = 'ce|figure ce|label'
    reference_css = 'ce|cross-refs'
    citation_css = 'ce|bib-reference'
    ignore_css = 'ce|bibliography, ce|acknowledgment, ce|correspondence, ce|author, ce|doi, ja|jid, ja|aid, ce|pii, xocs|oa-sponsor-type, xocs|open-access, default|openaccess,'\
                 'default|openaccessArticle, dc|format, dc|creator, dc|identifier,'\
                'default|eid, default|pii, xocs|meta, xocs|ref-info, default|scopus-eid,'\
                 'xocs|normalized-srctitle,' \
                 'xocs|eid, xocs|hub-eid, xocs|normalized-first-auth-surname,' \
                 'xocs|normalized-first-auth-initial, xocs|refkeys,' \
                 'xocs|attachment-eid, xocs|attachment-type,' \
                 'ja|jid, ce|given-name, ce|surname, ce|affiliation, ce|cross-refs, ce|cross-ref,' \
                 'ce|grant-sponsor, ce|grant-number, prism|copyright,' \
                 'xocs|pii-unformatted, xocs|ucs-locator, ce|copyright,' \
                 'prism|publisher, prism|*, xocs|copyright-line, xocs|cp-notice,' \
                 'dc|description'

    def detect(self, fstring, fname=None):
        """Elsevier document detection based on string found in xml"""
        if fname and not fname.endswith('.xml'):
            return False
        if b'xmlns="http://www.elsevier.com/xml/svapi/article/dtd"' in fstring:
            return True
        return False
