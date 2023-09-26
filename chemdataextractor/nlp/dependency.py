import logging
import logging.config
import stanza
from ..nlp.tag import BaseTagger, EnsembleTagger
from collections import namedtuple


# current_level = logging.root.level
# To counteract stanza messing up the log level
# logging.config.dictConfig({"version": 1, "loggers": {"": {"level": current_level}}})

Dependency = namedtuple("Dependency", ["head", "relation"])


class IndexTagger(BaseTagger):
    tag_type = "index"

    def tag(self, tokens):
        return zip(tokens, range(len(tokens)))


class _DependencyTagger(BaseTagger):

    tag_type = "dependency"

    def __init__(self):
        try:
            self._nlp = stanza.Pipeline("en", tokenize_pretokenized=True, logging_level="ERROR")
        except Exception:
            stanza.download("en", resources_version="1.1.0")
            self._nlp = stanza.Pipeline("en", tokenize_pretokenized=True, logging_level="ERROR")

    def _tokens_to_stanza_tokens(self, tokens):
        return [token.text for token in tokens]

    def tag(self, tokens):
        stanza_tok = self._tokens_to_stanza_tokens(tokens)
        doc = self._nlp([stanza_tok])
        labels = []
        for word in doc.sentences[0].words:
            relation = word.deprel
            if relation == "root":
                labels.append(Dependency(None, relation))
            else:
                labels.append(Dependency(tokens[word.head - 1], relation))
        return zip(tokens, labels)

    def batch_tag(self, sents):
        stanza_toks = [self._tokens_to_stanza_tokens(sent) for sent in sents]
        doc = self._nlp(stanza_toks)
        labels = []
        for tokens, sent in zip(sents, doc.sentences):
            sent_labels = []
            for word in sent.words:
                relation = word.deprel
                if relation == "root":
                    sent_labels.append(Dependency(None, relation))
                else:
                    sent_labels.append(Dependency(tokens[word.head - 1], relation))
            labels.append(zip(tokens, sent_labels))
        return labels


class DependencyTagger(EnsembleTagger):
    taggers = [_DependencyTagger(), IndexTagger()]

