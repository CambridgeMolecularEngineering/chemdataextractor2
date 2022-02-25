# Changelog

##[v2.1.0](https://github.com/CambridgeMolecularEngineering/ChemDataExtractor/releases/tag/v2.1.0) 

**Implemented Enhancements:**
- An improved NER system that allows for much better performance on inorganic materials.
- New tokenization to go with the new NER system.
- The addition of InferredProperty allows for users to define explicit links between different properties included in their data models, reducing a large amount of boilerplate parser code.
- The Every parse element means that users can specify that a certain token satisfy multiple condition.
- A more flexible tagging system that allows for the creation of taggers beyond just part of speech and NER taggers.
- Batch tagging.
- A new, modern theme for the documentation, along with much more detail in the documentation on certain parts of ChemDataExtractor, such as tagging and tokenization.

**Breaking Changes:**
- Any taggers previously written by the user will be broken. Please refer to the migration guide for version 2.1.
- The new tokenization can break some parse rules written by the user. This can either be fixed by adopting a few changes to the parse rules, or by reverting to the previous NER system and tokenizer. Please refer to the migration guide for more details.

## [v2.0](https://github.com/mcs07/ChemDataExtractor/releases/tag/v2.0) (2019-09-xx)
[Full Changelog](https://github.com/mcs07/ChemDataExtractor/compare/...)

**Implemented enhancements:**

 - New model structure changed so that the Compound class is no longer at the root of all properties
 - Hierarchy changed so that documents own models, not parsers, so that the user doesn’t need to remember to pass in all the correct parsers.
 - Quantity based models, allowing for easy detection of units and values. Also allows for better comparisons of models.
 - Completely new table parsing routine with the incorporation of TableDataExtractor. This returns a more structured form for tables without any user input.
 - Automatically generated parsers based on the dimensional information of properties.
 - Forward looking Interdependency Resolution for detecting definitions of specifier terms and chemical names.
 - Improved Interdependency Resolution to account for more complex models.
 - Snowball integration where Snowball parsers can be used seamlessly alongside rule-based parsers.
 - Improved performance, with parsing up to 2x faster in real-world usage.
 - The incorporation of an evaluation package for measuring the performance of CDE.
 - Improved tokenization when using new quantity based models.
 - Improved documentation, including a migration guide for users coming from older versions.

## [v1.3.0](https://github.com/mcs07/ChemDataExtractor/releases/tag/v1.3.0) (2017-02-03)
[Full Changelog](https://github.com/mcs07/ChemDataExtractor/compare/v1.2.3...v1.3.0)

**Implemented enhancements:**

- Add parser for glass transition temperature [\#13](https://github.com/mcs07/ChemDataExtractor/pull/13) ([rtchoua](https://github.com/rtchoua))

## [v1.2.3](https://github.com/mcs07/ChemDataExtractor/releases/tag/v1.2.3) (2017-01-22)
[Full Changelog](https://github.com/mcs07/ChemDataExtractor/compare/v1.2.2...v1.2.3)

**Fixed bugs:**

- \_in\_stoplist should return True for entities trimmed out of existence [\#12](https://github.com/mcs07/ChemDataExtractor/issues/12)

## [v1.2.2](https://github.com/mcs07/ChemDataExtractor/releases/tag/v1.2.2) (2016-11-02)
[Full Changelog](https://github.com/mcs07/ChemDataExtractor/compare/v1.2.1...v1.2.2)

**Fixed bugs:**

- Fix issues with reference link extraction using HTML/XML readers [\#10](https://github.com/mcs07/ChemDataExtractor/pull/10) ([mcs07](https://github.com/mcs07))

## [v1.2.1](https://github.com/mcs07/ChemDataExtractor/releases/tag/v1.2.1) (2016-10-24)
[Full Changelog](https://github.com/mcs07/ChemDataExtractor/compare/v1.2.0...v1.2.1)

**Fixed bugs:**

- RSCHTMLReader throws bytes/string error [\#8](https://github.com/mcs07/ChemDataExtractor/issues/8)
- Fix encoding bug in RSC image character handling [\#9](https://github.com/mcs07/ChemDataExtractor/pull/9) ([mcs07](https://github.com/mcs07))

## [v1.2.0](https://github.com/mcs07/ChemDataExtractor/releases/tag/v1.2.0) (2016-10-11)
[Full Changelog](https://github.com/mcs07/ChemDataExtractor/compare/v1.1.1...v1.2.0)

**Implemented enhancements:**

- New model layer [\#5](https://github.com/mcs07/ChemDataExtractor/pull/5) ([mcs07](https://github.com/mcs07))

**Fixed bugs:**

- import error: HTMLParser in Python 3 [\#7](https://github.com/mcs07/ChemDataExtractor/issues/7)
- Installation on Windows 7 [\#3](https://github.com/mcs07/ChemDataExtractor/issues/3)
- HTML unescape py2/3 compat - fixes \#4 [\#6](https://github.com/mcs07/ChemDataExtractor/pull/6) ([mcs07](https://github.com/mcs07))

## [v1.1.1](https://github.com/mcs07/ChemDataExtractor/releases/tag/v1.1.1) (2016-10-04)
[Full Changelog](https://github.com/mcs07/ChemDataExtractor/compare/v1.1.0...v1.1.1)

**Implemented enhancements:**

- Python 3 compatibility [\#2](https://github.com/mcs07/ChemDataExtractor/pull/2) ([mcs07](https://github.com/mcs07))

**Fixed bugs:**

- version of pdfminer [\#1](https://github.com/mcs07/ChemDataExtractor/issues/1)

## [v1.1.0](https://github.com/mcs07/ChemDataExtractor/releases/tag/v1.1.0) (2016-10-03)


\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*
