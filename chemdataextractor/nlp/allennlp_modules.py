"""
Modules used in the BERT CRF tagger that are originally from AllenNLP
https://github.com/allenai/allennlp/blob/v0.9.0/allennlp/modules/time_distributed.py
https://github.com/allenai/allennlp/blob/v0.9.0/allennlp/data/tokenizers/token.py
"""

from typing import List, NamedTuple

from overrides import overrides
import torch


class TimeDistributed(torch.nn.Module):
    """
    A wrapper that unrolls the second (time) dimension of a tensor
    into the first (batch) dimension, applies some other `Module`,
    and then rolls the time dimension back up.

    Given an input shaped like `(batch_size, time_steps, [rest])` and a `Module` that takes
    inputs like `(batch_size, [rest])`, `TimeDistributed` reshapes the input to be
    `(batch_size * time_steps, [rest])`, applies the contained `Module`, then reshapes it back.

    Note that while the above gives shapes with `batch_size` first, this `Module` also works if
    `batch_size` is second - we always just combine the first two dimensions, then split them.

    It also reshapes keyword arguments unless they are not tensors or their name is specified in
    the optional `pass_through` iterable.
    """

    def __init__(self, module):
        super().__init__()
        self._module = module

    @overrides
    def forward(self, *inputs, pass_through: List[str] = None, **kwargs):

        pass_through = pass_through or []

        reshaped_inputs = [
            self._reshape_tensor(input_tensor) for input_tensor in inputs
        ]

        # Need some input to then get the batch_size and time_steps.
        some_input = None
        if inputs:
            some_input = inputs[-1]

        reshaped_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, torch.Tensor) and key not in pass_through:
                if some_input is None:
                    some_input = value

                value = self._reshape_tensor(value)

            reshaped_kwargs[key] = value

        reshaped_outputs = self._module(*reshaped_inputs, **reshaped_kwargs)

        if some_input is None:
            raise RuntimeError("No input tensor to time-distribute")

        # Now get the output back into the right shape.
        # (batch_size, time_steps, **output_size)
        tuple_output = True
        if not isinstance(reshaped_outputs, tuple):
            tuple_output = False
            reshaped_outputs = (reshaped_outputs,)

        outputs = []
        for reshaped_output in reshaped_outputs:
            new_size = some_input.size()[:2] + reshaped_output.size()[1:]
            outputs.append(reshaped_output.contiguous().view(new_size))

        if not tuple_output:
            outputs = outputs[0]

        return outputs

    @staticmethod
    def _reshape_tensor(input_tensor):
        input_size = input_tensor.size()
        if len(input_size) <= 2:
            raise RuntimeError(f"No dimension to distribute: {input_size}")
        # Squash batch_size and time_steps into a single axis; result has shape
        # (batch_size * time_steps, **input_size).
        squashed_shape = [-1] + list(input_size[2:])
        return input_tensor.contiguous().view(*squashed_shape)


class Token(NamedTuple):
    """
    A simple token representation, keeping track of the token's text, offset in the passage it was
    taken from, POS tag, dependency relation, and similar information.  These fields match spacy's
    exactly, so we can just use a spacy token for this.

    Parameters
    ----------
    text : ``str``, optional
        The original text represented by this token.
    idx : ``int``, optional
        The character offset of this token into the tokenized passage.
    lemma_ : ``str``, optional
        The lemma of this token.
    pos_ : ``str``, optional
        The coarse-grained part of speech of this token.
    tag_ : ``str``, optional
        The fine-grained part of speech of this token.
    dep_ : ``str``, optional
        The dependency relation for this token.
    ent_type_ : ``str``, optional
        The entity type (i.e., the NER tag) for this token.
    text_id : ``int``, optional
        If your tokenizer returns integers instead of strings (e.g., because you're doing byte
        encoding, or some hash-based embedding), set this with the integer.  If this is set, we
        will bypass the vocabulary when indexing this token, regardless of whether ``text`` is also
        set.  You can `also` set ``text`` with the original text, if you want, so that you can
        still use a character-level representation in addition to a hash-based word embedding.

        The other fields on ``Token`` follow the fields on spacy's ``Token`` object; this is one we
        added, similar to spacy's ``lex_id``.
    """

    text: str = None
    idx: int = None
    lemma_: str = None
    pos_: str = None
    tag_: str = None
    dep_: str = None
    ent_type_: str = None
    text_id: int = None

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.__str__()


def show_token(token: Token) -> str:
    return (
        f"{token.text} "
        f"(idx: {token.idx}) "
        f"(lemma: {token.lemma_}) "
        f"(pos: {token.pos_}) "
        f"(tag: {token.tag_}) "
        f"(dep: {token.dep_}) "
        f"(ent_type: {token.ent_type_}) "
    )
