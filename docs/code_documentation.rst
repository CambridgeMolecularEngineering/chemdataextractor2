.. _source_code_docs:

=====================
API Documentation
=====================

.. note:: Private methods are not included in the documentation!


.. toctree::
   :maxdepth: 5
   :caption: Contents
   :hidden:

   source_code_docs/chemdataextractor
   source_code_docs/biblio
   source_code_docs/cli
   source_code_docs/doc
   source_code_docs/model
   source_code_docs/nlp
   source_code_docs/parse
   source_code_docs/reader
   source_code_docs/relex
   source_code_docs/scrape
   source_code_docs/text


.. currentmodule:: chemdataextractor

.. autosummary::

   config
   data
   errors
   utils

---------------------------------------------------------

.. autosummary::

   biblio
   biblio.bibtex
   biblio.person
   biblio.xmp

---------------------------------------------------------

.. autosummary::

   cli
   cli.cem
   cli.chemdner
   cli.cluster
   cli.config
   cli.data
   cli.dict
   cli.evaluate
   cli.pos
   cli.tokenize

---------------------------------------------------------

.. autosummary::

   doc
   doc.document
   doc.element
   doc.figure
   doc.table
   doc.table_new
   doc.text

---------------------------------------------------------

.. autosummary::

   model
   model.base
   model.model
   model.units
   model.units.unit
   model.units.dimension
   model.units.quantity_model
   model.units.length
   model.units.mass
   model.units.time
   model.units.temperature

---------------------------------------------------------

.. autosummary::

   nlp
   nlp.abbrev
   nlp.cem
   nlp.corpus
   nlp.lexicon
   nlp.pos
   nlp.tag
   nlp.tokenize

---------------------------------------------------------

.. autosummary::

   parse
   parse.actions
   parse.auto
   parse.base
   parse.cem
   parse.common
   parse.context
   parse.elements
   parse.ir
   parse.mp
   parse.nmr
   parse.tg
   parse.uvvis

---------------------------------------------------------

.. autosummary::

   reader
   reader.acs
   reader.base
   reader.cssp
   reader.markup
   reader.nlm
   reader.pdf
   reader.plaintext
   reader.rsc
   reader.uspto
   reader.elsevier
   reader.springer

---------------------------------------------------------

.. autosummary::

   scrape
   scrape.base
   scrape.clean
   scrape.csstranslator
   scrape.entity
   scrape.fields
   scrape.scraper
   scrape.selector
   scrape.pub
   scrape.pub.nlm
   scrape.pub.rsc
   scrape.pub.springer
   scrape.pub.elsevier

---------------------------------------------------------

.. autosummary::

   text
   text.chem
   text.latex
   text.normalize
   text.processors
   text.unwrap

---------------------------------------------------------

.. autosummary::

   relex
   relex.cluster
   relex.entity
   relex.pattern
   relex.phrase
   relex.relationship
   relex.snowball
   relex.utils










