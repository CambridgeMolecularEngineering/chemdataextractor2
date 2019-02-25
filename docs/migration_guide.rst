.. role:: python(code)
   :language: python

******************************************
v1.5.0 Migration Guide
******************************************

Overview
=================================

Previously, ChemDataExtractor required huge amounts of manual input to create parsers for new models and if the user had multiple new models that were similar, we resulted in huge amounts of duplicated code within the parse model. This system was very user-unfriendly and didn't really follow the logic of how Physics and Chemistry is structured.

Furthermore, the Interdependency Resolution (IR) for these models was purely backwards-looking and did not account for dynamic or document-specific terminology that was clearly defined in the text.

To resolve some of these issues we have developed a new model-based approach to parsing, that intrinsically links the models and the parsers, enabling completely automated parser creation and forward-looking Interdependecy Resolutioin.

This has resulted in some breaking changes to the API for ChemDataExtractor, however, these are all fixable with minor changes to existing code, which are outlined in the section `Migrating Existing Code`_.

Changes to ChemDataExtractor
=================================

Overall Structure
-------------------------

At a high level, in previous versions of ChemDataExtractor, the :python:`Document` class and each of its subelements (e.g. :python:`Paragraph` or :python:`Sentence`) had a list of parsers. These parsers each had an associated model which they were parsing for. When these parsers found a sentence (or table cell) that contained the requisite elements, it would create a :python:`Compound` and the property would be associated to this instance of a compound.

The new structure changes this hierarchy slightly. The :python:`Document` class and its subelements now own models that the documents should look for. Each model contains a list of parsers that can be used for parsing different types of elements (e.g. :python:`Sentence` or :python:`Table`) to extract the model. At the appropriate timings, the elements will call the appropriate parsers in the model.

This new structure has several advantages:

- You no longer has to search for the appropriate classes for parsing. You don't need to find :python:`MpParser` and :python:`MpTableParser` and assign them as parsers to :python:`Sentences` and :python:`Tables` respectively to extract a :python:`MeltingPoint`. With the new model, one just passes in a list, :python:`[MeltingPoint, Compound]`, to document, and the appropriate parsers are automatically used.

- The new structure is far safer, that is, it is impossible to use a parser meant for tables on a sentence and a parser meant for sentences on tables.

- The properties are no longer neccesarily tied to the :python:`Compound` class, meaning one could use ChemDataExtractor for other purposes too, such as extracting the conditions under which an experiment was done.

Changes to Models
----------------------------------

In addition to the overall change of structure, involving each property optionally owning a Compound, new types of models have  been introduced for the majority usecase, of extracting a physical quantity structure, i.e. the case with a specifier, a value, and units, such as melting points, interatomic distances, and cooling rates. These models are all defined as subclasses of a new type of model, :python:`QuantityModel`

.. note::

    While new Quantity-based models have been added to ChemDataExtractor, old-style models can still be used. Refer to the section `Migrating Existing Code`_ on how to have older models be extracted as similarly to the old behaviour as possible.

These model types can now be defined with minimal effort as the various base-quantities (Temperature, Length, Time etc) are included in ChemDataExtractor. Now for example, if we wished to create a new model that will be of type Temperature we simply inherit our model from the :python:`TemperatureModel` class and define our entities.

Models of this type have only 2 requirements:

- A specifier parse expression (Optional, only required if autoparsers are desired)
- If applicable, a compound entity, named :python:`compound`

While previous models in ChemDataExtractor stored values and units as strings, these are now automatically extracted and stored as numbers and Unit classes, allowing for easy conversion and comparison. These changes are explored in more detail in `Addition of Units and Dimensions`_.

Each entity must have a defined type, for example :python:`StringType`, :python:`FloatType` or :python:`ModelType`. Note that by specifying :python:`ModelType` you must provide another model, allowing for nested model relationships.

The entities also have properties:

- :python:`required`: Whether or not the entitiy is required to form a relationship, if the entity is not found, the relationship will not be output by ChemDataExtractor.
- :python:`contextual`: Whether or not the entity can be sourced from a different element to the rest of the entities, e.g. whether the entity can be completed with data from another sentence.
- :python:`mutable`: Whether or not the parse_expression can be updated based on definitions found in the document (see `Forward looking Interdependency resolution`_)

