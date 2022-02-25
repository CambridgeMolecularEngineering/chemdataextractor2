==========================
Finding new Properties
==========================

While ChemDataExtractor provides functionality for finding a number of properties out of the box, you will almost definitely need to write some of your own code to extend ChemDataExtractor. This document will walk you through the steps to do this. For more information, you should also look at the :ref:`examples <examples>`.

Creating a New Property Parser
------------------------------------

Depending on your specific use case, you will almost definitely need to add new property parsers to ChemDataExtractor in order to retrieve new properties from scientific text/tables.
Here we take you through a simple example of how to create a new parser.

First, we need all the relevant imports::

    from chemdataextractor import Document
    from chemdataextractor.model import BaseModel, Compound, StringType, ModelType
    from chemdataextractor.model.units import TemperatureModel, LengthModel
    from chemdataextractor.parse import I, join
    from chemdataextractor.doc import Paragraph, Heading


Let's create a simple example document with a single heading followed by a single paragraph that contains a boiling point::

    d = Document(
        Heading(u'Synthesis of 2,4,6-trinitrotoluene (3a)'),
        Paragraph(u'The procedure was followed to yield a pale yellow solid (boiling point 240 °C)')
    )

By default, ChemDataExtractor won't extract any boiling points. This can be shown by examining the output records by calling the :meth:`~chemdataextractor.doc.document.Document.records` method.

To extract this information, we want to create a *boiling_point* property parser.

.. rubric:: Step 1: Defining a new property model

In ``chemdataextractor.model.py`` you will see all the current property models defined in ChemDataExtractor.
Each property inherits from ``BaseModel`` and can contain fields that can have different types
(``StringType``: a string, ``ModelType``: Another property model, ``ListType``: A list of another type e.g. ``ListType(StringType())`` is a list of strings).

So in ``model.py`` we need to create a ``BoilingPoint`` class and give it some useful fields.
As a boiling point is a temperature, we can subclass the ``TemperatureModel`` class which automatically
gives value and unit fields. Now all we need to add is a compound. ::

    class BoilingPoint(TemperatureModel):
        """ A boiling point property"""
        compound = ModelType(Compound)

Such models automatically have :class:`~chemdataextractor.parse.template.QuantityModelTemplateParser`, :class:`~chemdataextractor.parse.template.MultiQuantityModelTemplateParser` set as the sentence parsers and :class:`~chemdataextractor.parse.auto.AutoTableParser` as the table parser. These
parsers use the provided information to extract the model defined by the user. In the above case, the user hasn't yet provided any indication
of what the property is called, so this will pick up all mentions of temperatures found in the document will be extracted. To make sure that we only
find boiling points, we can alter the model as follows::

    class BoilingPoint(TemperatureModel):
        """ A boiling point property"""
        specifier = StringType(parse_expression=(I('Boiling') + I('Point')).add_action(join), required=True)
        compound = ModelType(Compound)

We now have a specifier, which specifies a phrase that must be found in a sentence for the model to be extracted.
The parse expression for the specifier is written in the ``parse_expression`` field, in this case showing that
we need to find the word boiling followed by the word point, and the case does not matter. More detail on these
parse elements is provided :ref:`below <parserwriting>`.

.. note::

    If the parse expression is more than one word long, please add the action :func:`~chemdataextractor.parse.actions.join`
    to the parse expression so that the whole specifier is picked up by the automatically generated parsers correctly.

Also note the ``required`` parameter being set to be ``True``. The required parameter defines whether a field is required
for a model instance to be valid. For example, in the above case, any records without a specifier will be discarded
by CDE.

Another parameter which one could set is the ``contextual``, which is ``False`` by default. This parameter defines whether
information from other elements of the document will be merged into this field. For example, if we wanted to capture the
altitude at which the melting point was captured, we could set up the following::

    class Altitude(LengthModel):
        specifier = StringType(parse_expression=I('Altitude'), required=True)

    class BoilingPoint(TemperatureModel):
        """ A boiling point property"""
        specifier = StringType(parse_expression=(I('Boiling') + I('Point')).add_action(join), required=True)
        compound = ModelType(Compound)
        altitude = ModelType(Altitude, contextual=True)

By doing this, the altitude, which may be found in a different sentence or even a different paragraph, can be added
a boiling point record automatically using CDE's interdependency resolution facilities.

If the nested property (e.g. the altitude the above example) is associated with a compound as well, it may be worth
adding an associated compound to altitude and making the compound field a binding one::

    class Altitude(LengthModel):
        specifier = StringType(parse_expression=I('Altitude'), required=True)
        compound = ModelType(Compound)

    class BoilingPoint(TemperatureModel):
        """ A boiling point property"""
        specifier = StringType(parse_expression=(I('Boiling') + I('Point')).add_action(join), required=True)
        compound = ModelType(Compound, binding=True)
        altitude = ModelType(Altitude, contextual=True)

