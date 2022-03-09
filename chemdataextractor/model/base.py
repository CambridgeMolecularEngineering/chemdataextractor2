# -*- coding: utf-8 -*-
"""
Data model for extracted information.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
from abc import ABCMeta
from collections import MutableSequence
import json
import logging
from pprint import pprint

import six

from ..utils import python_2_unicode_compatible
from ..parse.elements import Any, W, I
from ..parse.auto import AutoSentenceParser, AutoTableParser

log = logging.getLogger(__name__)


class BaseType(six.with_metaclass(ABCMeta)):

    # This is assigned by ModelMeta to match the attribute on the Model
    name = None

    def __init__(self, default=None, null=False, required=False, contextual=False, parse_expression=None, updatable=False, binding=False, ignore_when_merging=False):
        """

        :param default: (Optional) The default value for this field if none is set.
        :param bool null: (Optional) Include in serialized output even if value is None. Default False.
        :param bool required: (Optional) Whether a value is required. Default False.
        :param bool contextual: (Optional) Whether this value is contextual. Default False.
        :param BaseParserElement parse_expression: (Optional) Expression for parsing, instance of a subclass of BaseParserElement. Default None.
        :param bool updatable: (Optional) Whether the parse_expression can be changed by the document as parsing occurs. Default False.
        :param bool binding: (Optional) If this option is set to True, any submodels that have an attribute with the same name must have the same value for this attribute. Default False/
        :param bool ignore_when_merging: (Optional) If this option is set to True, any records with a different value for this field is treated as corresponding to the same physical record.
        """
        self.default = copy.deepcopy(default)
        self.null = null
        self.required = required
        self.contextual = contextual
        self.parse_expression = parse_expression
        self.updatable = updatable
        self.binding = binding
        self.ignore_when_merging = ignore_when_merging
        if self.parse_expression is None and self.updatable:
            print('No parse_expression supplied but updatable set as True for ', type(self))
            print('updatable refers to whether parse_expression can be changed by the document as parsing occurs. Setting updatable to False.')
            self.updatable = False
        self.parse_expression = copy.copy(parse_expression)
        self._default_parse_expression = parse_expression
        # when a record is created from the table, this will be filled with the row/col header cateogry strings
        # which helps merging based on same row/column category
        self.table_row_categories = None
        self.table_col_categories = None

    def reset(self):
        """
        Reset the parse expression to the initial value.
        """
        if self.updatable:
            self.parse_expression = copy.copy(self._default_parse_expression)

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field in a Model."""
        # Check if Model class is being called, rather than Model instance
        if instance is None:
            return self
        # Get value from Model instance if available
        value = instance._values.get(self.name)
        # If value is None or empty string then return the default value, if set
        # if value in [None, ''] and self.default is not None:
        #     return self.default
        return value

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a Model."""
        instance._values[self.name] = self.process(value)

    def process(self, value):
        """Convert an assigned value into the desired data format for this field."""
        return value

    def serialize(self, value, primitive=False):
        """Serialize this field."""
        if hasattr(value, 'serialize'):
            # i.e. value is a nested model
            return value.serialize(primitive=primitive)
        else:
            return value

    def is_empty(self, value):
        """Return whether a value is considered empty for the case of this field."""
        return False


class StringType(BaseType):
    """"""

    def process(self, value):
        """Convert value to a unicode string. Useful in case lxml _ElementUnicodeResult are passed from parser."""
        return six.text_type(value) if value is not None else None

    def is_empty(self, value):
        if value is not None and isinstance(value, str) and value:
            return False
        return True


class FloatType(BaseType):
    """An floating point number field."""

    def process(self, value):
        """Convert value to a float."""
        if value is not None:
            return float(value)
        return None

    def is_empty(self, value):
        if value is not None:
            return False
        return True


class ModelType(BaseType):

    def __init__(self, model, **kwargs):
        self.model_class = model
        self.model_name = self.model_class.__name__
        super(ModelType, self).__init__(**kwargs)

    def process(self, value):
        if isinstance(value, self.model_class):
            return value
        else:
            return None

    def serialize(self, value, primitive=False):
        """Serialize this field."""
        return value.serialize(primitive=primitive)

    def is_empty(self, value):
        if isinstance(value, self.model_class):
            return value.is_empty
        return True


class ListType(BaseType):

    def __init__(self, field, default=None, sorted_=False, **kwargs):
        super(ListType, self).__init__(**kwargs)
        self.field = field
        self.default = default if default is not None else []
        self.sorted = sorted_

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a ListField in a Model."""
        # Run process for the nested field type for each value in list
        if value is None:
            instance._values[self.name] = None
        else:
            processed = [self.field.process(v) for v in value]
            if self.sorted:
                processed = sorted(processed)
            instance._values[self.name] = processed

    def serialize(self, value, primitive=False):
        """Serialize this field."""
        if value:
            return [self.field.serialize(v, primitive=primitive) for v in value]
        else:
            return None

    def is_empty(self, value):
        if isinstance(value, list) and len(value) != 0:
            return False
        return True


