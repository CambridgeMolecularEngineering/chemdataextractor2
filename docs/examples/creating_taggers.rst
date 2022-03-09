.. _creating_taggers:
.. role:: python(code)
   :language: python

******************************************
Creating and Using New Taggers
******************************************

Overview
=================================

ChemDataExtractor includes facilities to easily and flexibly add new taggers to your NLP pipeline. To take advantage of the new tagger APIs, you need to follow the following steps:

- :ref:`Define a new tagger<Defining a New Tagger>`

- :ref:`Add the new tagger to any elements that you want it called for<Adding the New Tagger to Document Elements>`

- :ref:`Use the new tagger when parsing<Using the New Tagger when Parsing>`

As a toy example, we're going to try creating a new tagger, RENTagger, that takes the NER tag of each token and reverses its character order (e.g. "B-CM" goes to "MC-B").

Defining a New Tagger
==========================

To define a new tagger, we can either subclass the :class:`~chemdataextractor.nlp.tag.BaseTagger` class or implement the API ourselves. For this example, we're going to be taking the easier route of subclassing :class:`~chemdataextractor.nlp.tag.BaseTagger`, but the documentation for the class will give you more information about the API.

When we're subclassing :class:`~chemdataextractor.nlp.tag.BaseTagger`, we only need to implement two different things: a ``tag_type`` attribute and a ``tag`` method. Let's see what this looks like::

    class RENTagger(BaseTagger):
        tag_type = "ren_tag"

        def tag(self, tokens):
            return list(zip(tokens, [token["ner_tag"][::-1] for token in tokens]))

By setting the ``tag_type`` attribute, we express intent to the system that this is the tagger that should be called when the user wants to access this tag type for any token from elements for which this tagger is registered.

The tagger also needs to provide a ``tag`` method, which takes as its argument a list of tokens and returns a list of token, tag tuples. In this case, we get the NER tag for each token and reverse it.

Should I be Using :meth:`~chemdataextractor.tag.BaseTagger.batch_tag`?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :meth:`~chemdataextractor.tag.BaseTagger.batch_tag` method allows for faster tagging if your tagger is more efficient when you are tagging multiple instances at once. This isn't the case for the ``RENTagger`` we just created, but if we wanted to, we can add a :meth:`~chemdataextractor.tag.BaseTagger.batch_tag` method easily as follows. ::

    class RENTagger(BaseTagger):
        tag_type = "ren_tag"

        def tag(self, tokens):
            return list(zip(tokens, [token["ner_tag"][::-1] for token in tokens]))

        def batch_tag(self, sents):
            tags = []
            for sent in sents:
                tags.append(list(zip(sent, [token["ner_tag"][::-1] for token in sent])))
            return tags

This method is primarily intended for when your tagger is a wrapper around some external libraries, which often operate much faster if you pass in a large number of elements at once.

Should I be Using an :class:`~chemdataextractor.nlp.tag.EnsembleTagger`?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`~chemdataextractor.nlp.tag.EnsembleTagger` provides a way to collect multiple taggers into one place. This may be useful if you have a tagger that should only be used in conjunction with some others. For example, imagine if you wanted a ``PoSRENTagger`` that would have as a token the reversed NER tag appended to the part of speech tag. ::

    class PoSRENTagger(EnsembleTagger):
        taggers = [RENTagger()]
        tag_type = "pos_ren_tag"

        def tag(self, tokens):
            return list(zip(tokens, [token["pos_tag"] + token["ren_tag"] for token in tokens]))

One thing to note is that even if the :class:`~chemdataextractor.nlp.tag.EnsembleTagger` subclass has not implemented the :meth:`~chemdataextractor.tag.BaseTagger.batch_tag` method itself, if any of the taggers included in it have implemented it, ChemDataExtractor will call the :meth:`~chemdataextractor.tag.BaseTagger.batch_tag` method for those taggers.

We use :class:`~chemdataextractor.nlp.tag.EnsembleTagger` in the ChemDataExtractor library for the NER taggers. The old NER tagger relied on collating the results from multiple methods, while the new NER tagger acts on processed text which has had any numbers converted into a special token. To ensure that neither of these taggers run without the other required taggers, they are implemented as :class:`~chemdataextractor.nlp.tag.EnsembleTagger` subclasses.

Using the New Tagger
====================

To use the new tagger, we need to add the tagger to the list of taggers that an element will call, and then access it either directly as an element of the tokens or through parse rules.

Adding the New Tagger to Document Elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To add your new tagger to any elements, all you have to do is to append it to the ``taggers`` property, as shown here, and then ChemDataExtractor will call it when required to tag the tokens in the sentence. ::

    Sentence.taggers.append(RENTagger())

.. note::

    Any taggers appended are called before the default taggers, so if you want to override system taggers, instead of finding the original tagger and removing it, you can just append to the end of the ``taggers`` list.

You can then verify that this works by checking the tags for a sample sentence::

    sent = Sentence("MgO melts at 100 K.")
    print([token.ren_tag for token in sent.tokens])

This should give you the following result::

    ['MC-B', 'O', 'O', 'O', 'O', 'O']

.. note::

    You can also access any properties on tokens with dictionary style syntax, so the previous bit of code could have also been written as [token["ren_tag"] for token in sent.tokens]

Using the New Tagger when Parsing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using the tags from our tagger when parsing is simple; you can use the class:`~chemdataextractor.parse.elements.Tag` element (or its shorthand, ``T``), while specifying the tag type, like this::

    ren_element = T("MC-B", tag_type="ren_tag")
