"""
Tools for production run data-extraction.

.. codeauthor:: Juraj Mavračić <jm2111@cam.ac.uk>

"""

import os
import sys
from pprint import pprint
from pymongo import MongoClient
from datetime import datetime
from chemdataextractor.scrape import Selector, RscHtmlDocument, ElsevierXmlDocument
from chemdataextractor.scrape.pub.springer import SpringerHtmlDocument
from .evaluation import documents
from cde_additions.analysis.compounds import find_elements


def detect_publisher(fstring):
    """
    Detect the publisher of a file by searching for unique strings

    .. codeauthor:: Callum Court

    """
    if b'<meta name="dc.Identifier" scheme="doi" content="10.1021/' in fstring:
        return 'acs'
    elif b'content="10.1039/' in fstring:
        return 'rsc'
    elif b'<link rel="canonical" href="http://www.sciencedirect.com/' in fstring:
        return 'elsevier'
    elif b'full-text-retrieval-response' in fstring:
        return 'elsevier'
    elif b'<meta content="10.1007/' in fstring or b'<meta content="https://link.springer.com' in fstring or b'<meta name="citation_doi" content="10.1007/' in fstring:
        return 'springer'
    return None


def get_cde_document_info(fname):
    """
    Scrape document information using ChemDataExtractor Scrapers

    .. codeauthor:: Callum Court

    """
    f = open(fname, 'rb').read()
    sel = Selector.from_text(f)
    # Determine which journal the document is from and file type,  use the
    # RSC scraper by default
    publisher = detect_publisher(f)
    if publisher == 'rsc':
        document_info = RscHtmlDocument(sel)
        return document_info.serialize()
    elif publisher == 'elsevier':
        document_info = ElsevierXmlDocument(sel)
        return document_info.serialize()
    elif publisher == 'springer':
        document_info = SpringerHtmlDocument(sel)
        return document_info
    return None


def records(cde_doc, models):
    """Yields CDE records for a given CDE document and CDE model"""
    cde_doc.models = models
    recs = cde_doc.records
    if recs:
        for record in recs:
            if isinstance(record, tuple(models)):
                yield record


