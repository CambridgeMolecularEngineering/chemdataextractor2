# -*- coding: utf-8 -*-
"""
MetaData Document elements

"""
from .element import BaseElement
from ..model.base import ModelList
import logging
log = logging.getLogger(__name__)

class MetaData(BaseElement):

    def __init__(self, data):
        super(MetaData, self).__init__()
        self._data = data
        self._title = None
        self._authors = None
        self._publisher = None
        self._journal = None
        self._volume = None
        self._issue = None
        self._firstpage = None
        self._lastpage = None
        self._doi = None
        self._date = None
        self._language = None
        self._pdf_url = None
        self._html_url = None
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return {k: v for k, v in self.data.items() if v}.__str__()

    @property
    def records(self):
        return []

    def serialize(self):
        return {'MetaData': {k: v for k, v in self.data.items() if v}}

    @property
    def title(self):
        """The article title"""

        return self._title

    @property
    def authors(self):
        """The article Authors
        type:: list()
        """
        return self._authors

    @property
    def publisher(self):
        """The source publisher"""
        return self._publisher

    @property
    def journal(self):
        """The source journal"""
        return self._journal

    @property
    def volume(self):
        """The source volume"""
        return self._volume

    @property
    def issue(self):
        """The source issue"""
        return self._issue

    @property
    def firstpage(self):
        """The source first page title"""
        return self._firstpage

    @property
    def lastpage(self):
        """The source last page"""
        return self._lastpage

    @property
    def doi(self):
        """The source DOI"""
        return self._doi

    @property
    def pdf_url(self):
        """The source url to the PDF version"""
        return self._pdf_url

    @property
    def html_url(self):
        """The source url to the HTML version"""
        return self._html_url

    @property
    def date(self):
        """The source publish date"""
        return self._date

    @property
    def data(self):
        """Returns all data as a dict()"""
        return {k.lstrip('_'): v for k, v in self._data.items()}

    @property
    def abbreviation_definitions(self):
        return []

    @property
    def definitions(self):
        return []

    @property
    def chemical_definitions(self):
        return []
    
    @property
    def cems(self):
        return []

    @property
    def is_unidentified(self):
        return False