# -*- coding: utf-8 -*-
"""
Figure document elements.
:codeauthor:: Callum Court (cc889@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging

from .element import CaptionedElement
from ..model import ModelList, Compound
log = logging.getLogger(__name__)


class Figure(CaptionedElement):

    def __init__(self, caption, label=None, links=None, models=None, **kwargs):
        """
        Create a new Figure element, to interface with FDE
        """
        super(Figure, self).__init__(caption=caption, label=label, models=models, **kwargs)
        self.links = links
        self.caption_tokens = None

    @property
    def records(self):
        """ Return FigureData records

        Returns:
            [type] -- [description]
        """
        records = ModelList()
        seen_labels = set()
        skip_parsers = self.document.skip_parsers if self.document is not None else []

        p = None

        if not self.caption_tokens:
            self.caption_tokens = []
            for sent in self.caption.sentences:
                self.caption_tokens.extend(sent.tokens)

        for model in self._streamlined_models:
            for parser in model.parsers:
                if parser in skip_parsers:
                    # print(f"Figure Skipped: {parser.model}")
                    continue
                parser_records = []

                if hasattr(parser, 'parse_caption'):
                    for record in parser.parse_caption(self.caption, self.label, self.links):
                        parser_records.append(record)

                elif hasattr(parser, 'parse_sentence'):
                    for caption_sentence in self.caption.sentences:
                        for subsentence in caption_sentence.subsentences:
                            for record in parser.parse_sentence(subsentence):
                                parser_records.append(record)
                else:
                    continue

                if not parser_records:
                    continue

                for record in parser_records:
                    p = record.serialize()
                    if not p:  # TODO: Potential performance issues?
                        continue
                    # Skip duplicate records
                    if record in records:
                        continue
                    # Skip just labels that have already been seen (bit of a hack)
                    if (isinstance(record, Compound) and 'Compound' in p.keys() and all(k in {'labels', 'roles'} for k in p['Compound'].keys()) and
                        set(record.labels).issubset(seen_labels)):
                        continue
                    if isinstance(record, Compound):
                        seen_labels.update(record.labels)
                        # This could be super slow if we find lots of things
                        found = False
                        for seen_record in records:
                            if (isinstance(seen_record, Compound)
                                and (not set(record.names).isdisjoint(seen_record.names)
                                    or not set(record.labels).isdisjoint(seen_record.labels))):
                                seen_record.names = sorted(list(set(seen_record.names).union(record.names)))
                                seen_record.labels = sorted(list(set(seen_record.labels).union(record.labels)))
                                seen_record.roles = sorted(list(set(seen_record.roles).union(record.roles)))
                                found = True
                        if found:
                            continue
                    elif hasattr(record, 'compound') and record.compound is not None:
                        seen_labels.update(record.compound.labels)
                    records.append(record)
        i = 0
        length = len(records)
        while i < length:
            j = 0
            while j < length:
                if i != j:
                    records[j].merge_all(records[i])
                j += 1
            i += 1

        cleaned_records = []
        for record in records:
            record._clean(clean_contextual=False)
            if record.noncontextual_required_fulfilled:
                cleaned_records.append(record)

        sorted_records = ModelList(*sorted(cleaned_records, key=lambda el: el.total_confidence() if el.total_confidence() is not None else -10000, reverse=True))
        return sorted_records

    def _repr_html_(self):
        html_lines = ['<figure>', self.caption._repr_html_(), '</figure>']
        # TODO: img element with figure URL
        return '\n'.join(html_lines)
