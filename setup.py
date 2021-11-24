#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


if os.path.exists('README.rst'):
    long_description = open('README.rst').read()
else:
    long_description = '''A toolkit for extracting chemical information from the scientific literature.'''

setup(
    name='ChemDataExtractor',
    version='2.01',
    author='Matt Swain, Callum Court, Juraj Mavracic, Taketomo Isazawa, and contributors',
    author_email='m.swain@me.com, cc889@cam.ac.uk, jm2111@cam.ac.uk, ti250@cam.ac.uk',
    license='MIT',
    url='https://github.com/CambridgeMolecularEngineering/ChemDataExtractor',
    packages=find_packages(),
    description='A toolkit for extracting chemical information from the scientific literature.',
    long_description=long_description,
    keywords='text-mining mining chemistry cheminformatics nlp html xml science scientific',
    zip_safe=False,
    entry_points={'console_scripts': ['cde = chemdataextractor.cli:cli']},
    tests_require=['pytest'],
    install_requires=[
        'appdirs',
        'beautifulsoup4',
        'click==6.7',
        'cssselect',
        'lxml',
        'nltk',
        'pdfminer.six',
        'python-dateutil',
        'requests==2.21.0',
        'six',
        'python-crfsuite',
        'TableDataExtractor @ git+https://github.com/CambridgeMolecularEngineering/tabledataextractor',
        'DAWG @ git+https://github.com/ti250/DAWG-patched',
        'PyYAML',
        'selenium',
        'numpy',
        'scipy'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
)
