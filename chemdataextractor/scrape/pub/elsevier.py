# -*- coding: utf-8 -*-
"""
Tools for scraping documents from Elsevier.

:copyright: Copyright 2017 by Callum Court.
:license: MIT, see LICENSE file for more details.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re

from bs4 import UnicodeDammit
from lxml.etree import fromstring, FunctionNamespace
from lxml.html import HTMLParser, Element
import six

from ...text.processors import Substitutor, Discard, Chain, LStrip, RStrip, LAdd
from ...text.normalize import normalize
from .. import BLOCK_ELEMENTS
from ..clean import Cleaner, clean
from ..entity import Entity, DocumentEntity, EntityList
from ..fields import StringField, EntityField, UrlField, DateTimeField
from ..scraper import RssScraper, SearchScraper, UrlScraper
from ..selector import Selector
from selenium import webdriver
from time import sleep
from ..csstranslator import CssHTMLTranslator, CssXmlTranslator
from lxml import etree 

log = logging.getLogger(__name__)

#: Map placeholder text to unicode characters.
CHAR_REPLACEMENTS = [
    ('\[?\[1 with combining macron\]\]?', '1\u0304'),
    ('\[?\[2 with combining macron\]\]?', '2\u0304'),
    ('\[?\[3 with combining macron\]\]?', '3\u0304'),
    ('\[?\[4 with combining macron\]\]?', '4\u0304'),
    ('\[?\[approximate\]\]?', '\u2248'),
    ('\[?\[bottom\]\]?', '\u22a5'),
    ('\[?\[c with combining tilde\]\]?', 'C\u0303'),
    ('\[?\[capital delta\]\]?', '\u0394'),
    ('\[?\[capital lambda\]\]?', '\u039b'),
    ('\[?\[capital omega\]\]?', '\u03a9'),
    ('\[?\[capital phi\]\]?', '\u03a6'),
    ('\[?\[capital pi\]\]?', '\u03a0'),
    ('\[?\[capital psi\]\]?', '\u03a8'),
    ('\[?\[capital sigma\]\]?', '\u03a3'),
    ('\[?\[caret\]\]?', '^'),
    ('\[?\[congruent with\]\]?', '\u2245'),
    ('\[?\[curly or open phi\]\]?', '\u03d5'),
    ('\[?\[dagger\]\]?', '\u2020'),
    ('\[?\[dbl greater-than\]\]?', '\u226b'),
    ('\[?\[dbl vertical bar\]\]?', '\u2016'),
    ('\[?\[degree\]\]?', '\xb0'),
    ('\[?\[double bond, length as m-dash\]\]?', '='),
    ('\[?\[double bond, length half m-dash\]\]?', '='),
    ('\[?\[double dagger\]\]?', '\u2021'),
    ('\[?\[double equals\]\]?', '\u2267'),
    ('\[?\[double less-than\]\]?', '\u226a'),
    ('\[?\[double prime\]\]?', '\u2033'),
    ('\[?\[downward arrow\]\]?', '\u2193'),
    ('\[?\[fraction five-over-two\]\]?', '5/2'),
    ('\[?\[fraction three-over-two\]\]?', '3/2'),
    ('\[?\[gamma\]\]?', '\u03b3'),
    ('\[?\[greater-than-or-equal\]\]?', '\u2265'),
    ('\[?\[greater, similar\]\]?', '\u2273'),
    ('\[?\[gt-or-equal\]\]?', '\u2265'),
    ('\[?\[i without dot\]\]?', '\u0131'),
    ('\[?\[identical with\]\]?', '\u2261'),
    ('\[?\[infinity\]\]?', '\u221e'),
    ('\[?\[intersection\]\]?', '\u2229'),
    ('\[?\[iota\]\]?', '\u03b9'),
    ('\[?\[is proportional to\]\]?', '\u221d'),
    ('\[?\[leftrightarrow\]\]?', '\u2194'),
    ('\[?\[leftrightarrows\]\]?', '\u21c4'),
    ('\[?\[less-than-or-equal\]\]?', '\u2264'),
    ('\[?\[less, similar\]\]?', '\u2272'),
    ('\[?\[logical and\]\]?', '\u2227'),
    ('\[?\[middle dot\]\]?', '\xb7'),
    ('\[?\[not equal\]\]?', '\u2260'),
    ('\[?\[parallel\]\]?', '\u2225'),
    ('\[?\[per thousand\]\]?', '\u2030'),
    ('\[?\[prime or minute\]\]?', '\u2032'),
    ('\[?\[quadruple bond, length as m-dash\]\]?', '\u2263'),
    ('\[?\[radical dot\]\]?', ' \u0307'),
    ('\[?\[ratio\]\]?', '\u2236'),
    ('\[?\[registered sign\]\]?', '\xae'),
    ('\[?\[reverse similar\]\]?', '\u223d'),
    ('\[?\[right left arrows\]\]?', '\u21C4'),
    ('\[?\[right left harpoons\]\]?', '\u21cc'),
    ('\[?\[rightward arrow\]\]?', '\u2192'),
    ('\[?\[round bullet, filled\]\]?', '\u2022'),
    ('\[?\[sigma\]\]?', '\u03c3'),
    ('\[?\[similar\]\]?', '\u223c'),
    ('\[?\[small alpha\]\]?', '\u03b1'),
    ('\[?\[small beta\]\]?', '\u03b2'),
    ('\[?\[small chi\]\]?', '\u03c7'),
    ('\[?\[small delta\]\]?', '\u03b4'),
    ('\[?\[small eta\]\]?', '\u03b7'),
    ('\[?\[small gamma, Greek, dot above\]\]?', '\u03b3\u0307'),
    ('\[?\[small kappa\]\]?', '\u03ba'),
    ('\[?\[small lambda\]\]?', '\u03bb'),
    ('\[?\[small micro\]\]?', '\xb5'),
    ('\[?\[small mu \]\]?', '\u03bc'),
    ('\[?\[small nu\]\]?', '\u03bd'),
    ('\[?\[small omega\]\]?', '\u03c9'),
    ('\[?\[small phi\]\]?', '\u03c6'),
    ('\[?\[small pi\]\]?', '\u03c0'),
    ('\[?\[small psi\]\]?', '\u03c8'),
    ('\[?\[small tau\]\]?', '\u03c4'),
    ('\[?\[small theta\]\]?', '\u03b8'),
    ('\[?\[small upsilon\]\]?', '\u03c5'),
    ('\[?\[small xi\]\]?', '\u03be'),
    ('\[?\[small zeta\]\]?', '\u03b6'),
    ('\[?\[space\]\]?', ' '),
    ('\[?\[square\]\]?', '\u25a1'),
    ('\[?\[subset or is implied by\]\]?', '\u2282'),
    ('\[?\[summation operator\]\]?', '\u2211'),
    ('\[?\[times\]\]?', '\xd7'),
    ('\[?\[trade mark sign\]\]?', '\u2122'),
    ('\[?\[triple bond, length as m-dash\]\]?', '\u2261'),
    ('\[?\[triple bond, length half m-dash\]\]?', '\u2261'),
    ('\[?\[triple prime\]\]?', '\u2034'),
    ('\[?\[upper bond 1 end\]\]?', ''),
    ('\[?\[upper bond 1 start\]\]?', ''),
    ('\[?\[upward arrow\]\]?', '\u2191'),
    ('\[?\[varepsilon\]\]?', '\u03b5'),
    ('\[?\[x with combining tilde\]\]?', 'X\u0303'),
]

#: Substitutor that replaces ACS escape codes with the actual unicode character
elsevier_substitute = Substitutor(CHAR_REPLACEMENTS)

class ElsevierSearchDocument(Entity):
    """Document information from Elsevier API search results."""
    test = StringField('.', xpath=True)


class ElsevierSearchScraper(UrlScraper):
    """Scraper for Elsevier search results."""
    entity = ElsevierSearchDocument

    def make_request(self, url):
        driver = webdriver.Firefox()
        driver.get(url)
        sleep(10)
        response = driver.page_source
        driver.quit()
        return response

    def run(self, url):
        """Request URL, scrape response and return an EntityList."""
        if not url:
            return
        response = self.make_request(url)
        selector = Selector.from_html_text(response)
        entities = []
        for root in self.get_roots(selector):
            entity = self.entity(root)
            entity = self.process_entity(entity)
            if entity:
                entities.append(entity)
        return EntityList(*entities)


class ElsevierImage(Entity):
    """Embedded figure. Includes both Schemes and Figures."""
    caption = StringField('dd[id^="labelCaption"]')
    image_url = StringField('a[class="S_C_full_size"]::attr("data-src")')
    process_caption = Chain(elsevier_substitute, normalize)
    process_image_url = LAdd('http://sciencedirect.com')


class ElsevierTableData(Entity):
    """ Embedded row data from document tables"""
    rows = StringField('td', all=True)


class ElsevierTable(Entity):
    """Table within document."""
    title = StringField('span[class="label"]')
    column_headings = StringField('th', all=True)
    data = EntityField(ElsevierTableData, 'tbody', all=True)
    caption = StringField('div[class="caption"]', all=True)
    process_title = Chain(elsevier_substitute, normalize)
    process_title = Chain(elsevier_substitute, normalize)


class ElsevierHtmlDocument(DocumentEntity):
    """Scraper of document information from Elsevier html papers"""

    doi = StringField(
        'substring-before(substring-after(//script[contains(.,"SDM.doi")]/text(), "SDM.doi = "), ";")', xpath=True)
    title = StringField('//title', xpath=True)
    authors = StringField(
        '//ul[@class="authorGroup noCollab svAuthor"]', xpath=True)
    abstract = StringField(
        '//div[@class="abstract svAbstract "]/p', xpath=True)
    journal = StringField('//div[@class="title"]/a', xpath=True)
    volume = StringField('//p[@class="volIssue"]', xpath=True)
    copyright = StringField('//p[@class="copyright"]', xpath=True)
    headings = StringField('//h2[@id]', xpath=True, all=True)
    sub_headings = StringField(
        '//h3[@class="svArticle"]', xpath=True, all=True)
    html_url = UrlField('//meta[@name="dc.identifier"]/@content', xpath=True)
    paragraphs = StringField(
        '//p[@class="svArticle section clear"]', xpath=True, all=True)
    figures = EntityField(ElsevierImage, 'dl[class="figure"]', all=True)
    published_date = StringField('//dl[@class="articleDates smh"]', xpath=True)
    citations = StringField('//ul[@class="reference"]', xpath=True, all=True)
    tables = EntityField(ElsevierTable, 'dl[class="table "]', all=True)


class ElsevierHtmlScraper(UrlScraper):
    """ Scraper for Elsever html paper pages """
    entity = ElsevierHtmlDocument


class ElsevierXmlImage(Entity):
    caption = StringField('simple-para')
    label = StringField('label')


class ElsevierXmlTableData(Entity):
    rows = StringField('entry', all=True)


class ElsevierXmlTable(Entity):
    label = StringField('label')
    caption = StringField('caption')
    column_headings = EntityField(ElsevierXmlTableData, 'thead row', all=True)
    data = EntityField(ElsevierXmlTableData, 'tbody row', all=True)


class ElsevierXmlDocument(Entity):
    """ Scraper for Elsevier XML articles """

    doi = StringField('doi')
    title = StringField('title')
    authors = StringField('creator', all=True)
    abstract = StringField('abstract, ce|abstract-sec, ce|abstract')
    journal = StringField('publicationName')
    volume = StringField('volume')
    issue = StringField('issn')
    pages = StringField('pageRange')
    firstpage = StringField('startingPage')
    lastpage = StringField('endingPage')
    copyright = StringField('copyright')
    publisher = StringField('publisher')
    headings = StringField('section-title', all=True)
    url = UrlField('url')
    paragraphs = StringField('para', all=True)
    figures = EntityField(ElsevierXmlImage, 'figure', all=True)
    published_date = StringField('coverDate')
    citations = StringField('bib-reference', all=True)
    tables = EntityField(ElsevierXmlTable, 'table', all=True)

    process_abstract = Chain(LStrip(), RStrip(), LStrip('Abstract'))
