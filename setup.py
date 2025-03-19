#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


if os.path.exists("README.md"):
    long_description = open("README.md").read()
else:
    long_description = """A toolkit for extracting chemical information from the scientific literature."""

setup(
    name="chemdataextractor2",
    version="2.4.0",
    author="Matt Swain, Callum Court, Juraj Mavracic, Taketomo Isazawa, and contributors",
    author_email="m.swain@me.com, cc889@cam.ac.uk, jm2111@cam.ac.uk, ti250@cam.ac.uk",
    license="MIT",
    url="https://github.com/CambridgeMolecularEngineering/ChemDataExtractor2",
    packages=find_packages(),
    description="A toolkit for extracting chemical information from the scientific literature.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="text-mining mining chemistry cheminformatics nlp html xml science scientific",
    zip_safe=False,
    entry_points={"console_scripts": ["cde = chemdataextractor.cli:cli"]},
    tests_require=["pytest"],
    install_requires=[
        "appdirs>=1.4.3",
        "beautifulsoup4>=4.12.0",
        "boto3>=1.15.18",
        "botocore>=1.18.18",
        "click>=6.7",
        "cssselect>=1.0.1",
        "DAWG2",
        "tabledataextractor",
        "lxml>=3.7.2",
        "nltk>=3.2.2",
        'pdfminer.six ; python_version >= "3.8"',
        'pdfminer.six >=20160614, <=20220524 ; python_version < "3.8"',
        "python-crfsuite>=0.9.1",
        "python-dateutil>=2.6.0",
        "PyYAML>=3.12",
        "requests>=2.12.5",
        "selenium>=3.14.1",
        "protobuf>=3.0.0",
        "scipy<1.13.0",
        "numpy>=1.17,<2.0.0",
        "deprecation",
        "yaspin",
        "tokenizers>=0.12.1",
        "scikit-learn>=0.22.1",
        "stanza>=1.6.1",
        "overrides>=3.1.0",
        "transformers>=4.30.1",
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Text Processing",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
)
