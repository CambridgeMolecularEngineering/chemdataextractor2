.. _creating_units:
.. role:: python(code)
   :language: python

******************************************
Creating new units and dimensions
******************************************

Overview
=================================

Units and dimensions are a new addition to ChemDataExtractor 2.0, and form a fundamental component in making sure that a large number of new features, such as automatic parsing, works. Many units are included in ChemDataExtractor, making it easy to create models out of the box, but there may be cases when you need to create your own units, and this document should get you started with that.

Dimensions
===============================

If you're implementing a completely new type of unit, then the first step you need to take is to write a dimension for it. An example of an implementation of dimension is as follows::

    class Temperature(Dimension):
        pass

As you can see, it's incredibly simple to define a dimension from scratch; all that really matters is the name of the dimension, so you just need to define the name for the dimension and the rest can be empty. If you want to implement *composite dimensions*, that is, dimensions which are composed of other, more basic dimensions, such as speed, you just need one more line of code::

    class Speed(Dimension):
        constituent_dimensions = Length() / Time()

Units
====================

Defining a unit for a certain dimension is also straightforward, but each unit needs to implement an :python:`__init__` function, although it's just boilerplate code::

    def __init__(self, magnitude=0.0, powers=None):
        super(TemperatureUnit, self).__init__(Temperature(), magnitude, powers)

Where the first argument passed to the superclass should be the dimensions that you want the unit to have. Writing this for each unit would be wasteful, so for each commonly used type of unit, we have defined a subclass of :class:`~chemdataextractor.model.units.unit.Unit`, such as :class:`~chemdataextractor.models.units.temperature.TemperatureUnit`, which you can subclass from to get these initializers for free. We would encourage you to do the same.

Once that's done, each unit needs to implement functions to convert values and errors to the standard value. The four functions that need to be implemented are :meth:`~chemdataextractor.model.units.unit.Unit.convert_value_to_standard`, :meth:`~chemdataextractor.model.units.unit.Unit.convert_value_from_standard`, :meth:`~chemdataextractor.model.units.unit.Unit.convert_error_to_standard`, and :meth:`~chemdataextractor.model.units.unit.Unit.convert_error_from_standard`. It is crucial that you provide documentation about what the standard unit is for each type of unit so that when people build other units of the same type, they know what each function should do. An example of a unit is the Fahrenheit class::

    class Fahrenheit(TemperatureUnit):
        """
        Class for Fahrenheit.
        """

        def convert_value_to_standard(self, value):
            return (value + 459.67) * (5. / 9.)

        def convert_value_from_standard(self, value):
            return value * (9. / 5.) - 459.67

        def convert_error_to_standard(self, error):
            return error * (5. / 9.)

        def convert_error_from_standard(self, error):
            return error * (9. / 5.)

Defining a standard unit
------------------------

In addition to documenting what the standard unit is, you should also enforce it in code by setting the dimension's standard units. This can simply be done as follows, in the example of temperature::

    Temperature.standard_units = Kelvin()

After which all instances of temperature will hold a reference to the correct standard units. This is used in :meth:`~chemdataextractor.model.units.quantity_model.QuantityModel.convert_to_standard` to make it easy to convert any models to the standard values. If you define a composite dimension and this property not set, the standard units will be automatically inferred from the constituent units' standard units, e.g. a speed dimension will automatically have a standard unit of m/s.

Adding facilities for parsing
==============================

Whilst all magnitudes (e.g. kilo-, centi-, mega-, etc.) are handled by ChemDataExtractor, you need to write down parse expressions to make sure that units are extracted correctly and picked up correctly by autoparsers. To do this, you need to set the :attr:`~chemdataextractor.units.dimension.Dimension.units_dict` property of your dimension. An example can be seen in the case of temperatures::

    units_dict = {R('°?(((K|k)elvin(s)?)|K)\.?', group=0): Kelvin,
              R('(°C|((C|c)elsius))\.?', group=0): Celsius,
              R('°?((F|f)ahrenheit|F)\.?', group=0): Fahrenheit,
              R('°|C', group=0): None}
    Temperature.units_dict = units_dict

.. note::

    This property needs to be set after the declaration of the dimension class as :attr:`~chemdataextractor.units.dimension.Dimension.units_dict` references the units which in turn reference the dimensions.

.. note::

        The units_dict has been extensively tested using regex elements, and while in theory it may work with other parse
        elements, it is strongly recommended that you use a regex element.
        If a regex element is specified, it should

        - Not have a $ symbol at the end: the units can be passed in with numbers or other symbols after it, and these are also used in the autoparser to find candidate tokens which may contain units, and a $ symbol at the end would stop this from working.

        - Have the group attribute set to 0. Unless this is set, the default behaviour of the regex element is to return the whole token in which the match was found. This is unhelpful behaviour for our logic for extracting units, as we want to extract only the exact characters that matched the unit.

The final element in the above :attr:`~chemdataextractor.model.units.dimension.Dimension.units_dict` has no unit set to it. This is a special case which is used by autoparsers but not during units extraction. This is to handle the fact that °C is always split into two tokens, so we need to be able to capture these separately, but we do not want that to affect units extraction later down the line.

In the case you have a composite dimension, such as energy, you should **update** :attr:`~chemdataextractor.model.units.dimension.Dimension.units_dict` instead of setting it, so that ChemDataExtractor can correctly extract the dimension even if it is composed of its constituent SI units. ::

    units_dict = {R('(J|j)(oule(s)?)?', group=0): Joule,
                R('(E|e)(lectron)( )?(V|v)(olts)?', group=0): ElectronVolt}
    Energy.units_dict.update(units_dict)


