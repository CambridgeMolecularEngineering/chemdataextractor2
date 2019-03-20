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

import six

from ..utils import python_2_unicode_compatible
from ..parse.elements import Any, W

log = logging.getLogger(__name__)


class BaseType(six.with_metaclass(ABCMeta)):

    # This is assigned by ModelMeta to match the attribute on the Model
    name = None

    def __init__(self, default=None, null=False, required=False, contextual=False, parse_expression=None, mutable=False):
        """

        :param default: (Optional) The default value for this field if none is set.
        :param bool null: (Optional) Include in serialized output even if value is None. Default False.
        :param bool required: (Optional) Whether a value is required. Default False.
        :param bool contextual: (Optional) Whether this value is contextual. Default False.
        :param BaseParserElement parse_expression: (Optional) Expression for parsing, instance of a subclass of BaseParserElement. Default None.
        :param bool mutable: (Optional) Whether the parse_expression can be changed by the document as parsing occurs. Default False
        """
        self.default = copy.deepcopy(default)
        self.null = null
        self.required = required
        self.contextual = contextual
        self.parse_expression = parse_expression
        self.mutable = mutable
        if self.parse_expression is None and self.mutable:
            print('No parse_expression supplied but mutable set as True for ', type(self))
            print('mutable refers to whether parse_expression can be changed by the document as parsing occurs. Setting mutable to False.')
            self.mutable = False
        if mutable:
            self._default_parse_expression = copy.copy(parse_expression)

    def reset(self):
        """
        Reset the parse expression to the initial value.
        """
        if self.mutable:
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


class StringType(BaseType):
    """"""

    def process(self, value):
        """Convert value to a unicode string. Useful in case lxml _ElementUnicodeResult are passed from parser."""
        return six.text_type(value) if value is not None else None


class FloatType(BaseType):
    """An floating point number field."""

    def process(self, value):
        """Convert value to a float."""
        if value is not None:
            return float(value)

        return None


class ModelType(BaseType):

    def __init__(self, model, **kwargs):
        self.model_class = model
        self.model_name = self.model_class.__name__
        super(ModelType, self).__init__(**kwargs)

    def serialize(self, value, primitive=False):
        """Serialize this field."""
        return value.serialize(primitive=primitive)