The ``binding`` parameter is set to ``False`` by default, but by setting it to ``True``, we can make sure that any fields
with the same name in nested fields are consistent. For example, in the above case, it would ensure that the altitude
is associated with the same compound as the boiling point.

These three properties, ``contextual``, ``required``, and ``binding``, ensure that CDE's interdependency resolution facilities
work as well as possible and are especially important with more complicated models such as those shown above.

Once you have these options set, you can try out ChemDataExtractor's automatically generated Sentence Parsers (:class:`~chemdataextractor.parse.auto.AutoSentenceParser`, :class:`~chemdataextractor.parse.template.QuantityModelTemplateParser`) by setting ``BoilingPoint`` as the model you're looking for and calling ``doc.records``, as below::

    doc = Document('The boiling point of MgO was 900 K as measured at an altitude of 100 m.')
    doc.models = [BoilingPoint]
    print(doc.records.serialize())

which should give you the following output::

    [{'BoilingPoint': {'altitude': {'Altitude': {'compound': {'Compound': {'names': ['MgO']}},
                                             'raw_units': 'm',
                                             'raw_value': '100',
                                             'specifier': 'altitude',
                                             'units': 'Meter^(1.0)',
                                             'value': [100.0]}},
                   'compound': {'Compound': {'names': ['MgO']}},
                   'raw_units': 'K',
                   'raw_value': '900',
                   'specifier': 'boiling point',
                   'units': 'Kelvin^(1.0)',
                   'value': [900.0]}}]

.. note::

    Note how we didn't have to set ``Altitude`` as one of the models that ChemDataExtractor should look for in the example above. This is because if your models have some nested structure, ChemDataExtractor automatically looks through the model structure to find all the parsers it needs to call for each element.

.. _parserwriting:
.. rubric:: Step 2: Writing a Parser

Whilst ChemDataExtractor provides automatically generated parsers for properties
(for more information on these automatically generated parsers, see :ref:`examples`) as shown above, if they are not adequate for your use case, you
can also write your own parser for higher precision.

Now we need to create the logic that actually extracts boiling points from the text.
ChemDataExtractor uses nested rules (*grammars*) to extract chemical properties.
These parsers are defined in the ``chemdataextractor.parse`` package.
For example, have a look at the melting point parser in ``chemdataextractor.parse.mp_new.py``.
This contains a number of statements that are used to define the melting point relationship.

It seems very complicated at first, but let's break the first statement down into its constituent parts::

    prefix = Optional(I('a')).hide() + (Optional(lbrct) + W('Tm') + Optional(rbrct)| R('^m\.?pt?\.?$', re.I) | I('melting') + Optional((I('point') | I('temperature')| I('range'))) | R('^m\.?$', re.I) + R('^pt?\.?$', re.I)).hide() + Optional(lbrct + W('Tm') + rbrct) + Optional(W('=') | I('of') | I('was') | I('is') | I('at')).hide() + Optional(I('in') + I('the') + I('range') + Optional(I('of')) | I('about')).hide()

Here, we have created a variable prefix, that contains the logic for identifying the melting point relationship specifier
(e.g. the text that makes it clear we are talking about a melting point in the text, such "a melting temperature, Tm, ").
The grammar contains several elements, with nested logic. Each token must be assigned an element type, these can be:

    * ``I``: A case insensitive word
    * ``W``: A case sensitive word
    * ``R``: A regular expression rule
    * ``T``: A Part-of-Speech tag

Tokens can be joined using the + symbol, and or logic can be formed using the | symbol.

There are also a number of ``ParseElementEnhance`` classes that can be used, found in the ``chemdataextractor.parse.elements.py`` file:

    * ``Optional``: Matches the contained tokens if they appear, but are not required to form a match
    * ``ZeroOrMore``: Matches any number of the contained tokens
    * ``Any``: Matches any token e.g. ``ZeroOrMore(Any())`` will match the whole of the text
    * ``OneOrMore``: Similar to zero or more, but at least one token is required.
    * ``Not``: Looks ahead to disallow a match

Finally, we note that we can hide elements by adding the ``.hide()`` method.
This means that when the parser creates the relationship tree, the hidden tokens are not used.

Continuing to look at the melting point parser, we see the following line::

    units = (W('°') + Optional(R('^[CFK]\.?$')) | W('K\.?'))('units').add_action(merge)

This will clearly match any temperature unit, and as such we tag the rule as 'units'.
On top of the tags, we can do some post-processing actions to clean up the output.
Here, we add the action ``merge``, which joins all tokens without whitespace (° C becomes °C).
Other actions include:

    * ``join``: Join tokens into a single string with spaces between.
    * ``flatten``: Replace all child results with their text contents.

