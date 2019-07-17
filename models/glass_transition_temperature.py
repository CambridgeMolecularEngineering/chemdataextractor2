from ..chemdataextractor.model.units import TemperatureModel
from ..chemdataextractor.model.model import Compound, ModelType, StringType
from ..chemdataextractor.parse.elements import R, W, Not
from ..chemdataextractor.parse.actions import join
from ..chemdataextractor.parse.template import QuantityModelTemplateParser, MultiQuantityModelTemplateParser
from ..chemdataextractor.parse.auto import AutoSentenceParser, AutoTableParser


class GlassTransitionTemperature(TemperatureModel):
    specifier_expr = ((R('[Gg]lass') + R('transition') + R('temperature')) | ((R('^Tg$'))+Not(W('/')))).add_action(join)
    specifier = StringType(parse_expression=specifier_expr, required=True, contextual=True, updatable=True)
    compound = ModelType(Compound, required=True, contextual=True)
    parsers = [MultiQuantityModelTemplateParser(), QuantityModelTemplateParser(), AutoTableParser()]


# The Snowball model has compound contextual = 'False' in order not to be wrongly found by the AutoSentenceParser
class GlassTransitionTemperatureSB(TemperatureModel):
    specifier_expr = ((R('[Gg]lass') + R('transition') + R('temperature')) | ((R('^Tg$'))+Not(W('/')))).add_action(join)
    specifier = StringType(parse_expression=specifier_expr, required=True, contextual=False, updatable=True)
    compound = ModelType(Compound, required=True, contextual=False)
