.. _migration_guide:

.. role:: python(code)
   :language: python

******************************************
v1.5.0 Migration Guide
******************************************

Overview
=================================

Previously, ChemDataExtractor required huge amounts of manual input to create parsers for new models and if the user had multiple new models that were similar, we ended up with huge amounts of duplicated code. This system was very user-unfriendly and didn't really follow the logic of how Physics and Chemistry are structured.

Furthermore, the Interdependency Resolution (IR) for these models was purely backwards-looking and did not account for dynamic or document-specific terminology even when it was clearly defined in the text.

To resolve some of these issues we have developed a new model-based approach to parsing that intrinsically links the models and the parsers, enabling completely automated parser creation and forward-looking Interdependency Resolution.

This has resulted in some breaking changes to the API for ChemDataExtractor, however, these are all fixable with minor changes to existing code, which are outlined in the section `Migrating Existing Code`_.

Changes to ChemDataExtractor
=================================

Overall Structure
-------------------------

At a high level, in previous versions of ChemDataExtractor, the :class:`~chemdataextractor.doc.document.Document` class and each of its subelements (e.g. :class:`~chemdataextractor.doc.text.Paragraph`, :class:`~chemdataextractor.doc.table.Table` or :class:`~chemdataextractor.doc.text.Sentence`) had a list of parsers. These parsers each had an associated model which they were parsing for. When these parsers found a sentence (or table cell) that matched to the parse phrase root, it would create a :class:`~chemdataextractor.doc.text.Compound` and the property would be associated to this instance of a compound.

The new structure changes this hierarchy significantly. The :class:`~chemdataextractor.doc.document.Document` class and its subelements now own the models that they should look for. Each model contains a list of parsers that can be used for parsing different types of elements (e.g. :class:`~chemdataextractor.doc.text.Sentence` or :class:`~chemdataextractor.doc.table_new.Table`) to extract the model. At the appropriate timings, the elements will call the appropriate parsers in the models.

This new structure has several advantages:

- You no longer have to search for the appropriate classes for parsing. You don't need to find :class:`~chemdataextractor.parse.mp_new.MpParser` and :class:`~chemdataextractor.parse.table.MpTableParser` and assign them as parsers to :class:`~chemdataextractor.doc.text.Sentence` s and :class:`~chemdataextractor.doc.table_new.Table` s respectively to extract a :class:`~chemdataextractor.model.model.MeltingPoint`. With the new structure, you just pass in a list, :python:`[MeltingPoint, Compound]`, to document, and the appropriate parsers are automatically used.

- The new structure is far safer, that is, it is impossible to use a parser meant for tables on a sentence and a parser meant for sentences on tables.

- The properties are no longer necessarily tied to the :class:`~chemdataextractor.model.models.Compound` class, meaning one could use ChemDataExtractor for other purposes too, such as extracting the conditions under which an experiment was done.

- You can easily build nested model hierarchies that more closely resemble the structure of Physics and Chemistry.

Changes to Models
----------------------------------

In addition to the overall change of structure, involving each property optionally owning a :class:`~chemdataextractor.model.model.Compound`, new types of models have  been introduced for the majority usecase of extracting a physical quantity structure, i.e. the case with a specifier, a value, and units, such as melting points, interatomic distances, and cooling rates.
These models are all defined as subclasses of a new type of model, :class:`~chemdataextractor.model.units.quantity_model.QuantityModel`.

.. note::

    While new Quantity-based models have been added to ChemDataExtractor, old-style models can still be used. Refer to the section `Migrating Existing Code`_ on how to have older models be extracted as similarly to the old behaviour as possible.

These model types can now be defined with minimal effort as the various base-quantities (Temperature, Length, Time etc) are included in ChemDataExtractor. Now for example, if we wished to create a new model that will be of type Temperature we simply inherit our model from the :class:`~chemdataextractor.model.units.temperature.TemperatureModel` class and define our entities.

Models of this type have only 2 requirements:

- A specifier with an associated parse expression (Optional, only required if autoparsers are desired). These parse expressions will be updated automatically using forward-looking Interdependency Resolution if the :python:`updatable` flag is set to :python:`True`.
- If applicable, a compound entity, named :python:`compound`