We can also add arbitrarily-named entities with any parse expressions we like.
Example::

    from models.units.temperature import TemperatureModel

    #: My new model for finding Boiling points
    class BoilingPoint(TemperatureModel):
        specifier = StringType(parse_expression=I('boiling')+I('point'),
                               required=True,
                               contextual=True,
                               mutable=True)
        compound = ModelType(Compound,
                             required=True,
                             contextual=False,
                             mutable=False)
        random_entity = StringType(parse_expression=I('complete')+I('nonsense'))

Some model types have not yet been defined. An example of how to create a new model is included in the Examples.

Addition of Units and Dimensions
--------------------------------

Newly included in ChemDataExtractor are the concepts of :python:`Unit` s and :python:`Dimension` s. These work just as expected; each :python:`Unit` has a dimension and quantities with the same :python:`Unit` s can be converted between each other. See the API documentation for :python:`model.units` for more information.

Changes to Parsers
--------------------

Previously, different types of parsers were just distinguished by name. A :python:`MpTableParser` was understood to parse tables, and :python:`MpParser` was understood to parse Sentences. However, this was not enforced in any way. This has now been changed, with all parsers now implementing either :python:`parse_sentence` if they are sentence parsers, or :python:`parse_cell` if a table parser. You can get these methods for free by subclassing from :python:`BaseSentenceParser` and :python:`BaseTableParser` respectively. You then only need to implement the interpret function, just as before.

To work with the models now being able to store values and units in a more structured manner, :python:`BaseParser` now contains new methods for extracting them. Refer to the API documentation for it for more detail.

Forward looking Interdependency Resolution
------------------------------------------

More often than not, the specifier you define in your model will be insufficient at capturing all variations of the way in which the model is defined in text. In most cases, the specifier is given a short abbreviation such as:

"...the boiling point, bp,..."

Using the definition parsers within ChemDataExtractor, we now automatically update specifier entities within local document scope when these definitions are found. This means that the specifier parse-expression gets automatically updated to include the new definition. Following the example above, the new specifier parse expression will become::

(I('boiling') + I('point')) | I('bp')

Then for all remaining elements in the document, the relationship will be found if this specifier is used.

Note: This information only persists in the current document, so when a new document is parsed, we revert to the default defined specifier.

Integration with TableDataExtractor
-----------------------------------

TableDataExtractor is a new toolkit for ChemDataExtractor that vastly enhances its capabilities for table data extraction. It reads all tables and outputs the data from them in a highly standardised format whilst also retaining information about things including subheadings. More information can be found in the TableDataExtractor documentation, also available online.

Automatic Parsers
----------------------------------

All of the above enhancements to ChemDataExtractor mean that the extraction is much more powerful and context-rich. The forward-looking Interdependency Resolution means that one no longer needs to manually specify as many specifiers when looking for new properties, and the quantity extraction involving units and dimensions means that we have rich new metadata on our extracted values.

We have taken advantage this new data to create automatic parsers for both sentences and tables. Any subclasses of :python:`QuantityModel` have, by default, automatic parsers enabled, meaning no user intervention is needed to start extracting. These automatic parsers work expecially well with the TableDataExtractor tables, which have the data in a highly standardised format, meaning that more basic parsers can still work exceptionally well.

.. note::

    These parsers rely on the specifier and units information provided in :python:`Quantitymodel`, so cannot be used with existing subclasses of :python:`BaseModel` s.

Migrating Existing Code
=================================

This section is aimed at moving existing code to run in ChemDataExtractor 1.5.0 without adding any new functionality. For information on how to take advantage of the new features please refer to `Upgrading Existing Code`_.

Migrating Models
-----------------
When a model was previously written, a reference to the model would need to be created from Compound. This no longer needs to be done, so where the old version would have been::

    from chemdataextractor.model import BaseModel, StringType, ListType, ModelType
    from chemdataextractor.model import Compound

    class BoilingPoint(BaseModel):
        value = StringType()
        units = StringType()

    Compound.boiling_points = ListType(ModelType(BoilingPoint))

