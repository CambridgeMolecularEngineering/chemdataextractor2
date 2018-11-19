from chemdataextractor.doc import Document

els = ['Here we define the Curie temperature (TC).',
               'Next we have the uv-vis absorption maximum, λmax',
               'Finally, the melting point, Tm']

d = Document(*els)
for p in d.paragraphs:
    for s in p.sentences:
        print(s.tagged_tokens)

print(d.definitions)