While previous models in ChemDataExtractor stored values and units as strings, these are now automatically extracted and stored as numbers and :class:`~chemdataextractor.model.units.unit.Unit` s, allowing for easy conversion and comparison. These changes are explored in more detail in `Addition of Units and Dimensions`_.

Each entity must have a defined type, for example :class:`~chemdataextractor.model.base.StringType`, :class:`~chemdataextractor.model.base.FloatType` or :class:`~chemdataextractor.model.base.ModelType`. Note that by specifying :class:`~chemdataextractor.model.base.ModelType` you must provide another model, allowing for nested model relationships.

The entities also have properties:

- :python:`parse_expression`: A :class:`~chemdataextractor.parse.elements.BaseElement` that is associated with the entity. This parse expression is used by the autoparser in constructing a parse rule.

- :python:`required`: Whether or not the entity is required to form a relationship. If required is :python:`True` and the entity is not found, the relationship will not be output by ChemDataExtractor.

- :python:`contextual`: Whether or not the entity can be sourced from a different element to the rest of the entities, e.g. whether the entity can be completed with data from another sentence, or a different part of the table.

- :python:`updatable`: Whether or not the :python:`parse_expression` can be updated based on definitions found in the document (see `Forward looking Interdependency resolution`_)

We can also add arbitrarily-named entities with any parse expressions we like.
Example::

    from models.units.temperature import TemperatureModel

    #: My new model for finding Boiling points
    class BoilingPoint(TemperatureModel):
        specifier = StringType(parse_expression=I('boiling')+I('point'),
                               required=True,
                               contextual=True,
                               updatable=True)
        compound = ModelType(Compound,
                             required=True,
                             contextual=False,
                             updatable=False)
        apparatus = ModelType(Apparatus, contextual=True)
        random_entity = StringType(parse_expression=I('complete')+I('nonsense'))

Notice also that we have added apparatus and compound as sub-models to :python:`BoilingPoint`. If we pass in :python:`BoilingPoint` to a document or a sentence, they will automatically also extract the apparatus and compound and associate them with the boiling point as required.

Model types for certain dimensions have not yet been defined. An example of how to create a new model is included in the Examples.

Addition of Units and Dimensions
--------------------------------

Newly included in ChemDataExtractor are the concepts of :class:`~chemdataextractor.model.units.unit.Unit` s and :class:`~chemdataextractor.model.units.dimension.Dimension` s. These work just as expected; each :class:`~chemdataextractor.model.units.unit.Unit` has a dimension and quantities with the same :class:`~chemdataextractor.model.units.unit.Unit` s can be converted between each other. See the API documentation for :mod:`chemdataextractor.model.units` for more information.

Changes to Parsers
--------------------

Previously, different types of parsers were just distinguished by name. A :class:`MpTableParser` was understood to parse tables, and :class:`~chemdataextractor.parse.mp_new.MpParser` was understood to parse sentences. However, this was not enforced in any way. This has now been changed, with all parsers now implementing either :meth:`~chemdataextractor.parse.base.BaseSentenceParser.parse_sentence` if they are sentence parsers, or :meth:`~chemdataextractor.parse.base.BaseTableParser.parse_cell` if a table parser. You can get these methods for free by subclassing from :class:`~chemdataextractor.parse.base.BaseSentenceParser` and :class:`~chemdataextractor.parse.base.BaseTableParser` respectively. You then only need to implement the interpret function, just as before.
The role of the interpret function is identical to before, it takes a parse result and formats it to the desired model.

To work with the models now being able to store values and units in a more structured manner, :class:`~chemdataextractor.parse.base.BaseParser` also now contains new methods for extracting them. Refer to the API documentation for more detail.

Forward looking Interdependency Resolution
------------------------------------------

More often than not, the specifier you define in your model will be insufficient for capturing all variations of the way in which the model is defined in text. In most cases, the specifier is given a short abbreviation such as:

"...the boiling point, bp,..."

Using the definition parsers within ChemDataExtractor, we now automatically update specifier entities at the document scope when these definitions are found. This means that the specifier parse-expression gets automatically updated to include the new definition. Following the example above, the new specifier parse expression will become::

(I('boiling') + I('point')) | I('bp')

Then for all remaining elements in the document, the relationship will be found if this specifier is used.

.. note::

    This information only persists in the current document, so when a new document is parsed, we revert to the default defined specifier. This is to avoid the specifier parse expressions becoming too far removed from the original definition.