class ListType(BaseType):

    def __init__(self, field, default=None, sorted=False, **kwargs):
        super(ListType, self).__init__(**kwargs)
        self.field = field
        self.default = default if default is not None else []
        self.sorted = sorted

    # def __get__(self, instance, owner):
    #     """Descriptor for retrieving a value from a field in a Model."""
    #     # Check if Model class is being called, rather than Model instance
    #     if instance is None:
    #         return self
    #     # Get value from Model instance if available
    #     value = instance._values.get(self.name)
    #     # If value is None or empty string then return the default value, if set
    #     if value in [None, '', []]:
    #         return self.default if self.default is not None else []
    #     return value

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a ListField in a Model."""
        # Run process for the nested field type for each value in list
        if value is None:
            instance._values[self.name] = None
        else:
            processed = [self.field.process(v) for v in value]
            if self.sorted:
                processed = sorted(processed)
            instance._values[self.name] = [self.field.process(v) for v in value]

    def serialize(self, value, primitive=False):
        """Serialize this field."""
        return [self.field.serialize(v, primitive=primitive) for v in value]


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
    """"""

    fields = {}
    parsers = []
    specifier = None

    def __init__(self, **raw_data):
        """"""
        self._values = {}
        for key, value in six.iteritems(raw_data):
            setattr(self, key, value)
        # Set defaults
        for key, field in six.iteritems(self.fields):
            if key not in raw_data:
                setattr(self, key, copy.copy(field.default))

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
        try:
            if key in self.fields:
                return getattr(self, key)
        except AttributeError:
            pass
        raise KeyError(key)

    def __setitem__(self, key, value):
        """Redirect dictionary-style field setting to attribute-style."""
        if key not in self.fields:
            raise KeyError(key)
        return setattr(self, key, value)

    def __contains__(self, name):
        try:
            val = getattr(self, name)
            return val is not None
        except AttributeError:
            return False

    def __hash__(self):
        return str(self.serialize()).__hash__()

    @classmethod
    def reset_mutables(cls):
        """
        Reset all mutable parse_expressions of properties associated with the class.
        """
        for key, field in six.iteritems(cls.fields):
            if cls.fields[key].mutable:
                cls.fields[key].reset()

    @classmethod
    def update(cls, definitions):
        """Update this Element's mutable attributes with new information from definitions

        Arguments:
            definitions {list} -- list of definitions found in this element
        """
        log.debug("Updating model")
        for definition in definitions:
            for field in cls.fields:
                if cls.fields[field].mutable:
                    matches = [i for i in cls.fields[field].parse_expression.scan(definition['tokens'])]
                    # print(matches)
                    if any(matches):
                        cls.fields[field].parse_expression = cls.fields[field].parse_expression | W(str(definition['specifier']))
        return

    def keys(self):
        return list(iter(self))

    def items(self):
        return [(k, getattr(self, k)) for k in self]

    def values(self):
        return [getattr(self, k) for k in self]

    def get(self, key, default=None):
        return getattr(self, key, default)

    # def validate(self):
    #     """"""
    #     for field_name in self:
    #         self.fields[field_name].validate()

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
        for field_name, field in six.iteritems(self.fields):
            if hasattr(field, 'model_class'):
                if self[field_name] == field.default \
                   and field.required:
                    return False
                if hasattr(self[field_name], 'required_fulfilled') and \
                   not self[field_name].required_fulfilled:
                    log.debug('Required unfulfilled')
                    return False
            elif field.required and self[field_name] == field.default:
                log.debug('Required unfulfilled')
                return False
        log.debug('Required fulfilled')
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

    def merge_contextual(self, other):
        """
        Merges any fields marked contextual with additional information from other provided that:

        - other is of the same type and they don't have any conflicting fields

        or

        - other is a model type that is part of this model and that field is currently
        set to be the default value or the field can be merged with the other.

        .. note::

            This method mutates the model it's called on **and** returns it.

        :param other: The other model to merge into this model
        :type other: BaseModel
        :return: A merged model
        :rtype: BaseModel
        """

        log.debug(self.serialize())
        log.debug(other.serialize())
        if self.contextual_fulfilled:
            return self
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            match = True
            for field_name, field in six.iteritems(self.fields):
                if (self[field_name] is not None
                   and other[field_name] is not None
                   and self[field_name] != other[field_name]):
                    match = False
                    break
            if match:
                for field_name, field in six.iteritems(self.fields):
                    if (field.contextual
                       and self[field_name] is None
                       and other.get(field_name, None) is not None):
                        self[field_name] = other[field_name]
        else:
            for field_name, field in six.iteritems(self.fields):
                if hasattr(field, 'model_class') and isinstance(other, field.model_class):
                    log.debug('model class case')
                    if self[field_name] is not None and not self[field_name].contextual_fulfilled:
                        self[field_name] = self[field_name].merge_contextual(other)
                    elif field.contextual and self[field_name] is None:
                        log.debug(field_name)
                        self[field_name] = copy.copy(other)
        return self

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
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            match = True
            for field_name, field in six.iteritems(self.fields):
                if (self[field_name] is not None
                  and other[field_name] is not None
                  and self[field_name] != other[field_name]):
                    match = False
                    break
            if match:
                for field_name, field in six.iteritems(self.fields):
                    if (self[field_name] is None
                      and other.get(field_name, None) is not None):
                        self[field_name] = other[field_name]
        else:
            for field_name, field in six.iteritems(self.fields):
                if hasattr(field, 'model_class') and isinstance(other, field.model_class):
                    log.debug('model class case')
                    if self[field_name] is not None:
                        self[field_name] = self[field_name].merge_all(
                            other)
                    elif self[field_name] is None:
                        log.debug(field_name)
                        self[field_name] = copy.copy(other)
        return self


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

