# -*- coding: utf-8 -*-
"""
XML and HTML readers based on lxml.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
from abc import abstractmethod, ABCMeta
from collections import defaultdict

from lxml import etree
from lxml.etree import XMLParser
from lxml.html import HTMLParser
import six

from ..errors import ReaderError
from ..doc.document import Document
from ..doc.text import Title, Heading, Paragraph, Caption, Citation, Footnote, Text, Sentence, Cell
from ..doc.meta import MetaData
from ..doc.table import Table
from ..doc.figure import Figure
from ..scrape import INLINE_ELEMENTS
from ..scrape.clean import clean
from ..scrape.csstranslator import CssHTMLTranslator
from ..text import get_encoding
from .base import BaseReader


log = logging.getLogger(__name__)


class LxmlReader(six.with_metaclass(ABCMeta, BaseReader)):
    """Abstract base class for lxml-based readers."""

    #: A ``Cleaner`` instance to
    cleaners = [clean]

    root_css = 'html'
    title_css = 'h1'
    heading_css = 'h2, h3, h4, h5, h6'
    table_css = 'table'
    table_caption_css = 'caption'
    table_head_row_css = 'thead tr'
    table_body_row_css = 'tbody tr'
    table_cell_css = 'th, td'
    table_footnote_css = 'tfoot tr th'
    reference_css = 'a.ref'
    figure_css = 'figure'
    figure_caption_css = 'figcaption'
    figure_label_css = 'figcaption span[class^="CaptionNumber"]'
    figure_download_link_css = 'a::attr(href), img::attr(src)'
    citation_css = 'cite'

    metadata_css = 'head'
    metadata_publisher_css = 'meta[name="DC.publisher"]::attr("content"), meta[name="citation_publisher"]::attr("content")'
    metadata_author_css = 'meta[name="DC.Creator"]::attr("content"), meta[name="citation_author"]::attr("content")'
    metadata_title_css = 'meta[name="DC.title"]::attr("content"), meta[name="citation_title"]::attr("content")'
    metadata_date_css = 'meta[name="DC.Date"]::attr("content"), meta[name="citation_date"]::attr("content"), meta[name="citation_online_date"]::attr("content")'
    metadata_doi_css = 'meta[name="DC.Identifier"]::attr("content"), meta[name="citation_doi"]::attr("content")'
    metadata_language_css = 'meta[name="DC.Language"]::attr("content"), meta[name="citation_language"]::attr("content")'
    metadata_journal_css = 'meta[name="citation_journal_title"]::attr("content")'
    metadata_volume_css = 'meta[name="citation_volume"]::attr("content")'
    metadata_issue_css = 'meta[name="citation_issue"]::attr("content")'
    metadata_firstpage_css = 'meta[name="citation_firstpage"]::attr("content")'
    metadata_lastpage_css = 'meta[name="citation_lastpage"]::attr("content")'
    metadata_pdf_url_css = 'meta[name="citation_pdf_url"]::attr("content")'
    metadata_html_url_css = 'meta[name="citation_fulltext_html_url"]::attr("content"), meta[name="citation_abstract_html_url"]::attr("content")'

    ignore_css = 'a.ref sup'

    #: Inline elements
    inline_elements = INLINE_ELEMENTS

    def _parse_element_r(self, el, specials, refs, id=None, element_cls=Paragraph):
        """Recursively parse HTML/XML element and its children into a list of Document elements."""
        elements = []
        if el.tag in {etree.Comment, etree.ProcessingInstruction}:
            return []
        # if el in refs:
        #     return [element_cls('', references=refs[el])]
        if el in specials:
            return specials[el]
        id = el.get('id', id)
        references = refs.get(el, [])
        if el.text is not None:
            elements.append(element_cls(six.text_type(el.text), id=id, references=references))
        elif references:
            elements.append(element_cls('', id=id, references=references))
        for child in el:
            # br is a special case - technically inline, but we want to split
            if child.tag not in {etree.Comment, etree.ProcessingInstruction} and child.tag.lower() == 'br':
                elements.append(element_cls(''))

            child_elements = self._parse_element_r(child, specials=specials, refs=refs, id=id, element_cls=element_cls)
            if (self._is_inline(child) and len(elements) > 0 and len(child_elements) > 0 and
                    isinstance(elements[-1], (Text, Sentence)) and isinstance(child_elements[0], (Text, Sentence)) and
                    type(elements[-1]) == type(child_elements[0])):
                elements[-1] += child_elements.pop(0)
            elements.extend(child_elements)
            if child.tail is not None:
                if self._is_inline(child) and len(elements) > 0 and isinstance(elements[-1], element_cls):
                    elements[-1] += element_cls(six.text_type(child.tail), id=id)
                else:
                    elements.append(element_cls(six.text_type(child.tail), id=id))
        return elements

    def _parse_element(self, el, specials=None, refs=None, element_cls=Paragraph):
        """"""
        if specials is None:
            specials = {}
        if refs is None:
            refs = {}
        elements = self._parse_element_r(el, specials=specials, refs=refs, element_cls=element_cls)
        final_elements = []
        for element in elements:
            # Filter empty text elements
            if isinstance(element, Text):
                if element.text.strip():
                    final_elements.append(element)
            else:
                final_elements.append(element)
        return final_elements

    def _parse_text(self, el, refs=None, specials=None, element_cls=Paragraph):
        """Like _parse_element but ensure a single element."""
        if specials is None:
            specials = {}
        if refs is None:
            refs = {}
        elements = self._parse_element_r(el, specials=specials, refs=refs, element_cls=element_cls)
        # This occurs if the input element is self-closing... (some table td in NLM XML)
        if not elements:
            return [element_cls('')]
        element = elements[0]
        for next_element in elements[1:]:
            try:
                element += element_cls(' ') + next_element
            except TypeError as e:
                log.warning('Adding of two objects was skipped. {} and {} cannot be added.'.format(str(type(element)), str(type(next_element))))
        return [element]
    
    def _parse_figure_links(self, el):
        return self._css(self.figure_download_link_css, el)

    def _parse_figure(self, el, refs, specials):
        caps = self._css(self.figure_caption_css, el)

        label_css = self._css(self.figure_label_css, el)
        label = label_css[0].text if label_css else None

        links = self._parse_figure_links(el)
        caption = self._parse_text(caps[0], refs=refs, specials=specials, element_cls=Caption)[0] if caps else Caption('')
        fig = Figure(caption, label=label, links=links)
        return [fig]

    def _parse_table_rows(self, els, refs, specials):
        hdict = {}
        for row, tr in enumerate(els):
            colnum = 0
            for td in self._css(self.table_cell_css, tr):
                cell = self._parse_text(td, refs=refs, specials=specials, element_cls=Cell)
                colspan = int(td.get('colspan', '1'))
                rowspan = int(td.get('rowspan', '1'))
                for i in range(colspan):
                    for j in range(rowspan):
                        rownum = row + j
                        if not rownum in hdict:
                            hdict[rownum] = {}
                        while colnum in hdict[rownum]:
                            colnum += 1
                        hdict[rownum][colnum] = cell[0]
                    colnum += 1
        rows = []
        for row in sorted(hdict):
            rows.append([])
            for col in sorted(hdict[row]):
                rows[-1].append(hdict[row][col])
        for r in rows:
            r.extend([Cell('')] * (len(max(rows, key=len)) - len(r)))
        rows = [r for r in rows if any(r)]
        return rows

    def _parse_table_footnotes(self, fns, refs, specials):
        return [self._parse_text(fn, refs=refs, specials=specials, element_cls=Footnote)[0] for fn in fns]

    def _parse_reference(self, el):
        """Return reference ID from href or text content."""
        if '#' in el.get('href', ''):
            return [el.get('href').split('#', 1)[1]]
        elif 'rid' in el.attrib:
            return [el.attrib['rid']]
        elif 'idref' in el.attrib:
            return [el.attrib['idref']]
        else:
            return [''.join(el.itertext()).strip()]

    # def _parse_table(self, el, refs, specials):
    #     caps = self._css(self.table_caption_css, el)
    #     caption = self._parse_text(caps[0], refs=refs, specials=specials, element_cls=Caption)[0] if caps else Caption('')
    #     hrows = self._parse_table_rows(self._css(self.table_head_row_css, el), refs=refs, specials=specials)
    #     rows = self._parse_table_rows(self._css(self.table_body_row_css, el), refs=refs, specials=specials)
    #     footnotes = self._parse_table_footnotes(self._css(self.table_footnote_css, el), refs=refs, specials=specials)
    #     tab = Table(caption, headings=hrows, rows=rows, footnotes=footnotes, id=el.get('id', None))
    #     return [tab]

    def _parse_table(self, el, refs, specials):
        caption_css = self._css(self.table_caption_css, el)
        caption = self._parse_text(caption_css[0], refs=refs, specials=specials, element_cls=Caption)[0] if caption_css else Caption('')
        hrows= self._parse_table_rows(self._css(self.table_head_row_css, el), refs=refs, specials=specials)
        rows = rows = self._parse_table_rows(self._css(self.table_body_row_css, el), refs=refs, specials=specials)
        data = []
        for hr in hrows:
            data.append([i.text.strip() for i in hr])
        for r in rows:
            data.append([i.text.strip() for i in r])
        table = Table(caption, table_data=data)

        return [table]

    def _parse_metadata(self, el, refs, specials):
        title = self._css(self.metadata_title_css, el)
        authors = self._css(self.metadata_author_css,el)
        publisher = self._css(self.metadata_publisher_css,el)
        journal = self._css(self.metadata_journal_css,el)
        date = self._css(self.metadata_date_css,el)
        language = self._css(self.metadata_language_css,el)
        volume = self._css(self.metadata_volume_css,el)
        issue = self._css(self.metadata_issue_css,el)
        firstpage =self._css(self.metadata_firstpage_css,el)
        lastpage=self._css(self.metadata_lastpage_css,el)
        doi = self._css(self.metadata_doi_css,el)
        pdf_url = self._css(self.metadata_pdf_url_css,el)
        html_url = self._css(self.metadata_html_url_css,el)

        metadata = {
                '_title': title[0] if title else None,
                '_authors': authors if authors else None,
                '_publisher': publisher[0] if publisher else None,
                '_journal': journal[0] if journal else None,
                '_date': date[0] if date else None,
                '_language': language[0] if language else None,
                '_volume': volume[0] if volume else None,
                '_issue': issue[0] if issue else None,
                '_firstpage': firstpage[0] if firstpage else None,
                '_lastpage': lastpage[0] if lastpage else None,
                '_doi': doi[0] if doi else None,
                '_pdf_url': pdf_url[0] if pdf_url else None,
                '_html_url': html_url[0] if html_url else None
                }
        meta = MetaData(metadata)
        return [meta]

    def _xpath(self, query, root):
        result = root.xpath(query, smart_strings=False)
        if type(result) is not list:
            result = [result]
        log.debug('Selecting XPath: {}: {}'.format(query, result))
        return result

    def _css(self, query, root):
        return self._xpath(CssHTMLTranslator().css_to_xpath(query), root)

    def _is_inline(self, element):
        """Return True if an element is inline."""
        if element.tag not in {etree.Comment, etree.ProcessingInstruction} and element.tag.lower() in self.inline_elements:
            return True
        return False

    @abstractmethod
    def _make_tree(self, fstring):
        """Read a string into an lxml elementtree."""
        pass

    def parse(self, fstring):
        root = self._make_tree(fstring)
        self.root = root

        if root is None:
            raise ReaderError

        root = self._css(self.root_css, root)[0]
        for cleaner in self.cleaners:
            cleaner(root)
        specials = {}
        refs = defaultdict(list)
        titles = self._css(self.title_css, root)
        headings = self._css(self.heading_css, root)
        figures = self._css(self.figure_css, root)
        tables = self._css(self.table_css, root)
        citations = self._css(self.citation_css, root)
        references = self._css(self.reference_css, root)
        ignores = self._css(self.ignore_css, root)
        metadata = self._css(self.metadata_css, root)
        for reference in references:
            refs[reference.getparent()].extend(self._parse_reference(reference))
        for ignore in ignores:
            specials[ignore] = []
        for title in titles:
            specials[title] = self._parse_text(title, element_cls=Title, refs=refs, specials=specials)
        for heading in headings:
            specials[heading] = self._parse_text(heading, element_cls=Heading, refs=refs, specials=specials)
        for figure in figures:
            specials[figure] = self._parse_figure(figure, refs=refs, specials=specials)
        for table in tables:
            specials[table] = self._parse_table(table, refs=refs, specials=specials)
        for citation in citations:
            specials[citation] = self._parse_text(citation, element_cls=Citation, refs=refs, specials=specials)
        for md in metadata:
            specials[md] = self._parse_metadata(md, refs=refs, specials=specials)
        elements = self._parse_element(root, specials=specials, refs=refs)
        return Document(*elements)


class XmlReader(LxmlReader):
    """Reader for generic XML documents."""

    def detect(self, fstring, fname=None):
        """"""
        if fname and not fname.endswith('.xml'):
            return False
        return True

    def _make_tree(self, fstring):
        root = etree.fromstring(fstring, parser=XMLParser(recover=True, encoding=get_encoding(fstring)))
        return root


class HtmlReader(LxmlReader):
    """Reader for generic HTML documents."""

    def detect(self, fstring, fname=None):
        """"""
        if fname and not (fname.endswith('.html') or fname.endswith('.htm')):
            return False
        return True

    def _make_tree(self, fstring):
        root = etree.fromstring(fstring, parser=HTMLParser(encoding=get_encoding(fstring)))
        return root
