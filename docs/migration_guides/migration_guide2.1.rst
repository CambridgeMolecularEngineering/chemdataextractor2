.. _migration_guide_2_1:

.. role:: python(code)
   :language: python

******************************************
Migrating to v2.1
******************************************

.. note::

    If you're migrating to ChemDataExtractor 2.1 from ChemDataExtractor 1.x, please consult the :ref:`migration guide to 2.0<migration_guide>` before coming back here.

Overview
=================================

ChemDataExtractor 2.1 includes a powerful new Named Entity Recognition (NER) system that performs competitively with the state of the art for both organic and inorganic chemical entities, as well as a brand new tokenizer that is designed to work in conjunction with it. To support these capabilities and any future additions, the way token tags are stored have been greatly enhanced, while maintaining backwards compatibility for almost all usecases. Unlike with the v2.0 release, any code not pertaining to NER and PoS taggers or configuring them should run as-is, but they may have diminished performance due to the new tokenization choices. While you can continue using the previous functionality as detailed in the section on `Maintaining Backwards Compatibility for Parsers`_, we recommend that parsers be moved to the newer systems as described in the `Migrating Parsers`_ section. Any changes pertaining to NER or PoS taggers are detailed in the section on `Migrating and Upgrading Taggers`_.

In addition to these changes, there are some more optional enhancements that can be adopted in the ways that values and units are extracted through the addition of :class:`~chemdataextractor.model.base.InferredProperty`, as well as a new parse expression, :class:`~chemdataextractor.parse.elements.Every`, examples of which can be seen under the `Upgrading Parsers`_ section.

A minor difference to keep in mind when setting up ChemDataExtractor 2.1 on a new machine is that the ``cde data download`` command no longer needs to be run, nor is it recommended. This is because any necessary files are downloaded automatically when required, and there are some packages that may not be used depending on your configuration. However, if you wish to turn this behavior off and revert to previous behavior of downloading all the packages with a command, please set :const:`chemdataextractor.data.AUTO_DOWNLOAD` to ``False`` and run the ``cde data download`` command as before.

Migrating Parsers
====================

By default, ChemDataExtractor 2.1 moves to a new Named Entity Recognition (NER) system that works in conjunction with a new tokenizer. Compared to the previous system, this system performs much better on a wide range of chemical entities, as shown below.

.. csv-table::
    :header: "", "Organic Materials/F1 Score", "Inorganic Materials/F1 Score"
    :delim: ;
    :widths: auto
    :align: center

    New NER + Tokenizer; 89.7; 88.0
    Old NER + Tokenizer; 89.1 ; 60.7

Where we measured took the performance on the CHEMDNER dataset to be representative of the performance on organic materials, and the score on the Matscholar dataset to be representative of the performance on inorganic materials.

However, if you've written any parse rules, this new tokenization will require some changes to your parser. These will mostly come in very predictable ways that we detail below, as we found when porting over our own code. In fact, even for all of the built-in parsers included in ChemDataExtractor, it only took a few days of work by one person to make these parsers pass all of the extensive tests included in ChemDataExtractor. We've included some tips for how to adjust your parse rules to take advantage of the new NER and tokenization rules, but if you're not ready to spend the time doing that yet, you can revert to the previous NER and tokenization behavior as shown in the `Maintaining Backwards Compatibility for Parsers`_ section.

If you have overridden the `parse_sentence` method, you will want to adjust it to take as its input a `Sentence` object instead of a list of tokens. To preserve previous behaviour, the quickest thing to do would be to just take the sentence's tokens with something along the lines of `tokens = sentence.tokens`.

Migrating Parse Rules
---------------------

Whether you took advantage of the new automatically generated parsers from CDE 2.0 or you manually wrote your own parse rules, you will have written a few parse rules that may have been affected by the changes in the tokenization. The general theme is that the new parser is much less 'clever' than the old one, with predictable rules.

This new tokenization was chosen for better NER performance, as detailed in the paper (LINK TO BE ADDED), but these should also be helpful in writing parse rules once you get used to them, as the rules behind tokenization are significantly less complex.