Integration with TableDataExtractor
-----------------------------------

TableDataExtractor is a new toolkit for ChemDataExtractor that vastly enhances its capabilities for information extraction from tabular data.
Previously, rule-based parsers had to be written specifically for tables, for every new property. These would usually be very limited, due to the complexity of tables found in the literature.

TableDataExtractor reads all tables and outputs their data in a highly standardised format whilst also retaining information about all the row or column headings and subheadings that the data point belongs to. The output of TableDataExtractor is a *category table*, where each row corresponds to a single data-cell of the original table, along with its corresponding header structure.
The standardized structure of the category table enables fully automated parsing with ChemDataExtractor. Within ChemDataExtractor all of the functionality of TableDataExtractor can be accessed via an instance of the :class:`~chemdataextractor.doc.table_new.Table` object, ``table``, as ``table.tde_table``.

In most cases it should not be necessary to interact directly with TableDataExtractor. However, it is recommended to test it on an individual corpus of literature, before a production run.
Visual inspection is the best option to do so::

    from chemdataextractor import Document

    f = open('my_dicument.xml', 'rb')
    doc = Document.from_file(f)

    for table in document.tables:
        table.tde_table.print_raw_table()
        print(table.tde_table)

This will print the raw table, as found in the source document (before processing with TableDataExtractor) as well as the structured category table, :python:`table.tde_table`.
For more information the following TableDataExtractor functionality:

    * ``print(table.tde_table.history)`` will return information about the algorithms within TableDataExtractor that have been used on the particular table. If needed these can be tweaked by providing configuration parameters for TableDataExtractor (see TableDataExtractor documentation).
    * ``table.tde_table.print()`` will print a more verbose output that includes the raw input table, the cleaned table (cleaned-up by TableDataExtractor), as well as a table that shows the labelling of the sections of the table.
    * ``table.tde_table.to_pandas()`` outputs the table as Pandas DataFrame. This can be useful for further analysis.

More information can be found in the `TableDataExtractor documentation <https://cambridgemolecularengineering-tabledataextractor.readthedocs-hosted.com/en/latest/>`_.


Automatic Parsers
----------------------------------

Due to the built-in forward-looking Interdependency Resolution we no longer have to manually specify as many specifiers when looking for new properties. The quantity extraction involving units and dimensions provides rich new metadata on our extracted values.
These features make data extraction with ChemDataExtractor inherently much more powerful and context-rich.

We have taken advantage this new data to create automatic parsers for both sentences and tables. Any subclasses of :class:`~chemdataextractor.model.units.quantity_model.QuantityModel` have, by default, automatic parsers enabled, meaning no user intervention is needed to start extracting. These automatic parsers work especially well with the TableDataExtractor tables, which store the data in a highly standardised format. Thus, no user adjustments will be needed to extract data from tables.

.. note::

    These parsers rely on the specifier and units information provided in :class:`~chemdataextractor.model.units.quantity_model.QuantityModel`, and described above. Therefore, they cannot be used with existing subclasses of :class:`~chemdataextractor.model.base.BaseModel` and, if needed, new model classes resembling the old ones can be written for that purpose.


Integration with Snowball
-----------------------------------

Due to the new ability of ChemDataExtractor to construct simple parsers automatically, Snowball is now fully integrated into the ChemDataExtractor workflow. Still, training of the Snowball algorithm needs to be performed. However, this is now much simpler to invoke. The Snowball algorithm is simply another parser that can optionally be used and can be passed into the models in the same way as any other custom created parser. Here is an example of using Snowball to extract Curie temperatures::

    class CurieTemperature(TemperatureModel):
        specifier_expression = (I('Curie')+I('temperature') | I('TC')).add_action(join)
        specifier = StringType(parse_expression=specifier_expression, required=True, contextual=False, updatable=True)
        compound = ModelType(Compound, required=True, contextual=True)


    #1. Train from a single/multiple sentences/documents
    s = Sentence('Cobalt displays a Curie Temperature of 1388 K which is higher than BiFeO3.')
    corpus = [s]

    #2. Or train from a path to files
    corpus = './tests/data/relex/curie_training_set/'

    sb = Snowball(CurieTemperature)
    sb.train(corpus)
    CurieTemperature.parsers.append(sb)