The new way to write this would be::

    from chemdataextractor.model import BaseModel, StringType, ModelType
    from chemdataextractor.model import Compound

    class BoilingPoint(BaseModel):
        value = StringType()
        units = StringType()
        compound = ModelType(Compound)
        parsers = [BpParser()]

Where BpParser will be explained in the next section.

Migrating Parsers
-----------------

The old way to write a parser would be to explicitly import the model and create it. This is no longer necessary, as all parsers contain a :python:`model` attribute which is set at the required timing by the model. this means that a parser written before as::

    import re
    from chemdataextractor.parse import R, I, W, Optional, merge
    from chemdataextractor.parse.base import BaseParser
    from chemdataextractor.utils import first

    prefix = (R(u'^b\.?p\.?$', re.I) | I(u'boiling') + I(u'point')).hide()
    units = (W(u'°') + Optional(R(u'^[CFK]\.?$')))(u'units').add_action(merge)
    value = R(u'^\d+(\.\d+)?$')(u'value')
    bp = (prefix + value + units)(u'bp')

    class BpParser(BaseParser):
        root = bp

        def interpret(self, result, start, end):
            compound = Compound(
                boiling_points=[
                    BoilingPoint(
                        value=first(result.xpath('./value/text()')),
                        units=first(result.xpath('./units/text()'))
                    )
                ]
            )
            yield compound

would now be written as::

    import re
    from chemdataextractor.parse import R, I, W, Optional, merge
    from chemdataextractor.parse.base import BaseSentenceParser
    from chemdataextractor.utils import first
    from chemdataextractor.model import Compound

    prefix = (R(u'^b\.?p\.?$', re.I) | I(u'boiling') + I(u'point')).hide()
    units = (W(u'°') + Optional(R(u'^[CFK]\.?$')))(u'units').add_action(merge)
    value = R(u'^\d+(\.\d+)?$')(u'value')
    bp = (prefix + value + units)(u'bp')

    class BpParser(BaseSentenceParser):
        root = bp

        def interpret(self, result, start, end):
            boiling_point = self.model(value=first(result.xpath('./value/text()')),
                                       units=first(result.xpath('./units/text()')))
            boiling_point.compound = Compound()
            yield boiling_point

Note also that the parser now inherits from :python:`BaseSentenceParser` as opposed to :python:`BaseParser` as it is a parser for sentences.

Extracting Properties
-----------------------

To extract a certain model, prior to 1.5.0, one had to set the parsers or the document. Instead of this, you now pass in the model that you want to extract from the document, so instead of this::

    document.parsers = [BpParser()]

you would write::

    document.models = [BoilingPoint]

Note that you should now pass in the class for the model we are parsing instead of an instance of the parser as before.


Upgrading Existing Code
=============================

The above small alterations are enough to get your code up and running, but to make the most of what ChemDataExtractor 1.5.0, you can upgrade your existing codebase to extract richer properties more easily.

Upgrading Models
------------------

A key new feature of version 1.5.0 are the new :python:`QuantityModel` s. These new models are much more versatile in that they extract values and errors as floats (or lists of floats), and units are properly identified and extracted. If your existing models are already of one of the dimensions defined in ChemDataExtractor, i.e. Length, Mass, Time, or Temperature, then it's easy. Just remove value and units properties, as those are included by default, and write the model as a subclass of the appropriate model.

For example, the :python:`BoilingPoint` class we wrote earlier can be further transformed::

    from chemdataextractor.model import TemperatureModel, StringType, ModelType
    from chemdataextractor.model import Compound

    class BoilingPoint(TemperatureModel):
        compound = ModelType(Compound)
        parsers = [BpParser()]

