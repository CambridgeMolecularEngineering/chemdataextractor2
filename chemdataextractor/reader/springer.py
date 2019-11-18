# -*- coding: utf-8 -*-
"""
Readers for documents from Springer.

.. codeauthor:: Callum Court

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from lxml import etree
import six
from lxml.html import HTMLParser
from ..text import get_encoding
from .markup import HtmlReader, XmlReader
from ..scrape.clean import clean, Cleaner, strip_html
from ..scrape.pub.springer import tidy_springer_references

clean_springer_html = Cleaner(fix_whitespace=True, strip_xpath='.//sub | .//em | .//strong')


class SpringerMaterialsHtmlReader(HtmlReader):
    """Reader for HTML documents from SpringerMaterials."""

    cleaners = [clean, clean_springer_html]

    root_css = 'html'
    citation_css = 'span[class="CitationRef"]'
    title_css = 'title'
    heading_css = 'h2, h3, h4, h5, h6, .title1, span.title2, span.title3'
    table_css = 'div[class="Table"]'
    table_caption_css = 'div[class="Table"] p'
    table_head_row_css = 'thead'
    table_body_row_css = 'tbody'
    table_cell_css = 'th, td'
    ignore_css = 'sub, sup, em[class^="EmphasisTypeItalic "], li[class="article-metrics__item"], div[class="CitationContent"]'

    def detect(self, fstring, fname=None):
        """"""
        if fname and not (fname.endswith('.html') or fname.endswith('.htm')):
            return False
        if b'<a class="footer-copyright_link" href="http://www.springernature.com"' in fstring or b'<meta content="SpringerLink"' in fstring:
            return True
        return False

    def _make_tree(self, fstring):
        root = etree.fromstring(fstring, parser=HTMLParser(
            encoding=get_encoding(fstring, guesses='utf-8', is_html=True)))
        return root

def springer_html_whitespace(document):
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

def fix_springer_table_whitespace(document):
    """remove leading and trailing whitespace from table cells
    
    Arguments:
        document {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    for el in document.xpath('.//table//p | .//table//p'):
        if el.text:
            stripped = str(el.text).strip()
            el.text = stripped
    return document

class SpringerHtmlReader(HtmlReader):

    cleaners = [clean, springer_html_whitespace, clean_springer_html, strip_html, tidy_springer_references, fix_springer_table_whitespace]

    root_css = 'html'
    title_css = 'h1[class^="ArticleTitle"]'
    heading_css = 'h2, h3, h4'
    table_css = 'div[class="Table"]'
    table_caption_css = 'div[class^="Caption"] p'
    table_head_row_css = 'thead tr'
    table_body_row_css = 'tbody tr'
    table_cell_css = 'td, th'
    figure_css = 'figure'
    figure_caption_css = 'figcaption'
    figure_label_css = 'figcaption span[class^="CaptionNumber"]'
    # citation_css = 'ce|bib-reference'
    ignore_css = 'a[class="skip-to__link pseudo-focus"], div[class="nojs-banner u-interface"], a[class="skip-to__link skip-to__link--contents pseudo-focus"],\
                  p[class="leaderboard__label"], div[class="u-screenreader-only"], label[for="search-springerlink"], span[class="search-button__title"],\
                  span[class="u-overflow-ellipsis"], span[class="u-overflow-ellipsis"], a[class="c-button c-button--blue c-button__icon-right gtm-pdf-link"],\
                  div[class="leaderboard u-hide"], title, li[class="article-metrics__item"], aside[class="section section--collapsible"], a[class="gtm-cite-link"],\
                  span[class="u-screenreader-only"], div[class="authors__list"], a[class="gtm-tab-authorsandaffiliations"], ol[class="BibliographyWrapper"],\
                  h2[id="copyrightInformation"], div[class="content authors-affiliations u-interface"], p[class="footer__copyright"], p[class="footer__user-access-info"],\
                  span[class="u-screenreader-only"], a[href="/contactus"], a[class="gtm-footer-accessibility"], ul[class="footer__nav"], div[class="footer__aside-wrapper"],\
                  aside[class="main-sidebar-right u-interface"], a[class="c-button share-this gtm-shareby-sharelink-link test-shareby-sharelink-link"],\
                  a[class="gtm-export-citation"], ul[class="citations__content"], h3[data-role="button-dropdown__title"],\
                  div[class="section section--collapsible uptodate-recommendations gtm-recommendations"], span[class="InlineEquation"], div[class="EquationContent"],\
                  div[class="EquationNumber"], footer'


    def detect(self, fstring, fname=None):
        """"""
        if fname and not (fname.endswith('.html') or fname.endswith('.htm')):
            return False
        if b'<meta content="Springer US" name="citation_publisher"' in fstring or b'<meta content="SpringerLink"' in fstring:
            print("springer HTML")
            return True
        return False

    def _make_tree(self, fstring):
        root = etree.fromstring(fstring, parser=HTMLParser(
            encoding=get_encoding(fstring, guesses='utf-8', is_html=True)))
        return root