So now we are able to create our own property parsing rules.
Create a file ``bp.py`` in the parse package.
Some very simple logic for extracting boiling points might be::

    from chemdataextractor.parse import R, I, W, Optional, merge
    from chemdataextractor.parse.base import BaseParser
    from chemdataextractor.utils import first


    prefix = (R(u'^b\.?p\.?$', re.I) | I(u'boiling') + I(u'point')).hide()
    units = (W(u'°') + Optional(R(u'^[CFK]\.?$')))(u'raw_units').add_action(merge)
    value = R(u'^\d+(\.\d+)?$')(u'raw_value')
    bp = (prefix + value + units)(u'bp')


The most important thing to note is that the final phrase (called ``bp``) is now a nested tree, with tags labelling the elements.
If we were to reproduce the XML it would look like:

.. code-block:: html

    <bp>
        <value>R(u'^\d+(\.\d+)?$')</value>
        <units>W(u'°') + Optional(R(u'^[CFK]\.?$'))</units>
    </bp>

Now we have to create the logic for parsing this structure.
In the same file, we create the parser class, that inherits from ``BaseParser``::

    class BpParser(BaseSentenceParser):
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

All parser classes must define:

    * A root variable: i.e. the phrase that forms the head of the tree
    * An *interpret* function: That defines the parsing logic

The *interpret* function then creates a new compound (with the model we defined in ``model.py``) and adds a boiling point property.
Here, the result parameter is the result of the parsing process. If a tree with root bp is found, we access the value and unit elements
using `XPath expressions <https://www.w3schools.com/xml/xpath_syntax.asp>`_.

.. note::

    CDE also provides an automatic interpret function if you subclass from :class:`~chemdataextractor.parse.auto.BaseAutoParser`.
    This interpret function relies upon all the names of the tags in the parse expressions being the same as the names of
    the fields in the model.

Finally, we need to tell ChemDataExtractor to parse the ``BoilingPoint`` model with the newly written parser.
This can be done by setting the parsers associated with the ``BoilingPoint`` model::

    BoilingPoint.parsers = [BpParser()]

alternatively, we could have this parser in addition to the default parsers::

    BoilingPoint.parsers.append(BpParser())

.. rubric:: Step 3: Testing the Parser

Now we can simply re-run the document through ChemDataExtractor::

    >>> d = Document(
    >>>     Heading(u'Synthesis of 2,4,6-trinitrotoluene (3a)'),
    >>>     Paragraph(u'The procedure was followed to yield a pale yellow solid (boiling point 240 °C)')
    >>>     )

    >>> d.records.serialize()
    [{'BoilingPoint': {'raw_value': '240',
                       'raw_units': '°C',
                        'compound': {'Compound': {'names': ['2,4,6-trinitrotoluene'], 'labels': ['3a'], 'roles': ['product']}}}}]

Of course, real world examples are much more complex than this, and a large amount of trial and error is needed to create good parsers.
It should also be noted that in this example, the chemical label ('3a') is found using interdependency resolution between the heading and associated paragraph.
In some cases you will need to put the chemical labels and names directly into the parser.
Rules for chemical entity recognition can be found in ``chemdataextractor.parse.cem.py``.


.. rubric:: Table Parsers

ChemDataExtractor parses tables in a similar way. In ``chemdataextractor.parse.table.py`` you will find the logic for finding chemical relationships from tables.
These parsers can be written very similarly to a sentence parser, but require the parser to be subclassed from :class:`~chemdataextractor.parse.base.BaseTableParser`
instead of :class:`~chemdataextractor.parse.base.BaseSentenceParser`.

However, due to the relatively uniform nature of tables and TableDataExtractor's powerful table normalisation facilities,
the automatically generated parser for tables tend to perform very well, with precisions of over 90% for tables often being achievable
by choosing the right parse expressions and setting the ``required``, ``contextual`` and ``binding`` properties appropriately.

Regular Expressions
---------------------------

Regular expressions are an important tool in the Natural Language Processing toolbox.
They are special strings that can be used to match sub-strings for the purpose of searching, splitting or grouping text.
Regular expressions appear frequently in ChemDataExtractor, most commonly in the chemical property parsers that will be outlined in the next section.
Below, we provide a number of useful links for information on Regular Expressions.

If you are unfamiliar with Regular Expressions, I recommend going through the `TutorialsPoint Python Regular Expressions tutorial <https://www.tutorialspoint.com/python/python_reg_expressions.htm>`_.

Python contains a useful regular expressions library ``re`` that also contains extensive documentation (https://docs.python.org/3/library/re.html).

Formatting Regular Expressions can be problematic, especially for highly nested groups.
Perhaps the most useful tool for dealing with Regular Expressions is `Debuggex <https://www.debuggex.com>`_ which provides a beautiful graphical interface for debugging regular expressions.