Parsing
-----------------------------------

As a result we now have 3 different text parsing methods, each with its own advantages and disadvantages when it comes to extraction precision and recall.

The auto-generated text-parsers, of type :class:`~chemdataextractor.parse.auto.AutoSentenceParser` are very lenient. The root phrases for these parsers find any sentences that contain the required entities and return the first match to the models. As such, parsing with only the auto sentence parser will yield high recall but low precision.
Furthermore, you will only extract correct relations from sentences that contain single instances of your model.

Snowball parsing is the opposite end of the precision-recall spectrum. Snowball is designed to be high precision and low recall based on the training data.

Therefore, if you wish to extract with both high precision and high recall, you will still need to write parse rules for complicated sentence structures, or train Snowball very extensively.

On the other hand, if you only wish to extract data from tables, the automated table parsers normally don't require any further adjustments for simple models.

Migrating Existing Code
=================================

This section is aimed at migrating existing code to run in ChemDataExtractor 1.5.0 without adding any new functionality. For information on how to take advantage of the new features please also refer to `Upgrading Existing Code`_.

Migrating Models
-----------------
When a model was previously written, a reference to the model would need to be added to  Compound. This no longer needs to be done, so where the old version would have been::

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
            yield boiling_point

Note also that the parser now inherits from :class:`~chemdataextractor.parse.base.BaseSentenceParser` as opposed to :class:`~chemdataextractor.parse.base.BaseParser` as it is a parser for sentences.

Extracting Properties
-----------------------

To extract a certain model, prior to 1.5.0, one had to set the parsers or the document. Instead of this, you now pass in the model that you want to extract from the document, so instead of this::

    document.parsers = [BpParser()]

you would write::

    document.models = [BoilingPoint]

Note that you should now pass in the class for the model you are parsing instead of an instance of the parser as before.


Upgrading Existing Code
=============================

The above small alterations are enough to get your code up and running, but to make the most of what ChemDataExtractor 1.5.0, you can upgrade your existing codebase to extract richer properties more easily.

Upgrading Models
------------------

A key new feature of version 1.5.0 are the new :class:`~chemdataextractor.model.units.quantity_model.QuantityModel` classes. These new models are much more versatile in that they extract values and errors as floats (or lists of floats), and units are properly identified and extracted. If your existing models are already of one of the dimensions defined in ChemDataExtractor, i.e. Length, Mass, Time, or Temperature, then it's easy. Just remove value and units properties, as those are included by default, and write the model as a subclass of the appropriate model.

For example, the :python:`BoilingPoint` class we wrote earlier can be further transformed::

    from chemdataextractor.model import TemperatureModel, StringType, ModelType
    from chemdataextractor.model import Compound

    class BoilingPoint(TemperatureModel):
        compound = ModelType(Compound)
        parsers = [BpParser()]

Defining your own dimensions is also easy; an example of how it's done within ChemDataExtractor for temperatures is provided below, and further information can be found in the :mod:`API documentation <chemdataextractor.model.units>`, and in the documentation on :ref:`creating new units and dimensions<creating_units>`. ::

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
        Base class for units with dimensions of temperature.
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
                  R('(°C|((C|c)elsius))\.?', group=0): Celsius,
                  R('°?((F|f)ahrenheit|F)\.?', group=0): Fahrenheit,
                  R('°|C', group=0): None}
    # The final element in units_dict is given to ensure that '°C' is parsed correctly,
    # as the tokenizer splits it into two. When a parser element is assigned to None,
    # this means that this element will be ignored when extracting units, but will
    # be taken into account for autoparsers to extract from sentences.
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
                            units=self.extract_units(raw_units, strict=True))
                yield boiling_point
            except TypeError as e:
                log.debug(e)

Using Automatic Parsers
----------------------------

This is actually the easiest part of upgrading to take advantage of 1.5.0's features; you only need to add a basic specifier and not set your own parsers, then ChemDataExtractor will handle it all for you. ::

    from chemdataextractor.model import TemperatureModel, StringType, ModelType
    from chemdataextractor.model import Compound
    from chemdataextractor.parse.actions import join
    from chemdataextractor.parse import I

    class BoilingPoint(TemperatureModel):
        specifier = StringType(parse_expression=I('Boiling') + I('Point'), required=True)
        compound = ModelType(Compound)

