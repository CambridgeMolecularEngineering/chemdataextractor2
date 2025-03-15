from .dependency import Dependency, IndexTagger
from .tag import BaseTagger, EnsembleTagger
from ..data import Package, find_data, PACKAGES

import socketserver
import os
import atexit
from yaspin import yaspin

import stanza
from stanza.server import CoreNLPClient


corenlp_loc = "models/corenlp"


def _setup_corenlp(local_path, force=False):
    stanza.install_corenlp(dir=local_path)


corenlp_package = Package(corenlp_loc, custom_download=_setup_corenlp)
PACKAGES.append(corenlp_package)


class _CoreNLPDependencyTagger(BaseTagger):
    tag_type = "dependency"

    def __init__(self, client=None):
        self._client = client
        atexit.register(self.stop_server)

    @property
    def client(self):
        if self._client is None:
            with yaspin(
                text="Initialising CoreNLP client", side="right"
            ).simpleDots as sp:
                os.environ["CORENLP_HOME"] = find_data(corenlp_loc)
                with socketserver.TCPServer(("localhost", 0), None) as s:
                    free_port = s.server_address[1]

                self._client = CoreNLPClient(
                    timeout=30000,
                    memory="16G",
                    endpoint=f"http://localhost:{free_port}",
                    annotators=["tokenize", "ssplit", "pos", "ner", "depparse"],
                    be_quiet=True,
                    properties={
                        "tokenize.whitespace": "true",
                        "ssplit.eolonly": "true",
                    },
                )
                sp.ok("✔")
        return self._client

    def tag(self, tokens):
        text_tokens = " ".join([token.text for token in tokens])
        annotated = self.client.annotate(text_tokens)
        sent = annotated.sentence[0]
        dependencies = sent.basicDependencies

        if len(dependencies.node) != len(tokens):
            raise IndexError(
                f"The length of the sequence returned by CoreNLP({len(dependencies.node)}) does not match the number of tokens passed in ({len(tokens)}) for the sentence {tokens[0].sentence.text}"
            )

        labels = [None for _ in range(len(tokens))]

        for edge in dependencies.edge:
            source_loc = edge.source - 1
            target_loc = edge.target - 1
            relation = edge.dep
            labels[target_loc] = Dependency(tokens[source_loc], relation)
        labels[dependencies.root[0] - 1] = Dependency(None, "root")

        return zip(tokens, labels)

    def batch_tag(self, sents):
        all_text = "\n".join(
            [" ".join([token.text for token in sent]) for sent in sents]
        )
        annotated = self.client.annotate(all_text)

        all_labels = []

        for sent, tokens in zip(annotated.sentence, sents):
            dependencies = sent.basicDependencies

            if len(dependencies.node) != len(tokens):
                raise IndexError(
                    f"The length of the sequence returned by CoreNLP({len(dependencies.node)}) does not match the number of tokens passed in ({len(tokens)}) for the sentence {tokens[0].sentence.text}"
                )

            labels = [None for _ in range(len(tokens))]

            for edge in dependencies.edge:
                source_loc = edge.source - 1
                target_loc = edge.target - 1
                relation = edge.dep
                labels[target_loc] = Dependency(tokens[source_loc], relation)
            labels[dependencies.root[0] - 1] = Dependency(None, "root")

            all_labels.append(zip(tokens, labels))

        return all_labels

    def stop_server(self):
        if self._client is not None:
            self._client.stop()


class CoreNLPDependencyTagger(EnsembleTagger):
    taggers = [_CoreNLPDependencyTagger(), IndexTagger()]
