import spacy

from .dependency import Dependency, IndexTagger
from .tag import BaseTagger, EnsembleTagger


class _SpacyDependencyTagger(BaseTagger):
    tag_type = "dependency"

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.tokenizer = self.nlp.tokenizer.tokens_from_list

    def tag(self, tokens):
        return self.batch_tag([tokens])[0]

    def batch_tag(self, sents):
        tokens_list = [[token.text for token in tokens] for tokens in sents]
        all_labels = []
        for tokens, processed in zip(sents, self.nlp.pipe(tokens_list)):
            labels = []
            for spacy_token in processed:
                relation = spacy_token.dep_
                if relation == "ROOT":
                    labels.append(Dependency(None, "root"))
                else:
                    labels.append(Dependency(tokens[spacy_token.head.i], relation))
            all_labels.append(zip(tokens, labels))
        return all_labels


class SpacyDependencyTagger(EnsembleTagger):
    taggers = [_SpacyDependencyTagger(), IndexTagger()]
