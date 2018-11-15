=======================
.cli
=======================

Command line interfact tools

.. automodule:: chemdataextractor.cli
    :members:
    :undoc-members:

    .. autofunction:: cli(ctx, verbose)

    .. autofunction:: extract(ctx, input, output)

    .. autofunction:: read(ctx, input, output)

.cli.cem
------------------------------------------------

.. automodule:: chemdataextractor.cli.cem
    :members:
    :undoc-members:

    .. autofunction:: cem(ctx)

    .. autofunction:: train_crf(ctx, input, output, clusters)

.cli.chemdner
------------------------------------------------

.. automodule:: chemdataextractor.cli.chemdner
    :members:
    :undoc-members:

    .. autofunction:: chemdner_cli(ctx)

    .. autofunction:: prepare_gold(ctx, annotations, gout)

    .. autofunction:: prepare_tokens(ctx, input, annotations, tout, lout)

    .. autofunction:: tag(ctx, corpus, output)

.cli.cluster
------------------------------------------------

.. automodule:: chemdataextractor.cli.cluster
    :members:
    :undoc-members:

    .. autofunction:: cluster_cli(ctx)

    .. autofunction:: load(ctx, input, output)

.cli.config
------------------------------------------------

.. automodule:: chemdataextractor.cli.config
    :members:
    :undoc-members:

    .. autofunction:: config_cli(ctx)

    .. autofunction:: list(ctx)

    .. autofunction:: get(ctx)

    .. autofunction:: set(ctx, key, value)

    .. autofunction:: remove(ctx, key)

    .. autofunction:: clear(ctx)

.cli.data
------------------------------------------------

.. automodule:: chemdataextractor.cli.data
    :members:
    :undoc-members:

    .. autofunction:: data_cli(ctx)

    .. autofunction:: where(ctx)

    .. autofunction:: list(ctx)

    .. autofunction:: download(ctx)

    .. autofunction:: clean(ctx)

.cli.dict
------------------------------------------------

.. automodule:: chemdataextractor.cli.dict
    :members:
    :undoc-members:

    .. autofunction:: dict_cli(ctx)

    .. autofunction:: prepare_jochem(ctx, jochem, output, csoutput)

    .. autofunction:: prepare_include(ctx, include, output)

    .. autofunction:: build(ctx, inputs, output, cs)

    .. autofunction:: tag(ctx, model, cs, corpus, output)

.cli.evaluate
------------------------------------------------

.. automodule:: chemdataextractor.cli.evaluate
    :members:
    :undoc-members:

    .. autofunction:: evaluate(ctx)

    .. autofunction:: run(input)

    .. autofunction:: compare()

.cli.pos
------------------------------------------------

.. automodule:: chemdataextractor.cli.pos
    :members:
    :undoc-members:

    .. autofunction:: pos_cli(ctx)

    .. autofunction:: train_all(ctx, output)

    .. autofunction:: evaluate_all(ctx, model)

    .. autofunction:: train(ctx, output, corpus, clusters)

    .. autofunction:: evaluate(ctx, model, corpus, clusters)

    .. autofunction:: train_perceptron(ctx, output, corpus, clusters)

    .. autofunction:: evaluate_perceptron(ctx, model, corpus)

    .. autofunction:: tag(ctx, input, output)


.cli.tokenize
------------------------------------------------

.. automodule:: chemdataextractor.cli.tokenize
    :members:
    :undoc-members:

    .. autofunction:: tokenize_cli(ctx)

    .. autofunction:: train_punkt(ctx, input, output, abbr, colloc)

    .. autofunction:: sentences(ctx, input, output)

    .. autofunction:: words(ctx, input, output)