The one major change that is most likely to affect you is that the tokenizer included in previous versions of ChemDataExtractor had a number of rules to try to keep punctuation such as dashes, periods, brackets, and commas together with other tokens provided they seemed to be part of a chemical entity. The new tokenizer no longer does this unless these symbols are surrounded by numbers, so your parse rules will need to be adjusted accordingly. Below are some examples of cases where we had to change the parse rules to work with the new tokenizer:

.. csv-table::
    :header: "Old Parse Rule", "New Parse Rule"
    :delim: ;
    :widths: auto
    :align: center

    :python:`R('^\[?cm[-–−‒]?1\]?$')`; :python:`(Optional(W('[')) + R('^\[?cm[-–−‒]?1\]?$') + Optional(W(']')))`
    :python:`R('^m\.?$', re.I) + R('^pt?\.?$', re.I)`; :python:`R('^m\.?$', re.I) + Optional(I('.')) + R('^pt?\.?$', re.I) + Optional(I('.'))`
    :python:`W('13C{1H}') | W('13C{1H') + W('}')`; :python:`(W('13C') + W('{') + W('1H') + W('}'))`

While there may be other edge cases due to the new NER system, this was the main difference we found when migrating our code and keeping this in mind should get you most of the way in terms of updating your parsers.

Maintaining Backwards Compatibility for Parsers
---------------------------------------------------

To minimize disruptions from moving to ChemDataExtractor 2.1, we have included functionality to revert to the previous NER and tokenization behavior. This previous behavior also has the advantage of being faster, especially on systems where ChemDataExtractor will be running without access to a GPU. The below table is a good example of their speeds:

.. csv-table::
    :header: "", "CPU", "GPU"
    :delim: ;
    :widths: auto
    :align: center

    New NER + Tokenizer; 54.32s ; 10.83s
    Old NER + Tokenizer; 6.55s ; 6.55s

The figures were obtained by reading in an HTML document and running NER and tokenization on it. This test was repeated ten times and the average result is shown above. The GPU used was an Nvidia Tesla K80 and ChemDataExtractor was run with the default settings. While your mileage may vary depending on your GPU and the length of the document, we believe that this is a relatively good indication of the performance of ChemDataExtractor.

.. note::

    If you encounter out of memory issues with your GPU, try changing the parameters in the CEM tagger to have a smaller batch size. This can be done fastest by creating a new NER tagger and patching ChemDataExtractor's CemTagger to use this, as shown below::

        from chemdataextractor.nlp.new_cem import BertFinetunedCRFCemTagger, CemTagger

        ner_tagger = BertFinetunedCRFCemTagger(max_batch_size=100)
        CemTagger.taggers[2] = ner_tagger

    The order of taggers in ``CemTagger`` may change making this unstable in future versions.


As can be seen in the table, ChemDataExtractor is still faster when using the previous tokenizer and NER, but also performs worse in general, especially on inorganic compounds, as shown earlier. For this reason, we recommend that if you can, you use the new NER. However, if you don't want to rewrite your parsers or have performance constraints, the previous NER and tokenization system is a great fallback, and can be activated easily by adding the following code to the start of your code. ::

    from chemdataextractor import fastner

This will set the correct NER and tokenization for all the document elements automatically for you.

Upgrading Parsers
====================

ChemDataExtractor 2.1 comes with a number of enhancements for creating parsers, whether you're manually defining rules or using other types of parsers such as :class:`~chemdataextractor.relex.snowball.Snowball` or :class:`~chemdataextractor.parse.auto.AutoSentenceParser`.

Inferred Properties
-------------------------

If you adopted :class:`~chemdataextractor.model.units.quantity_model.QuantityModel` in ChemDataExtractor 2.0, you no longer have to include custom interpretation code in your parsers to create values and units. Instead, :class:`~chemdataextractor.model.units.quantity_model.QuantityModel` now takes advantage of :class:`~chemdataextractor.model.base.InferredProperty` to ensure that you don't have to write any interpretation code yourself. See the definition of the updated :class:`~chemdataextractor.model.units.quantity_model.QuantityModel` ::

    class QuantityModel(BaseModel, metaclass=_QuantityModelMeta):
        raw_value = StringType(required=True, contextual=True)
        raw_units = StringType(required=True, contextual=True)
        value = InferredProperty(ListType(FloatType(), sorted_=True),
                                 origin_field='raw_value', inferrer=infer_value, contextual=True)
        units = InferredProperty(UnitType(),
                                 origin_field='raw_units', inferrer=infer_unit, contextual=True)
        error = InferredProperty(FloatType(),
                                 origin_field='raw_value', inferrer=infer_error, contextual=True)

