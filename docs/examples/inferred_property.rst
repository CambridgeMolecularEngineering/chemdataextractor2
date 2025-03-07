.. _inferred_properties_guide:

.. role:: python(code)
   :language: python

******************************************
Inferred Properties
******************************************

ChemDataExtractor provides the :class:`~chemdataextractor.model.base.InferredProperty` class so that you can save time on boilerplate code in your parser by making relationships between fields explicit. Let's look at how you can do this by looking at how this functionality is used within the ChemDataExtractor library to express the relationship between ``raw_value`` and ``value`` in the :class:`~chemdataextractor.model.units.quantity_model.QuantityModel` class. ::

    class QuantityModel(BaseModel, metaclass=_QuantityModelMeta):
        raw_value = StringType(required=True, contextual=True)
        raw_units = StringType(required=True, contextual=True)
        value = InferredProperty(ListType(FloatType(), sorted_=True),
                                 origin_field='raw_value', inferrer=infer_value, contextual=True)
        units = InferredProperty(UnitType(),
                                 origin_field='raw_units', inferrer=infer_unit, contextual=True)
        error = InferredProperty(FloatType(),
                                 origin_field='raw_value', inferrer=infer_error, contextual=True)

Let's break down what we've done with the ``value`` property step by step. First, we specify that it's an :class:`~chemdataextractor.model.base.InferredProperty`. Similarly to what we do with :class:`~chemdataextractor.model.base.ListType`, we first pass in the type of the content. In this case, it's a sorted list of floats. We can then specify the origin field, and the inferrer used. The inferrer is a function which takes as input the value of the origin field, and the :class:`~chemdataextractor.model.base.BaseModel` instance for which the value is being inferred, and returns the inferred value, or None. Let's take a look at what the inferrer for inferring values looks like::

    def infer_value(string, instance):
        value = None
        if string != 'NoValue' and string != '':
            try:
                value = extract_value(string)
            except (TypeError, IndexError) as e:
                log.debug(e)
        return value

So here we can see the implementation for ``infer_value`` as included in ChemDataExtractor. The implementation is incredibly simple; it just tries to extract the value from the string and returns the extracted values.

Having defined the relationship and written this function, you no longer need to write any custom interpretation code in your parser. Any parser that extracts a :class:`~chemdataextractor.model.units.quantity_model.QuantityModel` will automatically default to using the ``infer_value`` function when required to extract the value.

.. note::

    While ChemDataExtractor will default to using the ``infer_value`` function in this case, if your parser includes custom behaviour to set the ``value`` property, that will take priority and automatically override the inferring of properties for that field.