class Extractor:
    """
    Main class for extraction of data for a particular CDE 2.0 model on a given corpus of literature.
    Automatically connects to a MongoDB host and writes to the database.

    :param cde_models: ChemDataExtractor 2.0 User Models list
    :param database: Tuple containing the name of the database and the name of the collection
    :param sources_dir: Directory containing the papers to be processed
    :param mongodb_host: Host of the MongoDb database, in MongoDB URI format
    :param name: Used to name the output and pickle files
    :param n_papers_limit: Maximal number of papers to process
    :param n_records_limit: Maximal number of records to retrieve
    :param verbose: Paper information, with URL links and records are printed

    :type cde_models: ~chemdataextractor.model.base.BaseModel
    :type database: (str,str)
    :type sources_dir: str
    :type mongodb_host: str
    :type name: str
    :type n_papers_limit: int
    :type n_records_limit: int
    :type verbose: bool
    """
    def __init__(self,
                 cde_models,
                 database,
                 sources_dir=r'./',
                 mongodb_host='mongodb://localhost:27017/',
                 name='extraction',
                 n_papers_limit=1000000,
                 n_records_limit=1000000,
                 verbose=True,
                 ):
        """
        Initializes the user-defined parameters, checks MongoDB connection and stores a pickle object.
        """
        self.cde_models = cde_models
        self.sources_dir = sources_dir
        self.mongodb_host = mongodb_host
        self.name = name
        self.n_papers_limit = n_papers_limit
        self.n_records_limit = n_records_limit
        self.verbose = verbose

        # total number of papers to be processed
        self.n_papers = len(os.listdir(self.sources_dir))
        # number of paper that was last evaluated
        self.n_paper = -1

        # number of records found in the corpus
        self.n_unidentified = 0
        self.n_records = 0
        self.n_autosentence = 0
        self.n_autotemplate_single = 0
        self.n_autotemplate_multi_1 = 0
        self.n_autotemplate_multi_2 = 0
        self.n_autotemplate_multi_3 = 0
        self.n_autotemplate_multi_4 = 0
        self.n_snowball = 0
        self.n_table = 0
        self.n_definition_update = 0

        # MongoDB connection
        client = MongoClient(self.mongodb_host)
        self.db = getattr(client, database[0])
        self.collection = getattr(self.db, database[1])

    def extract(self):
        """
        Processes the papers and extracts values. Writes a file with an extraction summary.
        """
        f = open(self.name+".txt", "w", encoding='utf-8')
        for n_paper, doc in enumerate(documents(self.sources_dir)):

            # if loaded from pickle, eval will start where left of
            if n_paper <= self.n_paper and self.n_paper >= 0:
                continue

            # add the models first, as otherwise there might be interference with other things, such as doc.cems
            doc[0].models = []
            for model in self.cde_models:
                doc[0].models.append(model)

            print("Paper {}/{}".format(n_paper, self.n_papers))
            if self.verbose:
                print("DOI:       {}".format(doc[0].metadata.doi))
                print("Journal:   {}".format(doc[0].metadata.journal))
                print("Publisher: {}".format(doc[0].metadata.publisher))
                print("PDF Url:   {}".format(doc[0].metadata.pdf_url))
                print("HTML Url:  {}".format(doc[0].metadata.html_url))

            # document info which will be associated with each record for this document
            document_info = get_cde_document_info(doc[1])
            html_url = doc[0].metadata.html_url
            pdf_url = doc[0].metadata.pdf_url

            cems = []
            for cem in doc[0].cems:
                cems.append(str(cem))

            definitions = doc[0].definitions
            # abbreviation_definitions = doc[0].abbreviation_definitions
            abbreviation_definitions = []
            for abrv in doc[0].abbreviation_definitions:
                entry = dict()
                entry['abbreviation'] = ' '.join(abrv[0])
                entry['long_form'] = ' '.join(abrv[1])
                abbreviation_definitions.append(entry)

            # TODO Add chemical definitions in the future
            # chemical_definitions = doc[0].chemical_definitions

            for record in records(doc[0], self.cde_models):
                if record.is_unidentified:
                    self.n_unidentified += 1
                if not record.is_unidentified:
                    self.n_records += 1

                    # counting of all the metadata for the summary
                    if record.record_method == 'AutoSentenceParser':
                        self.n_autosentence += 1
                    elif record.record_method == 'PropertyParserTemplate':
                        self.n_autotemplate_single += 1
                    elif record.record_method == 'multi_entity_phrase_1':
                        self.n_autotemplate_multi_1 += 1
                    elif record.record_method == 'multi_entity_phrase_2':
                        self.n_autotemplate_multi_2 += 1
                    elif record.record_method == 'multi_entity_phrase_3':
                        self.n_autotemplate_multi_3 += 1
                    elif record.record_method == 'multi_entity_phrase_4':
                        self.n_autotemplate_multi_4 += 1
                    elif record.record_method == 'Snowball':
                        self.n_snowball += 1
                    elif record.record_method == 'AutoTableParser':
                        self.n_table += 1
                    if record.updated:
                        self.n_definition_update += 1

                    # Build the full MongoDB entry to insert into the database
                    # save the record
                    entry = record.serialize()
                    # add the cde2 method (parser) information
                    entry[record.__class__.__name__]['cde2_method'] = record.record_method
                    # add information about the definitions update
                    entry[record.__class__.__name__]['cde2_updated'] = record.updated
                    # add the chemical elements explicitly
                    try:
                        compounds = entry[record.__class__.__name__]['compound'][record.compound.__class__.__name__]['names']
                    except KeyError:
                        pass
                    else:
                        elements = find_elements(compounds)
                        entry[record.__class__.__name__]['compound']['elements'] = elements
                    # add metadata from the journal/document
                    entry['Document'] = {}
                    entry['Document']['doi'] = document_info['doi'] if 'doi' in document_info else None
                    entry['Document']['journal'] = document_info['journal'] if 'journal' in document_info else None
                    entry['Document']['volume'] = document_info['volume'] if 'volume' in document_info else None
                    entry['Document']['issue'] = document_info['issue'] if 'issue' in document_info else None
                    entry['Document']['pages'] = document_info['pages'] if 'pages' in document_info else None
                    entry['Document']['copyright'] = document_info['copyright'] if 'copyright' in document_info else None
                    entry['Document']['published_date'] = datetime.strptime(document_info['published_date'], '%Y-%m-%d') if 'published_date' in document_info else None
                    entry['Document']['authors'] = document_info['authors'] if 'authors' in document_info else None
                    entry['Document']['title'] = document_info['title'] if 'title' in document_info else None
                    entry['Document']['url'] = document_info['url'] if 'url' in document_info else None
                    entry['Document']['html_url'] = html_url
                    entry['Document']['pdf_url'] = pdf_url
                    entry['Document']['cems'] = cems
                    entry['Document']['abbreviation_definitions'] = abbreviation_definitions
                    entry['Document']['definitions'] = definitions
                    # add chemical definitions
                    # entry['Document']['chemical_definitions'] = chemical_definitions

                    if self.verbose:
                        print("Record {}: \n".format(self.n_records), flush=True)
                        pprint(entry)

                    # insert entry into MongoDB database
                    mongo_result = self.collection.insert_one(entry)
                    if mongo_result.inserted_id:
                        print("    MongoID: {}".format(mongo_result.inserted_id))
                    elif not mongo_result.acknowledged:
                        print("    Writing to MongoDB failed!")

                if self.limits_reached:
                    break

            # updating the number of the current paper being processed
            self.n_paper = n_paper

            # update the extraction summary
            f.seek(0)
            f.truncate()
            self.print_results(destination=f)
            f.flush()

            if self.verbose:
                print("")

            if self.limits_reached:
                break

        if self.verbose:
            print("")
            self.print_results()
            print("")

        f.close()

    @property
    def limits_reached(self):
        if self.n_paper+1 >= self.n_papers_limit and self.n_records >= self.n_records_limit:
            return True
        else:
            return False

    def print_results(self, destination=sys.stdout):
        """Prints the results of evaluation"""
        print("===================================================", file=destination)
        print("                  RESULTS                          ", file=destination)
        print("===================================================", file=destination)
        print("", file=destination)
        print("Number of papers tested: {}".format(self.n_paper+1), file=destination)
        print("Unidentified records: {}".format(self.n_unidentified), file=destination)
        print("Total records (correct+wrong+skipped): {}".format(self.n_records), file=destination)
        print("", file=destination)
        print("    AutoSentence:         {}".format(self.n_autosentence), file=destination)
        print("    AutoTemplate Simple:  {}".format(self.n_autotemplate_single), file=destination)
        print("    AutoTemplate Multi 1: {}".format(self.n_autotemplate_multi_1), file=destination)
        print("    AutoTemplate Multi 2: {}".format(self.n_autotemplate_multi_2), file=destination)
        print("    AutoTemplate Multi 3: {}".format(self.n_autotemplate_multi_3), file=destination)
        print("    AutoTemplate Multi 4: {}".format(self.n_autotemplate_multi_4), file=destination)
        print("    Snowball:             {}".format(self.n_snowball), file=destination)
        print("    AutoTable:            {}".format(self.n_table), file=destination)
        print("    Definition Updates:   {}".format(self.n_definition_update), file=destination)
        print("", file=destination)