Alternatively, if you want to use the parser you wrote yourself instead of the automatic sentence parser, you can do the following::

    from chemdataextractor.model import TemperatureModel, StringType, ModelType
    from chemdataextractor.model import Compound
       from chemdataextractor.parse.actions import join
    from chemdataextractor.parse import I
    from chemdataextractor.parse.auto import AutoSentenceParser, AutoTableParser


    class BoilingPoint(TemperatureModel):
        specifier = StringType(parse_expression=(I('Boiling') + I('Point')).add_action(join), required=True)
        compound = ModelType(Compound)
        parsers = [BpParser(), AutoTableParser()]

.. note::

    All parsers added to a class under parsers will be run on the document, so it's best not to have more than one parser which acts on the same type of element to avoid having a large number of duplicated results.

.. note::

    For autoparsers to work correctly, it is **strongly** recommended that you set :python:`required=True` on specifier, but in that case, it's also important that you set some value for the specifier (it doesn't matter what) when extracted with a manual parser, else the record will not be returned.

    Also key to making autoparsers work correctly is to always include :python:`add_action(join)` to the end of any parse expressions to ensure that multi-word parse expressions can be picked up correctly by the autoparser.

Preview: Nested Models
-----------------------

v1.5.0 brings the capability to nest models within other models. A simple example of this is that many models, such as the :python:`BoilingPoint` model we defined earlier, contains a model for compound. However, this also works with user-defined properties, and each of these models only needs to parse its surface-level properties, with everything else being merged in later. This nesting can in theory go multiple levels.

As a toy example, say we wanted to associate some additional properties to the boiling point, like the specific heat capacity of the material, and we're in turn interested in the dimensions of the apparatus used to measure the specific heat capacity::

    from chemdataextractor.model import TemperatureModel, LengthModel, StringType, ModelType, QuantityModel, Compound
    from chemdataextractor.model.units import Length, Mass, Temperature, Time
    from chemdataextractor.parse.actions import join
    from chemdataextractor.parse import I
    from chemdataextractor.doc import Document, Paragraph, Heading


    class ApparatusLength(LengthModel):
        specifier = StringType(parse_expression=(I('measured') + I('with')).add_action(join), required=True)


    class SpecificHeatCapacity(QuantityModel):
        dimensions = ((Length() ** 2) * Mass()) / ((Time() ** 2) * Temperature())
        specifier = StringType(parse_expression=(I('Specific') + I('Heat') + I('Capacity')).add_action(join), required=True)
        apparatuslength = ModelType(ApparatusLength, contextual=True)


    class BoilingPoint(TemperatureModel):
        specifier = StringType(parse_expression=(I('Boiling') + I('Point')).add_action(join), required=True)
        compound = ModelType(Compound, contextual=True)
        heat_capacity = ModelType(SpecificHeatCapacity, required=True, contextual=True)


    document = Document(
        Heading('H2O boiling point, measured with a 200cm long apparatus'),
        Paragraph('H2O was found to have a boiling point of 100 °C, with a specific heat capacity of 200 kgm2K-1s-2).'))
    document.models = [BoilingPoint]
    print(document.records.serialize())

The above code will print::

     [{'BoilingPoint':
    {'raw_value': '100',
    'raw_units': '°C',
    'value': [100.0],
    'units': 'Celsius^(1.0)',
    'specifier': 'boiling point',
    'compound': {'Compound': {'names': ['H2O']}},
    'heat_capacity': {'SpecificHeatCapacity':
                     {'raw_value': '200',
                     'raw_units': 'kgm2K-1s-2',
                     'value': [200.0],
                     'units': '(10^3.0) * Gram^(1.0)  Kelvin^(-1.0)  Meter^(2.0)  Second^(-2.0)',
                     'specifier': 'specific heat capacity',
                     'apparatuslength': {'ApparatusLength':
                                        {'raw_value': '200',
                                        'raw_units': 'cm',
                                        'value': [200.0],
                                        'units': '(10^-2.0) * Meter^(1.0)',
                                        'specifier': 'measured with'}}}}}}]

While this is obviously a toy example, we believe this is a powerful paradigm that represents the long-term future of ChemDataExtractor. It's still a preview as some parts of ChemDataExtractor may not work on it yet, but as shown above, it's already quite advanced in what it can do.




