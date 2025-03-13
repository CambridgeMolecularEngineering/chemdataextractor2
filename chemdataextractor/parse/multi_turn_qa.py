# -*- coding: utf-8 -*-
"""
Functionality to enable multi-turn question answering for information extraction in ChemDataExtractor

.. codeauthor:: Taketomo Isazawa <ti250@cam.ac.uk>
"""

import torch
from ..doc.text import Subsentence
from ..model.contextual_range import SentenceRange
from ..parse.auto import AutoSentenceParser
from ..parse.base import BaseSentenceParser
from ..parse.elements import NoMatch, OneOrMore, Optional, SkipTo
from ..parse.quantity import value_element
from ..utils import memoized_property

from transformers.pipelines import pipeline


class Question(NoMatch):
    """
    Question to be used for multi-turn question answering.
    This can only be used by certain parsers, such as `MultiTurnQAParser`.
    Other parsers will treat this parse element the same as a `NoMatch` element.

    Use this to define a template question alongside the fields that are
    used to fill in the template question. Also accessible using shorthand
    as `Q`

    An example for photocatalysis:

    .. code-block:: python

        compound = ModelType(
            parse_expression=Q(
                "What photocatalytic material has a {} of {}?",
                ["specifier", "val_units"],
            )(".names")
        )

    .. note::
        If you're using a Question expression to extract information,
        and you're extracting for a field on a sub-model, as is the
        case with the compound in the example above, simply name it
        (i.e. call the parse_expression), with the keypath to the field
        you want, and `MultiTurnQAParser` will do the right thing when
        constructing models
    """

    def __init__(
        self,
        question,
        fields,
        confidence_threshold=None,
        num_preceding_sentences=4,
        num_following_sentences=0,
        include_heading=True,
        no_merge_range=1,
    ):
        """
        Args:
            question (str): A template for the question, in the same format as an f-string (i.e. use
                curly brackets where the template needs to be filled)
            fields (str): Any prerequisite fields to fill in the template above
            confidence_threshold (int, optional): A threshold to be used during extraction. Any
                extraction with a confidence below this is discarded. Overrides the analogous
                property in `MultiTurnQAParser`, so you can set a global confidence threshold,
                as well as one for each field if desired.
            num_preceding_sentences (int, optional): The number of preceding sentences to include
                in the context when performing multi-turn question answering.
            num_following_sentences (int, optional): The number of sentences following the main
                sentence to include in the context when performing multi-turn question answering.
            include_heading (bool, optional): Whether to include the most recent heading in the
                context when performing multi-turn question answering.
            no_merge_range (int, optional): A range within which to not merge information on this
                field if a result was not found via multi-turn question answering.
        """
        super().__init__()
        self.question = question
        self.fields = fields
        self.confidence_threshold = confidence_threshold
        self.num_preceding_sentences = num_preceding_sentences
        self.num_following_sentences = num_following_sentences
        self.include_heading = include_heading
        self.no_merge_range = no_merge_range

    def formatted_question(self, record):
        """
        A formatted version of the question given the information currently in the records.
        This method will behave in undefined ways if given a record where the fields
        necessary to ask the question are not filled.
        """
        format_strings = []
        for field in self.fields:
            if isinstance(record[field], list):
                format_strings.append(record[field][0])
            elif isinstance(record[field], set):
                format_strings.append(list(record[field])[0])
            else:
                format_strings.append(record[field])
        return self.question.format(*format_strings)

    def can_ask_question(self, record):
        """
        Whether this question is a valid one to ask based on the record.
        This is based on whether the fields required to fill the templates are
        in the record or not.
        """
        for field in self.fields:
            try:
                if record[field]:
                    continue
            except KeyError:
                pass
            return False
        return True

    def postprocess_answer(self, answer):
        """
        Apply actions and conditions as with normal parse expressions.
        """
        if self.actions:
            for action in self.actions:
                answer = action(answer)
        if self.condition is not None:
            if not self.condition(answer):
                raise ValueError(
                    f"{answer} does not satisfy conditions for question {self.question}"
                )
        return answer


Q = Question