Defining your own dimensions is also easy; an example of how it's done within ChemDataExtractor for temperatures is provided below, and further information can be found in the API documentation for model.units. ::

    from __future__ import absolute_import
    from __future__ import division
    from __future__ import print_function
    from __future__ import unicode_literals

    import logging

    from .quantity_model import QuantityModel
    from .unit import Unit
    from .dimension import Dimension
    from ...parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
    from ...parse.actions import merge, join

    log = logging.getLogger(__name__)


    class Temperature(Dimension):
        """
        Dimension subclass for temperatures.
        """
        pass


    class TemperatureModel(QuantityModel):
        """
        Model for temperatures.
        """
        dimensions = Temperature()


    class TemperatureUnit(Unit):
        """
        Base class for units with dimensions of temprature.
        The standard value for temperature is defined to be a Kelvin, implemented in the Kelvin class.
        """

        def __init__(self, magnitude=0.0, powers=None):
            super(TemperatureUnit, self).__init__(Temperature(), magnitude, powers)


    class Kelvin(TemperatureUnit):
        """
        Class for Kelvins.
        """

        def convert_value_to_standard(self, value):
            return value

        def convert_value_from_standard(self, value):
            return value

        def convert_error_to_standard(self, error):
            return error

        def convert_error_from_standard(self, error):
            return error


    class Celsius(TemperatureUnit):
        """
        Class for Celsius
        """

        def convert_value_to_standard(self, value):
            return value + 273.15

        def convert_value_from_standard(self, value):
            return value - 273.15

        def convert_error_to_standard(self, error):
            return error

        def convert_error_from_standard(self, error):
            return error


    class Fahrenheit(TemperatureUnit):
        """
        Class for Fahrenheit.
        """

        def convert_value_to_standard(self, value):
            return (value + 459.67) * (5. / 9.)

        def convert_value_from_standard(self, value):
            return value * (9. / 5.) - 459.67

        def convert_error_to_standard(self, error):
            return error * (5. / 9.)

        def convert_error_from_standard(self, error):
            return error * (9. / 5.)


    units_dict = {R('°?(((K|k)elvin(s)?)|K)\.?', group=0): Kelvin,
                  R('(°|((C|c)elsius|°?C))\.?', group=0): Celsius,
                  R('°?((F|f)ahrenheit|F)\.?', group=0): Fahrenheit}
    Temperature.units_dict = units_dict


Upgrading Parsers
------------------

To define this model is great, but we also need to upgrade the parser to make sure that these properties are actually extracted. Let's continue with the boiling point example to see how we'd change :python:`BpParser` to make it extract this information. ::

    import re
    from chemdataextractor.parse import R, I, W, Optional, merge
    from chemdataextractor.parse.base import BaseSentenceParser
    from chemdataextractor.utils import first
    from chemdataextractor.model import Compound

    prefix = (R(u'^b\.?p\.?$', re.I) | I(u'boiling') + I(u'point')).hide()
    units = (W(u'°') + Optional(R(u'^[CFK]\.?$')))(u'units').add_action(merge)
    value = R(u'^\d+(\.\d+)?$')(u'value')
    bp = (prefix + value + units)(u'bp')

    class BpParser(BaseParser):
        root = bp

        def interpret(self, result, start, end):
            try:
                raw_value = first(result.xpath('./value/text()'))
                raw_units = first(result.xpath('./units/text()'))
                boiling_point = self.model(raw_value=raw_value,
                            raw_units=raw_units,
                            value=self.extract_value(raw_value),
                            error=self.extract_error(raw_value),
                            units=self.extract_units(raw_units, strict=True),
                            compound=Compound())
                yield boiling_point
            except TypeError as e:
                log.debug(e)

Using Automatic Parsers
----------------------------

This is actually the easiest part of upgrading to take advantage of 1.5.0's features; you only need to add a basic specifier and not set your own parsers, then ChemDataExtractor will handle it all for you. ::

    from chemdataextractor.model import TemperatureModel, StringType, ModelType
    from chemdataextractor.model import Compound

    class BoilingPoint(TemperatureModel):
        specifier = StringType(parse_expression=I('Boiling') + I('Point'))
        compound = ModelType(Compound)

Alternatively, if you want to use the automatic parsers and also the parser you wrote yourself, you can do the following::

    from chemdataextractor.model import TemperatureModel, StringType, ModelType
    from chemdataextractor.model import Compound
    from chemdataextractor.parse.auto import AutoSentenceParser, AutoTableParser

    class BoilingPoint(TemperatureModel):
        specifier = StringType(parse_expression=I('Boiling') + I('Point'))
        compound = ModelType(Compound)
        parsers = [BpParser(), AutoSentenceParser(), AutoTableParser()]





