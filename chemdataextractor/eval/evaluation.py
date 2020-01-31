"""
Scripts for evaluation.

Usage::

    tg_eval = Evaluate(GlassTransitionTemperature, folder=r'./scraped', n_papers_limit=200, n_records_limit=200)
    tg_eval.eval()
    tg_eval.print_results()

Here, `GlassTransitionTemperature` is a ChemDataExtractor model and `folder` is the folder with papers to be analyzed.
`n_papers_limit` and `n_records_limit` are the minima required for termination of the evaluation.
Both must be satisfied.

To continue the evaluation if interrupted::

    pickle_file = open("evaluation.pickle", "rb")
    tg_eval = pickle.load(pickle_file)
    tg_eval.eval()
    tg_eval.print_results()

A log file capturing the interactive terminal output and input is maintained in `evaluation-log.txt`.
The latest results are updated in 1results.txt`.

"""

import sys
import os
import webbrowser
from playsound import playsound
import pickle
import pkg_resources
import os
from pprint import pprint

from .. import Document


class Logger:
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("evaluation-log.txt", "a", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()


sys.stdout = Logger()


def documents(folder):
    """Yields CDE documents for a given folder"""
    for i, filename in enumerate(sorted(os.listdir(folder))):
        if filename[0] != '.':
            file_path = os.path.join(folder, filename)
            fb = open(file_path, 'rb')
            doc = Document.from_file(fb)
            fb.close()
            yield doc, file_path


def records(cde_doc, models):
    """Yields CDE records for a given CDE document and CDE model"""
    cde_doc.models = []
    for m in models:
        cde_doc.models.append(m)
    recs = cde_doc.records
    if recs:
        for record in recs:
            if isinstance(record, tuple(models)):
                yield record


class Evaluate:
    """Main class for evaluation of a particular model on a given corpus of literature"""
    def __init__(self, models, folder=r'./', n_papers_limit=200, n_records_limit=200, play_sound=True, show_website=True, _automated=False):
        self._automated = _automated
        self.play_sound = play_sound
        self.show_website = show_website
        self.folder = folder
        self.models = models
        self.n_papers_limit = n_papers_limit
        self.n_records_limit = n_records_limit
        self.n_papers = len(os.listdir(folder))

        # number of paper that was last evaluated
        self.n_paper = -1

        # number of records found in the corpus
        self.n_unidentified = 0
        self.n_records = 0

        # correct records
        self.nc = 0
        self.nc_autosentence = 0
        self.nc_template = 0
        self.nc_snowball = 0
        self.nc_table = 0
        self.nc_definition = 0

        # correct and duplicate
        self.ncd = 0
        self.ncd_autosentence = 0
        self.ncd_template = 0
        self.ncd_snowball = 0
        self.ncd_table = 0
        self.ncd_definition = 0

        # wrong records
        self.nw = 0
        self.nw_cer = 0
        self.nw_autosentence = 0
        self.nw_template = 0
        self.nw_snowball = 0
        self.nw_table = 0
        self.nw_table_tde = 0
        self.nw_table_cde = 0
        self.nw_definition = 0
        self.nw_interdependency = 0
        self.nw_other = 0

        # list containing description of other failures
        self.w_other = []

    def eval(self):
        """Evaluates the corpus"""
        f = open("results.txt", "w", encoding='utf-8')
        for n_paper, doc in enumerate(documents(self.folder)):

            # if loaded from pickle, eval will start where left of
            if n_paper <= self.n_paper and self.n_paper >= 0:
                continue

            print("Paper {}/{}".format(n_paper, self.n_papers))
            print("DOI:       {}".format(doc[0].metadata.doi))
            print("Journal:   {}".format(doc[0].metadata.journal))
            print("Publisher: {}".format(doc[0].metadata.publisher))
            print("PDF Url:   {}".format(doc[0].metadata.pdf_url))
            print("HTML Url:  {}".format(doc[0].metadata.html_url))

            doc_opened = False
            for record in records(doc[0], self.models):
                if record.is_unidentified:
                    self.n_unidentified += 1
                if not record.is_unidentified:
                    self.n_records += 1

                    print("Record {}: \n".format(self.n_records))
                    pprint(record.serialize())
                    print("    Method:  {}".format(record.record_method))
                    print("    Updated: {}".format(record.updated))
                    if self.play_sound:
                        sound_file = pkg_resources.resource_filename('chemdataextractor', 'eval/sound.mp3')
                        playsound(sound_file)

                    if not doc_opened and self.show_website:
                        webbrowser.open(doc[0].metadata.html_url)
                        doc_opened = True
                    if self._automated:
                        input_cw = 0
                    else:
                        input_cw = input("    Correct (0)   OR   Correct and duplicate (1)   OR   Wrong (2)   OR   SKIP (3)?")
                        try:
                            input_cw = int(input_cw)
                        except ValueError:
                            input_cw = input("    Correct (0)   OR   Correct and duplicate (1)   OR   Wrong (2)   OR   SKIP (3)?")
                            input_cw = int(input_cw)
                            print("         {}".format(input_cw))

                    if input_cw == 0:
                        self.nc += 1

                        if record.record_method == 'AutoSentenceParser':
                            self.nc_autosentence += 1
                        elif record.record_method == 'QuantityModelTemplateParser' or record.record_method == 'MultiQuantityModelTemplateParser':
                            self.nc_template += 1
                        elif record.record_method == 'Snowball':
                            self.nc_snowball += 1
                        elif record.record_method == 'AutoTableParser':
                            self.nc_table += 1

                        if record.updated:
                            self.nc_definition += 1
                            # print(doc[0].definitions)

                    if input_cw == 1:
                        self.ncd += 1

                        if record.record_method == 'AutoSentenceParser':
                            self.ncd_autosentence += 1
                        elif record.record_method == 'QuantityModelTemplateParser' or record.record_method == 'MultiQuantityModelTemplateParser':
                            self.ncd_template += 1
                        elif record.record_method == 'Snowball':
                            self.ncd_snowball += 1
                        elif record.record_method == 'AutoTableParser':
                            self.ncd_table += 1

                        if record.updated:
                            self.ncd_definition += 1

                    if input_cw == 2:
                        self.nw += 1

                        input_w = input("    CER (1), AutoSentence (2), AutoTemplate (3), Snowball (4), Table (5), Definition update (6), Interdependency resolution (7), Other (8)? ")
                        try:
                            input_w = int(input_w)
                        except ValueError:
                            input_w = input("    CER (1), AutoSentence (2), AutoTemplate (3), Snowball (4), Table (5), Definition update (6), Interdependency resolution (7), Other (8)? ")
                            input_w = int(input_w)
                        print("         {}".format(input_w))

                        if input_w == 1:
                            self.nw_cer += 1
                        elif input_w == 2:
                            self.nw_autosentence += 1
                        elif input_w == 3:
                            self.nw_template += 1
                        elif input_w == 4:
                            self.nw_snowball += 1
                        elif input_w == 5:
                            self.nw_table += 1
                        elif input_w == 6:
                            self.nw_definition += 1
                        elif input_w == 7:
                            self.nw_interdependency += 1
                        elif input_w == 8:
                            self.nw_other += 1

                        if input_w == 5:
                            for table in doc[0].tables:
                                print(table.tde_table)
                                table.tde_table.print()
                                print(table.tde_table.history)

                            input_w_table = input("    TDE (1) or CDE (2)?")
                            try:
                                input_w_table = int(input_w_table)
                            except ValueError:
                                input_w_table = input("    TDE (1) or CDE (2)?")
                                input_w_table = int(input_w_table)
                            print("         {}".format(input_w_table))

                            if input_w_table == 1:
                                self.nw_table_tde += 1
                            elif input_w_table == 2:
                                self.nw_table_cde += 1

                        if input_w == 8:
                            input_w_other = input("    Describe: ")
                            self.w_other.append(input_w_other)
                            print("             {}".format(input_w_other))

                    if input_cw == 3:
                        continue

                if self.limits_reached:
                    break

            self.n_paper = n_paper
            pickling_file = open('evaluation.pickle', 'wb')
            pickle.dump(self, pickling_file)
            pickling_file.close()
            f.seek(0)
            f.truncate()
            self.print_results(destination=f)
            f.flush()

            if self.limits_reached:
                if self.play_sound:
                    sound_end_file = pkg_resources.resource_filename('chemdataextractor', 'eval/sound_end.mp3')
                    playsound(sound_end_file)
                break
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
        print("Correct records: {}".format(self.nc), file=destination)
        print("    Correct AutoSentence: {}".format(self.nc_autosentence), file=destination)
        print("    Correct Template:     {}".format(self.nc_template), file=destination)
        print("    Correct Snowball:     {}".format(self.nc_snowball), file=destination)
        print("    Correct AutoTable:    {}".format(self.nc_table), file=destination)
        print("    Correct Definition:   {}".format(self.nc_definition), file=destination)
        print("", file=destination)
        print("Correct and duplicate records: {}".format(self.ncd), file=destination)
        print("    Duplicate AutoSentence: {}".format(self.ncd_autosentence), file=destination)
        print("    Duplicate Template:     {}".format(self.ncd_template), file=destination)
        print("    Duplicate Snowball:     {}".format(self.ncd_snowball), file=destination)
        print("    Duplicate AutoTable:    {}".format(self.ncd_table), file=destination)
        print("    Duplicate Definition:   {}".format(self.ncd_definition), file=destination)
        print("", file=destination)
        print("Wrong records: {}".format(self.nw), file=destination)
        print("    Wrong CER:          {}".format(self.nw_cer), file=destination)
        print("    Wrong AutoSentence: {}".format(self.nw_autosentence), file=destination)
        print("    Wrong Template:     {}".format(self.nw_template), file=destination)
        print("    Wrong Snowball:     {}".format(self.nw_snowball), file=destination)
        print("    Wrong AutoTable:    {}".format(self.nw_table), file=destination)
        print("        TDE:            {}".format(self.nw_table_tde), file=destination)
        print("        CDE:            {}".format(self.nw_table_cde), file=destination)
        print("    Wrong Definition:   {}".format(self.nw_definition), file=destination)
        print("    W. Interdependency: {}".format(self.nw_interdependency), file=destination)
        print("    Other:              {}".format(self.nw_other), file=destination)
        for item in self.w_other:
            print("        {}".format(item), file=destination)
        print("", file=destination)
        print(" PRECISION ", file=destination)
        print("===========", file=destination)
        print("", file=destination)
        if (self.nc+self.nw) != 0:
            print("Total precision                      = {:4.2f}, {}/{}".format((self.nc/(self.nc+self.nw)), self.nc, self.nc+self.nw), file=destination)
        if (self.nc+self.nw-self.nw_autosentence) != 0:
            print("Precision without AutoSentenceParser = {:4.2f}, {}/{}   ---> Approximation".format((self.nc-self.nc_autosentence)/(self.nc+self.nw-self.nw_autosentence), (self.nc-self.nc_autosentence), (self.nc+self.nw-self.nw_autosentence)), file=destination)
        if (self.nc+self.nw-self.nw_cer) != 0:
            print("Precision without CER Errors         = {:4.2f}, {}/{}".format((self.nc/(self.nc+self.nw-self.nw_cer)), self.nc, (self.nc+self.nw-self.nw_cer)), file=destination)
        if (self.nc+self.nw-self.nw_autosentence-self.nw_cer) != 0:
            print("Precision without AutoS. and CER     = {:4.2f}, {}/{}". format((self.nc-self.nc_autosentence)/(self.nc+self.nw-self.nw_autosentence-self.nw_cer), (self.nc-self.nc_autosentence), (self.nc+self.nw-self.nw_autosentence-self.nw_cer)), file=destination)
        if (self.nc_table+self.nw_table) != 0:
            print("Table Precision                      = {:4.2f}, {}/{}".format(self.nc_table/(self.nc_table+self.nw_table), self.nc_table, (self.nc_table+self.nw_table)), file=destination)
        if self.nw_table != 0:
            print("   TDE Errors within Table Errors    = {:4.2f}, {}/{}".format(self.nw_table_tde/self.nw_table, self.nw_table_tde, self.nw_table), file=destination)
            print("   CDE Errors within Table Errors    = {:4.2f}, {}/{}".format(self.nw_table_cde/self.nw_table, self.nw_table_cde, self.nw_table), file=destination)
        if (self.nc_template+self.nw_template) != 0:
            print("Template Precision                   = {:4.2f}, {}/{}".format(self.nc_template/(self.nc_template+self.nw_template), self.nc_template, (self.nc_template+self.nw_template)), file=destination)
        if (self.nc_snowball+self.nw_snowball) != 0:
            print("Snowball Precision                   = {:4.2f}, {}/{}".format(self.nc_snowball/(self.nc_snowball+self.nw_snowball), self.nc_snowball, (self.nc_snowball+self.nw_snowball)), file=destination)
        if (self.nc_definition+self.nw_definition) != 0:
            print("Definitions update Precision         = {:4.2f}, {}/{}".format(self.nc_definition/(self.nc_definition+self.nw_definition), self.nc_definition, (self.nc_definition+self.nw_definition)), file=destination)
        if self.nw != 0:
            print("Percentage of 'other' errors         = {:4.2f}, {}/{}".format(self.nw_other/self.nw, self.nw_other, self.nw), file=destination)