class InferredProperty(BaseType):
    """
    A property that is inferred from the value of another property via an inferrer function.
    An example is the processing the raw value extracted from a document into a list of floats,
    which can be seen in :class:`~chemdataextractor.model.units.quantity_model.QuantityModel`, where
    :attr:`~chemdataextractor.model.units.quantity_model.QuantityModel.value` is inferred from
    :attr:`~chemdataextractor.model.units.quantity_model.QuantityModel.raw_value`.
    """

    def __init__(self, field, origin_field, inferrer, **kwargs):
        """
        :param BaseType field: The type expected as a result of inference.
        :param str origin_field: The name of the field from which to infer the value. This can be a keypath, as detailed in
            :class:`~chemdataextractor.model.base.BaseModel`
        :param function inferrer: The function which is used to infer the value of the field.
            The function should have a signature of
            (*object* value of the origin field, *BaseModel* the instance for which the value is being inferred)
            -> *object* the value that the inferred field should have
        :param default: (Optional) The default value for this field if none is set.
        :param bool null: (Optional) Include in serialized output even if value is None. Default False.
        :param bool required: (Optional) Whether a value is required. Default False.
        :param bool contextual: (Optional) Whether this value is contextual. Default False.
        :param BaseParserElement parse_expression: (Optional) Expression for parsing, instance of a subclass of BaseParserElement. Default None.
        :param bool updatable: (Optional) Whether the parse_expression can be changed by the document as parsing occurs. Default False
        :param bool binding: (Optional) If this option is set to True, any submodels that have an attribute with the same name must have the same value for this attribute
        """
        self.field = field
        self.origin_field = origin_field
        self.inferrer = inferrer
        super(InferredProperty, self).__init__(**kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._values.get(self.name)
        if value is not None and value != self.default:
            return value

        value = self.inferrer(instance[self.origin_field],
                              instance)
        self.__set__(instance, value)
        if value is None:
            value = self.default
        return value

    def process(self, value):
        return self.field.process(value)

    def serialize(self, value, primitive=False):
        return self.field.serialize(value)

    def is_empty(self, value):
        if isinstance(value, list) and len(value) != 0:
            return False
        return True


class SetType(BaseType):

    def __init__(self, field, default=None, **kwargs):
        super(SetType, self).__init__(**kwargs)
        self.field = field
        self.default = default if default is not None else set()

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a SetField in a Model."""
        # Run process for the nested field type for each value in list
        if value is None:
            instance._values[self.name] = None
        else:
            instance._values[self.name] = set(self.field.process(v) for v in value)

    def serialize(self, value, primitive=False):
        """Serialize this field."""
        if value is None or len(value) == 0:
            return None
        # a list, instead of a set is needed for easy compatibility with JSON output formats
        # a new sorted list instance ensures the same order for different runs
        # sorting in place results in an empty list in this case
        rec_list = list(self.field.serialize(v, primitive=primitive) for v in value)
        return sorted(rec_list)

    def is_empty(self, value):
        if isinstance(value, set) and len(value) != 0:
            return False
        return True


class ModelMeta(ABCMeta):
    """"""

    def __new__(mcs, name, bases, attrs):
        cls = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        fields = {}
        for field_name, field in six.iteritems(cls.fields):
            fields[field_name] = copy.copy(field)
        for attr_name, attr_value in six.iteritems(attrs):
            if isinstance(attr_value, BaseType):
                # Set the name attribute on the Type to the attribute name on the Model
                attr_value.name = six.text_type(attr_name)
                fields[attr_name] = attr_value
        cls.fields = fields
        parsers = []
        for parser in cls.parsers:
            p = copy.copy(parser)
            p.model = cls
            parsers.append(p)
        cls.parsers = parsers
        return cls

    def __setattr__(cls, key, value):
        if isinstance(value, BaseType):
            value.name = six.text_type(key)
            cls.fields[key] = value
        return super(ModelMeta, cls).__setattr__(key, value)

    @property
    def required_fields(cls):
        output = []
        for key, field in cls.fields.items():
            if hasattr(field, 'model_class'):
                nest_req_fields = field.model_class.required_fields
                for nrf in nest_req_fields:
                    output.append(key + '__' + nrf)
            else:
                if field.required:
                    output.append(key)
        return output


@python_2_unicode_compatible
class BaseModel(six.with_metaclass(ModelMeta)):
    """
    A base class for representing a model within ChemDataExtractor.
    Each model can have a number of fields that are declared with the class::

        class ExampleModel(BaseModel):
            string_field = StringType()
            number_field = FloatType()

    See the documentation for :class:`~chemdataextractor.model.base.BaseType` for
    more information. These fields are required for ChemDataExtractor to correctly
    identify what to extract and for merging different records for the same model.

    The attributes in the models can then be accessed via either dot notation::

        example_record.string_field

    or dictionary notation::

        example_record["string_field"]

    You can have nexted models, as in the example below, where a
    new class, ``ExampleModel2`` can contain an ``ExampleModel``::

        class ExampleModel2(BaseModel):
            model_field = ModelType(ExampleModel)

    keypath notation can be used to find the nested properties::

        example_record2["model_field.string_field"]
    """

    fields = {}
    parsers = [AutoSentenceParser(), AutoTableParser()]
    specifier = None
    _updated = False

    def __init__(self, **raw_data):
        """"""
        self._values = {}
        for key, value in six.iteritems(raw_data):
            setattr(self, key, value)
        # Set defaults
        for key, field in six.iteritems(self.fields):
            if key not in raw_data:
                setattr(self, key, copy.copy(field.default))
        self._record_method = None
        self.was_updated = self._updated

    @property
    def is_unidentified(self):
        """
        If there is no 'compound' field associated with the model but the compound is contextual
        """
        try:
            if 'compound' not in self.fields.keys():
                return False
            if not self.compound.contextual_fulfilled:
                return self.compound.is_unidentified
        except AttributeError:
            return True

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__,)

    def __str__(self):
        return '<%s>' % (self.__class__.__name__,)

    def __eq__(self, other):
        # TODO: Check this actually works as expected (what about default values?)
        if isinstance(other, self.__class__):
            log.debug(self._values, other._values)
            return self._values == other._values
        return False

    def __iter__(self):
        return iter(self.fields)

    def __delattr__(self, attr):
        """Handle deletion of field values by setting to default if specified."""
        # Set to default value
        if attr in self.fields:
            setattr(self, attr, self.fields[attr].default)
        else:
            super(BaseModel, self).__delattr__(attr)

    def __getitem__(self, key):
        """Redirect dictionary-style field access to attribute-style."""
        return self._get_item(key)

    def _get_item(self, key, create_defaults=False):
        """
        A recursive way to items given a key, which can either be a simple property name for a top
        level property (e.g. `names` for a compound), or a keypath to be able to drill down
        a record (e.g. `compound.names`) for a property.
        """
        try:
            if not isinstance(key, list):
                key = self._get_keypath(key)
            if key[0] in self.fields:
                attribute = getattr(self, key[0])

                if ((attribute is None
                    or (attribute == [] and len(key) != 1))
                    and create_defaults):
                    field = self.fields[key[0]]
                    is_list = False
                    while hasattr(field, 'field'):
                        if isinstance(field, ListType):
                            is_list = True
                        field = field.field

                    if isinstance(field, ModelType):
                        created_attr = field.model_class()
                    else:
                        created_attr = field('')
                    if is_list:
                        created_attr = [created_attr]
                    attribute = created_attr
                    self[key[0]] = created_attr

                if len(key) == 1:
                    return attribute
                else:
                    if isinstance(attribute, list):
                        attribute = attribute[0]
                    return attribute[key[1:]]
        except AttributeError as e:
            pass
        raise KeyError(key)

    def __setitem__(self, key, value):
        """Redirect dictionary-style field setting to attribute-style."""
        if not isinstance(key, list):
            key = self._get_keypath(key)
        if key[0] not in self.fields:
            raise KeyError(key)
        target = self
        if len(key) > 1:
            target = self._get_item(key[:-1], create_defaults=True)
            if isinstance(target, list):
                if len(target) == 0:
                    self._get_item(key, create_defaults=True)
                    target = self._get_item(key[:-1], create_defaults=True)[0]
                else:
                    target = target[0]
        return setattr(target, key[-1], value)

    def __contains__(self, name):
        try:
            val = getattr(self, name)
            return val is not None
        except AttributeError:
            return False

    def __hash__(self):
        return str(self.serialize()).__hash__()

    def _get_keypath(self, string):
        return string.split(".")

    @classmethod
    def reset_updatables(cls):
        """
        Reset all updatable parse_expressions of properties associated with the class.
        """
        for key, field in six.iteritems(cls.fields):
            if cls.fields[key].updatable:
                cls.fields[key].reset()
                cls._updated = False

    @classmethod
    def update(cls, definitions, strict=True):
        """Update this Element's updatable attributes with new information from definitions

        Arguments:
            definitions {list} -- list of definitions found in this element
        """
        log.debug("Updating model")
        for definition in definitions:
            for field in cls.fields:
                if cls.fields[field].updatable:
                    matches = [i for i in cls.fields[field].parse_expression.scan(definition['tokens'])]
                    # print(matches)
                    if any(matches):
                        cls._updated = True
                        if strict:
                            cls.fields[field].parse_expression = cls.fields[field].parse_expression | W(str(definition['specifier']))
                        else:
                            cls.fields[field].parse_expression = cls.fields[field].parse_expression | I(str(definition['specifier']))
        return

    @property
    def updated(self):
        """
        True/False dependent on if a specifier within the model was updated.
        """
        for field_name, field in six.iteritems(self.fields):
            if hasattr(field, 'model_class'):
                if hasattr(self[field_name], 'updated') and self[field_name].was_updated:
                    return True
        return self.was_updated

    def keys(self):
        return list(iter(self))

    def items(self):
        return [(k, getattr(self, k)) for k in self]

    def values(self):
        return [getattr(self, k) for k in self]

    def get(self, key, default=None):
        return getattr(self, key, default)

    @property
    def contextual_fulfilled(self):
        """
        Whether all the contextual fields have been extracted.

        :return: True if all fields have been found, False if not.
        :rtype: bool
        """

        for field_name, field in six.iteritems(self.fields):
            if hasattr(field, 'model_class'):
                if self[field_name] == field.default and field.contextual:
                    return False
                if hasattr(self[field_name], 'contextual_fulfilled') and \
                   not self[field_name].contextual_fulfilled:
                    log.debug('Is contextual')
                    return False
            elif field.contextual and self[field_name] == field.default:
                log.debug('Is contextual')
                return False
        log.debug('Not contextual')
        return True

    @property
    def required_fulfilled(self):
        """
        Whether all the required fields have been extracted.

        :return: True if all fields have been found, False if not.
        :rtype: bool
        """
        return self._required_fulfilled(strict=True)

    @property
    def noncontextual_required_fulfilled(self):
        """
        Whether all the non-contextual required fields have been extracted.

        :return: True if all fields have been found, False if not.
        :rtype: bool
        """
        return self._required_fulfilled(strict=False)

    def _required_fulfilled(self, strict):
        for field_name, field in six.iteritems(self.fields):
            if hasattr(field, 'model_class'):
                if self[field_name] == field.default \
                   and field.required:

                    if not strict and field.contextual:
                        pass
                    else:
                        return False
                if field.required and hasattr(self[field_name], 'required_fulfilled') and \
                   not self[field_name].required_fulfilled:

                    if not strict and field.contextual:
                        pass
                    else:
                        log.debug('Required unfulfilled')
                        return False
            elif field.required and self[field_name] == field.default:
                # print(self.serialize(), field_name, "did not exist")
                if not strict and field.contextual:
                    pass
                else:
                    return False
        return True

    def serialize(self, primitive=False):
        """Convert Model to python dictionary."""
        # Serialize fields to a dict
        data = {}
        for field_name in self:
            value = getattr(self, field_name)
            field = self.fields.get(field_name)
            if value is not None:
                value = field.serialize(value, primitive=primitive)
            # Skip empty fields unless field.null
            if not field.null and value in [None, '', []]:
                continue
            data[field.name] = value
        record = {self.__class__.__name__: data}
        return record

    def to_json(self, *args, **kwargs):
        """Convert Model to JSON."""
        return json.dumps(self.serialize(primitive=True), *args, **kwargs)

    def is_superset(self, other):
        """
        Whether this model instance is a 'superset' of the other model instance.

        A model instance is a 'superset' of another if it satisfies the following conditions:

        - The model instances are of the same type

        - For each of the attributes of the model instances, either:

            - This instance has more information, or

            - Both instances have the same information

        :param other: The other model instance to compare with this model instance
        :type other: BaseModel
        :return: Whether this model instance is a superset of the other model instance
        :rtype: bool
        """
        if type(self) != type(other):
            return False
        for field_name, field in six.iteritems(self.fields):
            # Method works recursively so it works with nested models
            if hasattr(field, 'model_class'):
                if not self[field_name]:
                    if other[field_name]:
                        return False
                elif not other[field_name]:
                    pass
                elif not self[field_name].is_superset(other[field_name]):
                    return False
            else:
                if other[field_name] and self[field_name] != other[field_name]:
                    return False
        return True

    def is_subset(self, other):
        """
        Whether this model instance is a 'subset' of the other model instance.

        A model instance is a 'subset' of another if it satisfies the following conditions:

        - The model instances are of the same type

        - For each of the attributes of the model instances, either:

            - The other instance has more information, or

            - Both instances have the same information

        :param other: The other model instance to compare with this model instance
        :type other: BaseModel
        :return: Whether this model instance is a subset of the other model instance
        :rtype: bool
        """
        return other.is_superset(self)

    def merge_contextual(self, other):
        """
        Merges any fields marked contextual with additional information from other provided that:

        - other is of the same type and they don't have any conflicting fields

        or

        - other is a model type that is part of this model and that field is currently set to be the default value or the field can be merged with the other.

        .. note::

            This method mutates the model it's called on **and** returns it.

        :param other: The other model to merge into this model
        :type other: BaseModel
        :return: A merged model
        :rtype: BaseModel
        """

        log.debug(self.serialize())
        log.debug(other.serialize())
        did_merge = False
        should_keep_both_records = self._should_keep_both_records(other)
        if self.contextual_fulfilled:
            return self
        if self._binding_compatible(other):
            _compatible = False
            if type(self) == type(other) and self._compatible(other):
                _compatible = True
            if type(self) != type(other):
                for field_name, field in six.iteritems(self.fields):
                    if hasattr(field, 'model_class') and isinstance(other, field.model_class):
                        # print('model class case activated')
                        log.debug('model class case')
                        if self[field_name] is not None and field.contextual and not self[field_name].contextual_fulfilled:
                            if self[field_name].merge_contextual(other):
                                did_merge = True
                        elif (field.contextual and not self[field_name]
                              and other):
                            log.debug(field_name)
                            self[field_name] = copy.copy(other)
                            did_merge = True
            elif self._compatible(other):
                for field_name, field in six.iteritems(self.fields):
                    if (field.contextual
                       and not self[field_name]
                       and other.get(field_name, None)):
                        self[field_name] = other[field_name]
                        did_merge = True
        self._consolidate_binding()
        if did_merge:
            if should_keep_both_records:
                did_merge = False
        return did_merge

    def merge_all(self, other):
        """
        Merges any properties between other and self, regardless of whether that field is contextual.
        Checks to make sure that there are no conflicts between the values contained in self and those in other.

        .. note::

            This method mutates the model it's called on **and** returns it.

        :param other: The other model to merge into this model
        :type other: BaseModel
        :return: A merged model
        :rtype: BaseModel
        """

        log.debug(self.serialize())
        log.debug(other.serialize())
        did_merge = False
        should_keep_both_records = self._should_keep_both_records(other)
        if self._binding_compatible(other):
            if type(self) != type(other):
                for field_name, field in six.iteritems(self.fields):
                    if hasattr(field, 'model_class') and isinstance(other, field.model_class):
                        log.debug('model class case')
                        if self[field_name]:
                            if self[field_name].merge_all(other):
                                did_merge = True
                        elif (not self[field_name]
                              and other):
                            log.debug(field_name)
                            self[field_name] = copy.copy(other)
                            did_merge = True
            elif self._compatible(other):
                for field_name, field in six.iteritems(self.fields):
                    if (not self[field_name]
                      and other.get(field_name, None)):
                        did_merge = True
                        self[field_name] = other[field_name]
        self._consolidate_binding()
        if did_merge:
            if should_keep_both_records:
                did_merge = False
        return did_merge

    def _compatible(self, other):
        """
        Checks whether two records seem to be compatible for the purposes of merging.
        This means no conflicting fields, unless `ignore_when_merging` is set.
        """
        match = False
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            match = True
            for field_name, field in six.iteritems(self.fields):
                if isinstance(field, ModelType):
                    if (not field.ignore_when_merging
                    and self[field_name] is not None
                    and other[field_name] is not None
                    and not self[field_name]._compatible(other[field_name])):
                        match = False
                        break
                elif isinstance(field, ListType):
                    if (not field.ignore_when_merging
                      and self[field_name] is not None and self[field_name] != []
                      and other[field_name] is not None and other[field_name] != []
                      and self[field_name] != other[field_name]):
                        match = False
                        break
                else:
                    if (not field.ignore_when_merging
                      and self[field_name] is not None
                      and other[field_name] is not None
                      and self[field_name] != other[field_name]):
                        match = False
                        break
        return match

    def _compatible_legacy(self, other):
        match = False
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            match = True
            for field_name, field in six.iteritems(self.fields):
                if (not field.ignore_when_merging
                  and self[field_name] is not None
                  and other[field_name] is not None
                  and self[field_name] != other[field_name]):
                    match = False
                    break
        return match

    def _should_keep_both_records(self, other):
        should_keep_both = False
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            for field_name, field in six.iteritems(self.fields):
                if isinstance(field, ModelType):
                    if (field.ignore_when_merging
                    and self[field_name] is not None
                    and other[field_name] is not None
                    and not self[field_name]._compatible(other[field_name])):
                        should_keep_both = True
                        break
                else:
                    if (field.ignore_when_merging
                      and self[field_name] is not None
                      and other[field_name] is not None
                      and self[field_name] != other[field_name]):
                        should_keep_both = True
                        break
        return should_keep_both

    @classmethod
    def flatten(cls, include_inferred=True):
        """
        A set of all models that are associated with this model.
        For example, if we have a model like the following with multiple submodels:

        .. code-block:: python

            class A(BaseModel):
                pass

            class B(BaseModel):
                a = ModelType(A)

            class C(BaseModel):
                b = ModelType(B)

        then `C.flatten()` would give the result::

            set(C, B, A)

        :return: The set of all models associated with this model.
        :rtype: set(BaseModel)
        """
        model_set = {cls}
        for field_name, field in six.iteritems(cls.fields):
            while hasattr(field, 'field') and not isinstance(field, InferredProperty):
                if hasattr(field, 'model_class'):
                    model_set.update(field.model_class.flatten(include_inferred=include_inferred))
                field = field.field
            if hasattr(field, 'model_class'):
                model_set.update(field.model_class.flatten(include_inferred=include_inferred))
        log.debug(model_set)
        return model_set

    @property
    def binding_properties(self):
        """
        A dictionary of all binding properties in this model, and their values.

        .. note::

            This function only returns those properties that are immediately binding for this
            model, and not for any submodels.

        :returns: A dictionary with the names of all binding fields as the keys and their values as the values.
        :rtype: {str: Any}
        """
        binding_properties = {}
        for field_name, field in six.iteritems(self.fields):
            if field.binding and self[field_name]:
                binding_properties[field_name] = self[field_name]
        return binding_properties

    def _binding_compatible(self, other, binding_properties=None):
        """
        Whether two models are compatible in terms of their binding properties.
        For example, if this model had a compound associated with it and the field was binding,
        a model that is associated with another compound will not be merged in.

        :param BaseModel other: The other model that will be checked for compatibility with the binding properties in this model
        :param {str: Any} binding_properties: Any binding properties from a model that contains this model
        :returns: Whether the two models are compatible in terms of their binding properties.
        :rtype: bool
        """
        if binding_properties is None:
            binding_properties = self.binding_properties
        if not binding_properties:
            return True

        if type(other) == type(self):
            for field_name, field in six.iteritems(binding_properties):
                if other[field_name] != binding_properties[field_name]:
                    return False
        elif not other:
            pass
        else:
            for field_name, field in six.iteritems(other.fields):
                if field_name in binding_properties.keys():
                    if other[field_name]:
                        if not (binding_properties[field_name].is_superset(other[field_name]) or
                                binding_properties[field_name].is_subset(other[field_name])):
                            return False
                elif hasattr(field, 'model_class'):
                    if not self._binding_compatible(other[field_name]):
                        return False
        return True

    def _consolidate_binding(self, binding_properties=None):
        if binding_properties is None:
            binding_properties = self.binding_properties
        if binding_properties == {}:
            return
        for field_name, field in six.iteritems(self.fields):
            if field_name in binding_properties.keys():
                self[field_name] = binding_properties[field_name]
            elif hasattr(field, 'model_class') and self[field_name]:
                self[field_name]._consolidate_binding(binding_properties)


    @property
    def record_method(self):
        """
        Description (string) of which method was used to create this record.
        """
        return self._record_method

    @record_method.setter
    def record_method(self, text):
        if not isinstance(text, str):
            raise TypeError("Record method description is not string.")
        self._record_method = text

    def _clean(self):
        """
        Removes any subrecords where the required properties have not been fulfilled.
        """
        for field_name, field in six.iteritems(self.fields):
            if hasattr(field, 'model_class') and self[field_name]:
                self[field_name]._clean()
                if not self[field_name].required_fulfilled:
                    self[field_name] = field.default

    @classmethod
    def _all_keypaths(cls):
        all_keypaths = []
        for field_name, field in six.iteritems(cls.fields):
            while hasattr(field, 'field'):
                field = field.field
            if hasattr(field, 'model_class'):
                sub_keypaths = field.model_class._all_keypaths()
                for keypath in sub_keypaths:
                    all_keypaths.append(field_name + '.' + keypath)
            else:
                all_keypaths.append(field_name)
        return all_keypaths

    @property
    def is_empty(self):
        for field_name, field_type in six.iteritems(self.fields):
            if not field_type.is_empty(self[field_name]):
                return False
        return True



@python_2_unicode_compatible
class ModelList(MutableSequence):
    """Wrapper around a list of Models objects to facilitate operations on all at once."""

    def __init__(self, *models):
        self.models = list(models)

    def __getitem__(self, index):
        return self.models[index]

    def __setitem__(self, index, value):
        self.models[index] = value

    def __delitem__(self, index):
        del self.models[index]

    def __len__(self):
        return len(self.models)

    def __repr__(self):
        return self.models.__repr__()

    def __str__(self):
        return self.models.__str__()

    def __contains__(self, element):
        log.debug(element.serialize())
        log.debug(self.serialize())
        log.debug(self.models.__contains__(element))
        return self.models.__contains__(element)

    def insert(self, index, value):
        self.models.insert(index, value)

    def serialize(self):
        """Serialize to a list of python dictionaries."""
        return [e.serialize() for e in self.models]

    def to_json(self, *args, **kwargs):
        """Convert ModelList to JSON."""
        return json.dumps(self.serialize(), *args, **kwargs)

    def remove_subsets(self, strict=False):
        """
        Remove any subsets contained within the ModelList.

        :param bool strict: Default True. Whether only strict subsets are removed. When this is False, duplicates are removed too.
        """
        # A dictionary with the type of each element as the key, and the element itself as the value
        typed_list = {}
        for element in self.models:
            if type(element) in typed_list.keys():
                typed_list[type(element)].append(element)
            else:
                typed_list[type(element)] = [element]
        new_models = []
        for _, elements in six.iteritems(typed_list):
            i = 0
            length = len(elements)
            to_remove = []
            # Iterate through the list of elements and if any subsets are found, add the
            # indices to a list of values to remove
            while i < length:
                j = 0
                while j < length:
                    if i != j and elements[i].is_subset(elements[j]) and j not in to_remove:
                        if strict and elements[i] == elements[j]:
                            # Do not remove the element if it is not a strict subset depending on the value of strict
                            pass
                        else:
                            to_remove.append(i)
                    j += 1
                i += 1

            # Append any values that are not in the list of objects to remove
            i = 0
            while i < length:
                if i not in to_remove:
                    new_models.append(elements[i])
                i += 1
        self.models = new_models