Take a look at the value property. Because ``value`` is always linked to the ``raw_value``, we can express that ``value`` is inferred from ``raw_value`` using the syntax shown above. We can then pass in an inferrer function, which is used to the ``value`` from the ``raw_value``. By specifying these links in the model, we save ourselves from having to write a lot of boilerplate code in our parsers to extract properties, and these inferred properties are then calculated when appropriate.

These inferred properties can also be used with keypaths for the origin field, so you can even access properties from nested models to create inferred properties in the parent model. To learn more about how to use inferred properties, check out the documentation at :class:`~chemdataextractor.model.base.InferredProperty` and the :ref:`tutorial<inferred_properties_guide>`.

Tag
-----

The :class:`~chemdataextractor.parse.element.Tag` element has been made more powerful in that you can now choose what tag type it refers to. While before, you were given the combined tag as the element at index 1 of the tagged tokens and that was all you could access, you can now access whatever type of tag you want. By default, the element will keep referring to this combined tag, but you can also refer to any tag that you're interested in. By default, ChemDataExtractor comes with both NER and PoS tagging, so you can do something like this::

    pos_element = T('NN', tag_type='ner_tag')

This ensures that even if the element also happens to be a chemical named entity, your element will pick it up correctly, which was impossible to do in previous versions of ChemDataExtractor.

Every
----------

The :class:`~chemdataextractor.parse.element.Every` element is a useful tool if a single match has to satisfy multiple constraints. For example, if you have created a new tagger, but want to make sure that the tagger doesn't match things that you know that it gets confused by common mistakes, you can use the :class:`~chemdataextractor.parse.element.Every` element with a number of :class:`~chemdataextractor.parse.element.BaseParserElement` subclasses that it has to match.  where we want to find all the named entities in a document about NMR, but don't want any elements like 1H, that are actually labels for NMR spectra types::

    every_element = Every([T('B-CM'), Not(W('1H'))])

Of course, in reality, you wouldn't have to configure your own element to find named entities, as ChemDataExtractor will generally do that for you, but this shows a good example of a situation where the :class:`~chemdataextractor.parse.element.Every` element can be of use.

.. note::

    Should it match all the elements passed in, the :class:`~chemdataextractor.parse.element.Every` element will return the longest one.

Migrating and Upgrading Taggers
================================

Previous versions of ChemDataExtractor had two types of taggers: Part of Speech Taggers and Named Entity Taggers. ChemDataExtractor 2.1 only comes with those two types of taggers as well, but now includes the possibility for many more types of taggers. This functionality comes hand in hand with the new :class:`~chemdataextractor.doc.text.RichToken` class, which allows for dynamic tagging of tokens when the tags are needed. When the user accesses these tags either via ``token["tag_name"]`` or ``token.tag_name``, ChemDataExtractor will automatically call the appropriate tagger to tag the sentence that the token is included in.

Therefore, to support this type of tagging, you will need to make a few changes to your tagger, with the changes required depending on the type of tagger you had before.

Migrating a Part of Speech Tagger
----------------------------------

Migrating a Part of Speech Tagger is easy. Just add the ``tag_type`` property to your class and rename the ``tag`` method to ``legacy_tag``. For a toy example, see the Part of Speech Tagger below ::

    class ToyPOSTagger(BaseTagger):

        def tag(self, tokens):
            return list(zip(tokens, 'NN' for _ in tokens))

This is a pretty bad PoS tagger that just tags every word as a noun to be a chemical entity, but let's imagine that we wanted to port this tagger to ChemDataExtractor 2.1. Doing this is easy, as all you have to do is::

    class ToyPOSTagger(BaseTagger):
        tag_type = 'pos_tag'

        def legacy_tag(self, tokens):
            return list(zip(tokens, 'NN' for _ in tokens))

