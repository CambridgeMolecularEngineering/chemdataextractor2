================================
Finding Chemical Records
================================

ChemDataExtractor processes each document element separately to extract the chemical information,
and then merges data together from every element in the document to produce a single record for each unique chemical entity.

Consider this simple document as an example::

    >>> from chemdataextractor.doc import Document, Heading, Paragraph
    >>> doc = Document(
        Heading('5,10,15,20-Tetra(4-carboxyphenyl)porphyrin (3).'),
        Paragraph('m.p. 90°C.'),
        Paragraph('Melting points were measured in Tetrahydrofuran (THF).'),
        models=[Compound, MeltingPoint]
        )

Get the records for each element using the records property::

    >>> doc[0].records.serialize()
    [{'Compound': {'names': ['5,10,15,20-Tetra(4-carboxyphenyl)porphyrin'], 'labels': ['3']}}]
    >>> doc[1].records.serialize()
    [{'MeltingPoint': {'raw_value': '90', 'raw_units': '°C', 'value': [90.0], 'units': 'Celsius^(1.0)'}}]
    >>> doc[2].records.serialize()
    [{'Compound': {'names': ['THF', 'Tetrahydrofuran']}}, {'Compound': {'names': ['THF', 'Tetrahydrofuran']}}]

Due to the data interdependencies between the different document elements,
the records from each element aren't so useful individually. Instead, it's normally much more useful to get the combined records for the entire document::

    >>> doc.records.serialize()
    [{'Compound': {'names': ['5,10,15,20-Tetra(4-carboxyphenyl)porphyrin'], 'labels': ['3']}},
     {'Compound': {'names': ['THF', 'Tetrahydrofuran']}},
     {'MeltingPoint': {'raw_value': '90',
                       'raw_units': '°C',
                       'value': [90.0],
                       'units': 'Celsius^(1.0)',
                       'compound': {'Compound': {'names': ['5,10,15,20-Tetra(4-carboxyphenyl)porphyrin'],
                                                 'labels': ['3']}}}}]

ChemDataExtractor has merged the information from all the elements into two unique chemical records.
