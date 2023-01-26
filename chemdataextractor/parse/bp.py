from chemdataextractor.parse import R, I, W, Optional, merge
from chemdataextractor.parse.base import BaseParser
from chemdataextractor.utils import first
from chemdataextractor.model import BoilingPoint
from chemdataextractor.doc import Paragraph

log = logging.getLogger(__name__)

prefix = (R(u'^b\.?p\.?$', re.I) | I(u'boiling') + I(u'point')).hide()

units = (W(u'°') + Optional(R(u'^[CFK]\.?$')))(u'raw_units').add_action(merge)

value = R(u'^\d+(\.\d+)?$')(u'raw_value')

bp = (prefix + value + units)(u'bp')

class BpParser(BaseParser):
    root = bp

    def interpret(self, result, start, end):
        try:
            raw_value = first(result.xpath('./value/text()'))
            raw_units = first(result.xpath('./units/text()'))
            boiling_point = self.model(raw_value = raw_value,
                raw_units = raw_units,
                value = self.extract_value(raw_value),
                error = self.extract_error(raw_value),
                units = self.extract_units(raw_units, strict = True))
            yield boiling_point
        except TypeError as e:
            log.debug(e)

BoilingPoint.parsers = [BpParser()]
Paragraph.parses = [BpParser()]