class _BatchQuestion:
    """
    Internal class used to facilitate multi-turn question answering in batches.
    Main use is to move from ChemDataExtractor `Question` objects to Huggingface
    transformers and back.
    """

    def __init__(self, record, sentence, question, field_name):
        self.record = record
        self.sentence = sentence
        self.question = question
        self.field_name = field_name

    @property
    def qa_input(self):
        if self.sentence.document is not None:
            sentence = self.sentence
            if isinstance(sentence, Subsentence):
                sentence = sentence.parent_sentence
            context_sentences = []
            if self.question.num_preceding_sentences:
                context_sentences = sentence.document.preceding_sentences(
                    sentence,
                    self.question.num_preceding_sentences,
                )
            context_sentences += [sentence]
            if self.question.num_following_sentences:
                context_sentences = sentence.document.following_sentences(
                    sentence,
                    self.question.num_following_sentences,
                )

            context = ""
            if self.question.include_heading:
                heading = sentence.document.heading_for_sentence(sentence)
                if heading is not None:
                    context += heading.text + "\n\n"
            context += " ".join(
                context_sentence.text for context_sentence in context_sentences
            )
        else:
            context = self.sentence.text
        return {
            "question": self.question.formatted_question(self.record),
            "context": context,
        }

    @classmethod
    def from_sentences_records_and_questions(
        cls,
        sentences,
        records,
        question_fields,
        asked_questions=None,
    ):
        if asked_questions is None:
            asked_questions = [{}] * len(sentences)

        batch_questions = []
        for sentence, sentence_records, asked_questions_for_sentence in zip(
            sentences, records, asked_questions
        ):
            eligible_questions_for_sentence = cls._eligible_questions(
                question_fields,
                sentence_records,
                asked_questions_for_sentence,
                sentence,
            )
            batch_questions.extend(eligible_questions_for_sentence)
        return batch_questions

    @classmethod
    def _eligible_questions(cls, question_fields, records, asked_questions, sentence):
        if not records:
            return cls._eligible_questions_for_empty_records(question_fields, sentence)
        batch_questions_list = []
        for record in records:
            for field_name, question in question_fields.items():
                if (
                    not record[field_name]
                    and question.can_ask_question(record)
                    and (
                        id(record) not in asked_questions
                        or question.formatted_question(record)
                        not in asked_questions[id(record)]
                    )
                ):
                    batch_questions_list.append(
                        cls(record, sentence, question, field_name)
                    )
                    if id(record) in asked_questions:
                        asked_questions[id(record)].append(
                            question.formatted_question(record)
                        )
                    else:
                        asked_questions[id(record)] = [
                            question.formatted_question(record)
                        ]
        return batch_questions_list

    @classmethod
    def _eligible_questions_for_empty_records(cls, question_fields, sentence):
        return [
            cls(None, sentence, question, field_name)
            for field_name, question in question_fields.items()
            if not question.fields
        ]