While you can still set the :attr:`~chemdataextractor.doc.text.BaseText.pos_tagger` property, this has been deprecated, and you should modify the :attr:`~chemdataextractor.doc.text.BaseText.taggers` property instead. This is a list of all the taggers included in the element, from which ChemDataExtractor will automatically choose the one required. You can either modify the list and remove the default PoS tagger and add your own, or you can just append to the end of this list; ChemDataExtractor will automatically prioritize taggers that are included at the end of the list of :attr:`~chemdataextractor.doc.text.BaseText.taggers`.

Migrating a Named Entity Recognition Tagger
--------------------------------------------

Migrating a Named Entity Recognition tagger may be harder, as different taggers may expect different inputs into the ``tag`` function. Some of them expect an input of a list of strings representing the tokens, as with PoS taggers, or some may expect a list of tuples representing the token string and the part of speech tag.

If your NER tagger was designed with the former input in mind, then you should follow the instructions for migrating a PoS tagger, although you should change the ``tag_type`` to ``ner_tag``.

The process is slightly more involved in the case that you want to migrate a tagger that expects these tuples. The ``tag`` method now takes as input a list of :class:`~chemdataextractor.doc.text.RichToken`, and the default way to pass tags between taggers now is to just access that attribute within the :class:`~chemdataextractor.doc.text.RichToken`, with the tag being calculated as required.

Therefore, any previous calls in your ``tag`` method to the element at index 1 of a token should instead be changed to a request for the PoS tag. Here's a toy example; imagine that we had a tagger that would call every noun a chemical named entity. ::

    class ToyNERTagger(BaseTagger):

        def tag(self, tokens):
            tags = []
            for token in tokens:
                if token[1] == 'NN':
                    tags.append((token[0], 'B-CM'))
                else:
                    tags.append((token[0], None))
            return tags

To migrate this parser to ChemDataExtractor 2.1, you just need to change it as follows::

    class ToyNERTagger(BaseTagger):
        tag_type = 'ner_tag'

        def tag(self, tokens):
            tags = []
            for token in tokens:
                if token['pos_tag'] == 'NN':
                    tags.append((token, 'B-CM'))
                else:
                    tags.append((token, None))
            return tags

As with the :attr:`~chemdataextractor.doc.text.BaseText.pos_tagger` property, the :attr:`~chemdataextractor.doc.text.BaseText.ner_tagger` is deprecated, although it can still be used. Instead, you should modify the :attr:`~chemdataextractor.doc.text.BaseText.taggers` property. This is a list of all the taggers included in the element, from which ChemDataExtractor will automatically choose the one required. You can either modify the list and remove the default NER tagger and add your own, or you can just append to the end of this list; ChemDataExtractor will automatically prioritize taggers that are included at the end of the list of :attr:`~chemdataextractor.doc.text.BaseText.taggers`.

Upgrading your Taggers
------------------------

While you can easily migrate your taggers through the steps shown above, you can also upgrade your parser to take advantage of the new APIs in ChemDataExtractor 2.1. For more detail on how to use these new APIs and the concepts behind them, please consult this :ref:`guide<creating_taggers>`, but what follows is a quick overview of the features that you can now implement with the new APIs.

If your tagger leverages other libraries that are much faster if you pass in multiple sentences at the same time, you can instead implement the ``batch_tag`` method. ChemDataExtractor will then call this method preferentially over the ``tag`` method, handling the collection of all the elements which need to be tagged. This can result in large performance improvements for relatively little new code.

In addition, you can now create custom taggers for custom tag types that leverage other taggers through the flexibility of :class:`~chemdataextractor.doc.text.RichToken`, in the same way that NER taggers can leverage PoS taggers. This is trivial to do by accessing ``token["tag_type"]``. By breaking apart your tagger in this way, you can potentially reuse large amounts of computation between taggers, potentially resulting in a much more efficient tagger.

Finally, you can also easily collate multiple such taggers into one using :class:`~chemdataextractor.nlp.tag.EnsembleTagger`. The new NER tagger, :class:`~chemdataextractor.nlp.new_cem.CemTagger`, is an example of this, being composed of three other taggers.




