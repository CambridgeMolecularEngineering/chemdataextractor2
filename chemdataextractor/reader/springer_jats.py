# -*- coding: utf-8 -*-
"""
chemdataextractor.reader.springerjats

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Springer XML reader for the JATS format

author: Shu Huang <sh2009@cam.ac.uk>
"""
from ..scrape.clean import clean, Cleaner
from ..doc.meta import MetaData
from .markup import XmlReader

# XML stripper that removes the tags around numbers in chemical formulas
strip_spr_xml = Cleaner(strip_xpath='.//bold | .//label | .//xref | .//italic | .//sub | .//sup',
                        kill_xpath='.//tex-math | .//alternatives | .//mml:math | .//label')


class SpringerJatsReader(XmlReader):
    """Reader for Springer XML documents."""

    cleaners = [clean, strip_spr_xml]

    root_css = 'article'
    title_css = 'article-title'
    heading_css = 'title'
    reference_css = 'xref'
    citation_css = 'ref'
    abstract_css = 'abstract'
    table_css = 'ce|table'
    figure_css = 'graphic'

    metadata_css = 'front'
    metadata_title_css = 'article-title'
    metadata_author_css = 'surname'
    metadata_journal_css = 'journal-title'
    metadata_volume_css = 'volume'
    metadata_issue_css = 'issue'
    metadata_publisher_css = 'publisher-name'
    metadata_day_css = 'day'
    metadata_month_css = 'month'
    metadata_year_css = 'year'
    metadata_firstpage_css = 'fpage'
    metadata_lastpage_css = 'lpage'
    metadata_abstract_css = 'abstract'
    metadata_doi_css = 'article-id[pub-id-type="doi"]'

    ignore_css = 'tex-math, label, table'

    def detect(self, fstring, fname=None):
        """Springer document detection based on string found in xml"""
        if fname and not fname.endswith('.xml'):
            return False
        if b'dtd-version="1.2"' in fstring:
            return True
        return False

    def _parse_metadata(self, el, refs, specials):
        title = self._css(self.metadata_title_css, el)
        authors = self._css(self.metadata_author_css, el)
        publisher = self._css(self.metadata_publisher_css, el)
        journal = self._css(self.metadata_journal_css, el)
        day = self._css(self.metadata_day_css, el)
        month = self._css(self.metadata_month_css, el)
        year = self._css(self.metadata_year_css, el)
        volume = self._css(self.metadata_volume_css, el)
        issue = self._css(self.metadata_issue_css, el)
        firstpage = self._css(self.metadata_firstpage_css, el)
        lastpage = self._css(self.metadata_lastpage_css, el)
        doi = self._css(self.metadata_doi_css, el)
        month = '0' + month[0].text if len(month[0].text) == 1 else month[0].text
        day = '0' + day[0].text if len(day[0].text) == 1 else day[0].text
        date = year[0].text + month + day

        metadata = {
                '_title': title[0].text if title else None,
                '_authors': [i.text for i in authors] if authors else None,
                '_publisher': publisher[0].text if publisher else None,
                '_journal': journal[0].text if journal else None,
                '_date': date if date else None,
                '_volume': volume[0].text if volume else None,
                '_issue': issue[0].text if issue else None,
                '_firstpage': firstpage[0].text if firstpage else None,
                '_lastpage': lastpage[0].text if lastpage else None,
                '_doi': doi[0].text if doi else None,
                }
        meta = MetaData(metadata)
        return [meta]