class MultiTurnQAParser(AutoSentenceParser):
    """
    An implementation of multi-turn question answering in ChemDataExtractor.
    Allows for the questions defined in `Question` objects to be used within
    the regular extraction pipeline.
    """

    def __init__(
        self,
        model_name=None,
        model=None,
        confidence_threshold=0.1,
        device=None,
        batch_size=16,
        handle_impossible_answer=True,
        manual_parser=None,
        max_iters=5,
        enable_single_sentence=True,
        skip_phrase=None,
        skip_section_phrase=None,
        allow_section_phrase=None,
        **kwargs,
    ):
        """
        .. warning::
            When batch parsing, `skip_phrase`, `skip_section_phrase`, and `allow_section_phrase`
            do not take effect.

        .. warning::
            This parser only supports the extraction of numerical properties. If you want to change
            this, look at how numerical_value_expression is used.

        Args:
            model_name (None, optional): The name of the huggingface model to be used.
                This should be an extractive question answering model, and either this or
                `model` should be provided when creating this object.
            model (None, optional): A huggingface question answering pipeline to be used.
            confidence_threshold (float, optional): A confidence threshold, below which
                any answers from multi-turn question answering will be treated as if the model had
                considered the question unanswerable
            device (None, optional): The pytorch device to run the model on. If this is not provided,
                CDE will automatically try and run the model on a GPU if available.
            batch_size (int, optional): The batch size to be used during parsing
            handle_impossible_answer (bool, optional): Whether the model was trained on SQuAD 2.0.
                This parameter is ignored if the `model` argument is provided.
            manual_parser (BaseSentenceParser, optional): The manual parser used to find any properties where
                rules were defined using parse expressions from earlier versions of CDE.
                Defaults to following the behaviour of the AutoSentenceParser in CDE.
            max_iters (int, optional): The number of iterations to ask questions for.
                This should be equal to or more than the number of follow-up questions possible
                in the series of questions defined in your model. This is here as a separate
                parameter for performance reasons.
            enable_single_sentence (bool, optional): Whether to allow parsing not in batches
            skip_phrase (BaseParseElement, optional): If this phrase is encountered during parsing,
                the sentence will be skipped. This does not work when batch parsing.
            skip_section_phrase (BaseParseElement, optional): If this phrase is encountered during
                parsing in the section header, the section will be skipped. This does not work when
                batch parsing.
            allow_section_phrase (BaseParseElement, optional): If this phrase is encountered during
                parsing in the section header, the section will be skipped. This does not work when
                batch parsing.
        """
        super().__init__(**kwargs)
        if model_name is None and model is None:
            raise ValueError("Either model_name or model must be defined!")
        self.model_name = model_name

        # Do not change this to not be an underscore - this is done to avoid conflicts
        # with the rest of CDE where model refers to a CDE model
        self._model = model

        self.confidence_threshold = confidence_threshold
        self.batch_size = batch_size
        if device is None and torch.cuda.is_available():
            self.device = torch.cuda.current_device()
        else:
            self.device = device
        self.numerical_value_expression = value_element()

        self.skip_phrase = skip_phrase
        self.skip_section_phrase = skip_section_phrase
        self.allow_section_phrase = allow_section_phrase
        self.handle_impossible_answer = handle_impossible_answer

        self.max_iters = max_iters
        self.manual_parser = manual_parser
        self.enable_single_sentence = enable_single_sentence

    @memoized_property
    def qa_model(self):
        """
        The Huggingface tokensiers extractive question answering model for this parser.
        """
        if self._model is not None:
            return self._model
        return pipeline(
            "question-answering",
            model=self.model_name,
            device=self.device,
            handle_impossible_answer=self.handle_impossible_answer,
        )

    def parse_sentence(self, sentence):
        if sentence.document is not None or not self.enable_single_sentence:
            return []
        batch_results = self.batch_parse_sentences([sentence])
        if id(sentence) in batch_results:
            return batch_results[id(sentence)]
        return []

    def batch_parse_sentences(self, sentences):
        # print("Batch parsing sentences", len(sentences))
        # Gather only sentences which are likely to contain valid records
        # by scanning them with the specifier value and also filtering
        # out those without numerical values.
        filtered_sentences = []
        for sentence in sentences:
            if self._is_valid_sentence(sentence):
                filtered_sentences.append(sentence)

        if not len(filtered_sentences):
            return {}

        # Do manual parsing for e.g. specifiers
        records = [self._do_manual_parsing(sentence) for sentence in filtered_sentences]

        # Identify which fields have questions associated with them
        question_fields = {}
        for field_name, field in self.model.fields.items():
            if isinstance(field.parse_expression, Question):
                question_fields[field_name] = field.parse_expression

        # Ask questions
        asked_questions = [{}] * len(filtered_sentences)
        for i in range(self.max_iters):
            # Gather all askable questions
            batch_questions = _BatchQuestion.from_sentences_records_and_questions(
                filtered_sentences, records, question_fields, asked_questions
            )
            qa_inputs = [batch_question.qa_input for batch_question in batch_questions]

            if not len(qa_inputs):
                break

            # Get answers from ML model

            batch_size = 1
            if self.batch_size is not None:
                batch_size = self.batch_size
            answers = self.qa_model(qa_inputs, top_k=1, batch_size=batch_size)
            if len(qa_inputs) == 1:
                answers = [answers]

            # print(qa_inputs, answers)

            # Update the records
            for index, answer in enumerate(answers):
                # confidence = 1. - answer["score"] if self.squad_v2_format else answer["score"]
                confidence = answer["score"]
                batch_question = batch_questions[index]
                question = batch_question.question

                try:
                    answer["answer"] = question.postprocess_answer(answer["answer"])
                except ValueError as e:
                    answer = None

                if (
                    answer is not None
                    and (
                        (
                            question.confidence_threshold is not None
                            and confidence > question.confidence_threshold
                        )
                        or (
                            question.confidence_threshold is None
                            and confidence > self.confidence_threshold
                        )
                    )
                    and answer["answer"] != ""
                ):
                    record = batch_question.record
                    field_name = batch_question.field_name
                    if question.name:
                        field_name += question.name

                    if record is None:
                        record = self.model()
                        batch_question.record = record

                    if "names" in field_name:
                        record[field_name] = [answer["answer"].strip().strip(",.")]
                    else:
                        record[field_name] = answer["answer"].strip().strip(",.")
                    record.set_confidence(field_name, confidence)
                elif batch_question.record is not None:
                    record = batch_question.record
                    no_merge_sentence_count = max(
                        batch_question.question.num_preceding_sentences,
                        batch_question.question.num_following_sentences,
                        batch_question.question.no_merge_range,
                    )
                    record._no_merge_ranges[batch_question.field_name] = (
                        no_merge_sentence_count * SentenceRange()
                    )

            # Update the records list
            new_records_list = [[] for i in range(len(filtered_sentences))]
            for batch_question in batch_questions:
                if batch_question.record is not None:
                    index = filtered_sentences.index(batch_question.sentence)
                    new_records_list[index].append(batch_question.record)
            # Another loop iterating through current records and checking if that is in
            # the new records list, if not, appending it to the list
            for old_sentence_records, new_sentence_records in zip(
                records, new_records_list
            ):
                for record in old_sentence_records:
                    if record not in new_sentence_records:
                        new_sentence_records.append(record)
            records = new_records_list

        records_dict = {
            id(sentence): sentence_records
            for sentence, sentence_records in zip(filtered_sentences, records)
        }
        return records_dict

    def _is_valid_sentence(self, sentence):
        if len(
            [
                result
                for result in self.model.specifier.parse_expression.scan(
                    sentence.tokens
                )
            ]
        ) and len(
            [result for result in self.numerical_value_expression.scan(sentence.tokens)]
        ):
            return True
        return False

    def _do_manual_parsing(self, sentence):
        self.chem_name = NoMatch()
        if self.manual_parser is None:
            self.lenient = False
            results = []
            for result in self.root.scan(sentence.tokens):
                # print(etree.tostring(result[0]))
                for model in self.interpret(*result):
                    results.append(model)
            return results
        else:
            # TODO(ti250): Ensure that we do all the subsentence smarts here if needed
            # print(f"{self.manual_parser} manual parser called")
            self.manual_parser.model = self.model
            records = list(self.manual_parser.parse_sentence(sentence))
            return records

    # TODO(ti250): this is essentially a duplicate from CDE auto parser - try and remove this and use the same stuff
    def interpret(self, results, start, end):
        if results is None:
            return

        if not isinstance(results, list):
            results = [results]

        for result in results:
            property_entities = {}

            for field_name, field in self.model.fields.items():
                try:
                    data = self._get_data(field_name, field, result)
                    if data is not None:
                        property_entities.update(data)
                # if field is required, but empty, the requirements have not been met
                except TypeError:
                    pass

            model_instance = None
            if property_entities.keys():
                model_instance = self.model(**property_entities)

            yield model_instance

    # TODO(ti250): this is essentially a duplicate from CDE auto parser - try and remove this and use the same stuff
    @property
    def root(self):
        entities = []

        if hasattr(self.model, "specifier") and self.model.specifier:
            # now we are parsing an element that has no value but some custom string
            # therefore, there will be no matching interpret function, all entities are custom except for the specifier
            specifier = self.model.specifier.parse_expression("specifier")
            entities.append(specifier)

        # the optional, user-defined, entities of the model are added, they are tagged with the name of the field
        for field in self.model.fields:
            if field not in [
                "raw_value",
                "raw_units",
                "value",
                "units",
                "error",
                "specifier",
            ]:
                try:
                    if (
                        self.model.__getattribute__(self.model, field).parse_expression
                        is not None
                    ):
                        entities.append(
                            self.model.__getattribute__(
                                self.model, field
                            ).parse_expression(field)
                        )
                except AttributeError:
                    pass

        # logic for finding all the elements in any order
        combined_entities = _create_entities_list(entities)
        root_phrase = OneOrMore(
            combined_entities + Optional(SkipTo(combined_entities))
        )("root_phrase")
        return root_phrase


# TODO(ti250): this is essentially a duplicate from CDE auto parser - try and remove this and use the same stuff
def _create_entities_list(entities):
    """
    For a list of Base parser entities, creates an entity of structure. For example, with 4 entities in the list, the output is::

        (entities[0] | entities[1] | entities[2] | entities[3])

    :param entities: BaseParserElement type objects
    :return: BaseParserElement type object
    """
    result = entities[0]
    for entity in entities[1:]:
        result = result | entity
    return result
