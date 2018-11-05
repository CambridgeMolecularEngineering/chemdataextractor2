# -*- coding: utf-8 -*-
"""
chemdataextractor.parse.units
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Functions to get chemdataextractor.quantities.units from string representations of units.expected_dimensions

Taketomo Isazawa (ti250@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re
from fractions import Fraction

from .elements import R
from ..units.quantities import DimensionlessUnit

log = logging.getLogger(__name__)


exponents_dict = {R('k', group=0): 3., R('M', group=0): 6., R('G', group=0): 9., R('T', group=0): 12.,
                  R('m', group=0): -3., R('µ', group=0): -6., R('n', group=0): -9., R('p', group=0): -12.}


def extract_units(string, expected_dimensions, strict=False):
    """
    Takes a string and returns a Unit.
    Raises TypeError if strict and the dimensions do not match the expected dimensions.

    Usage::
        expected_dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
        test_string = 'Kh2/(km/s)-1/2'
        end_units = extract_units(test_string, expected_dimensions, strict=True)
        print(end_units) # Units of: (10^1.5) * Hour^(2.0)  Meter^(0.5)  Second^(-0.5)  Kelvin^(1.0)

    :param str string: A representation of the units as a string
    :param chemdataextractor.quantities.Dimension expected_dimensions: The expected dimensions of the resulting unit.
    :param bool strict: Whether to raise a TypeError if the dimensions of the parsed units do not have the expected dimensions.
    :returns: The string expressed as a Unit
    :rtype: chemdataextractor.quantities.Unit
    """
    split_string = _split(string)
    unit_types = _find_unit_types(split_string, expected_dimensions)
    powers = _find_powers(unit_types)
    end_unit = _find_units(powers, expected_dimensions, strict)
    return end_unit


def _split(string):
    """
    Splits string at numbers, /s, and brackets.

    :param str string: A representation of the units as a string
    :returns: The string split at numbers, /s, and brackets.
    :rtype: list(str)
    """

    # Split at numbers
    split_by_num = re.split('(\d+(?!\d+))', string)
    split_by_num_cleaned = []
    for element in split_by_num:
        try:
            # Check if the element is a number or not by trying to convert to float.
            float(element)
            split_by_num_cleaned[-1] = split_by_num_cleaned[-1] + element
        except ValueError:
            # Deal with fractions in powers
            if element == "/":
                split_by_num_cleaned[-1] = split_by_num_cleaned[-1] + element
            else:
                split_by_num_cleaned.append(element)

    # Split at slashes
    split_by_slash = []
    for element in split_by_num_cleaned:
        split = re.split('(/[^\d])', element)
        split_by_slash += split

    # Split at brackets
    split_by_bracket = []
    for element in split_by_slash:
        split = re.split('(\()', element)
        split_by_bracket += split

    # Merge bits that were split too much
    final_list = []
    for element in split_by_bracket:
        # Merge /s with forward brackets, or text,
        # e.g. ['/', '('] -> ['/('] and ['/n', 's'] -> ['/ns']
        if (re.match('-?\d\d*(\.\d\d*)?(/?-?\d\d*(\.\d\d*)?)?', element)
            or (final_list != [] and re.match('[\/]\D*', final_list[-1])
                and not re.match('\)\w*', element) and not re.match('\/\(', final_list[-1]))):
            final_list[-1] = final_list[-1] + element
        else:
            final_list.append(element)

    # Remove empty substrings
    final_list_cleaned = []
    for element in final_list:
        if element != '' and element != ' ':
            final_list_cleaned.append(element)
    return final_list_cleaned


def _find_unit_types(tokenized_sentence, dimensions):
    """
    Finds the unit types in the string and splits the string at the units

    :param list(str) tokenized_sentence: The sentence split at brackets, numbers, and slashes.
    :param chemdataextractor.quantities.dimensions dimensions: The dimensions with units to look for
    :returns: A list containing tuples of the found units and the string split by the units, in the format (unit, string containing the unit, the substring that caused the unit to be recognised)
    :rtype: list((chemdataextractor.quantities.Unit, str, str))
    """
    units_dict = dimensions.units_dict
    units_list = []
    # This is O(m*n), m being the length of the units dictionary, n the number of components of powers.
    for element in tokenized_sentence:
        # Find the elements first, but don't look for the locations
        found_units = {}
        # splitting_symbols is used to split the string into the parts pertaining to each element later
        splitting_symbols = '(['
        for unit in units_dict.keys():
            for result in unit.scan([[element, 'a']]):
                found_units[result[0].text] = units_dict[unit]
                splitting_symbols += '(' + result[0].text + ')'
        # If none found, then return the original string and that no units were found.
        if len(found_units) == 0:
            units_list.append((None, element, None))
        else:
            # Split into substrings for each unit
            splitting_symbols += '])'
            split = re.split(splitting_symbols, element)
            most_recent_unit = None
            most_recent_key = ''
            prev_key = ''
            current_string = ''
            # Iterate through the substrings to find the occurences of the units. prev_key is used to deal with cases like mm, where if you have two occurences of the same symbol, it's likely that the first letter was a modifier, hopefully an exponent, on the first.
            for index, string in enumerate(split):
                if string in found_units.keys():
                    if most_recent_unit is not None:
                        new_unit = found_units[string]
                        new_key = string
                        if len(units_list) != 0 and prev_key != '' and most_recent_key == prev_key:
                            old_unit, old_string, old_key = units_list.pop(-1)
                            units_list.append((most_recent_unit, old_string + current_string, most_recent_key))
                        else:
                            units_list.append((most_recent_unit, current_string, most_recent_key))
                        most_recent_unit = new_unit
                        current_string = string
                        prev_key = most_recent_key
                        most_recent_key = new_key
                    else:
                        most_recent_unit = found_units[string]
                        current_string += string
                        prev_key = most_recent_key
                        most_recent_key = string
                else:
                    current_string += string
                    if index == (len(split) - 1):
                        if prev_key != '' and most_recent_key == prev_key:
                            unit, string, key = units_list.pop(-1)
                            units_list.append((most_recent_unit, string + current_string, most_recent_key))
                        else:
                            units_list.append((most_recent_unit, current_string, most_recent_key))
    return units_list


def _find_powers(units_list):
    """
    Finds the powers associated with each of the units

    :param list((chemdataextractor.quantities.Unit, str, str)) units_list: The units found, in the format (units found, string in which this occured, string which matched with the unit's definition)
    :returns: A list containing tuples of the found units and the string split by the units, in the format (units found, string in which this occured, power associated with the unit, string which matched with the unit's definition)
    :rtype: list((chemdataextractor.quantities.Unit, str, str, str))
    """

    powers = []
    i = 0

    while i in range(len(units_list)):

        element = units_list[i][1]

        power = 1.0
        if element[0] == '/':
            power = power * -1.0
            element = re.split('/', element)[1]
        found_power = re.search('-?\d\d*(\.\d\d*)?(/?-?\d\d*(\.\d\d*)?)?', element)
        if found_power is not None:
            power = power * float(sum(Fraction(s) for s in found_power.group(0).split()))
            element = re.split(found_power.group(0), element)[0]

        powers.append((units_list[i][0], element, power, units_list[i][2]))
        i += 1
    powers_cleaned, _ = _remove_brackets(powers)
    return powers_cleaned


def _remove_brackets(powers, base_power=1.0):
    """
    Helper to _find_powers, resolving powers from brackets

    :param list((chemdataextractor.quantities.Unit, str, str)) units_list: The units found, in the format (units found, string in which this occured, string which matched with the unit's definition)
    :param float base_power: The power of all the elements within this set of brackets. Default 1.0. An example of when this would be different is when we have /(km)
    :returns: A tuple, where the first element is a list containing tuples of the found units and the string split by the units, in the format (units found, string in which this occured, power associated with the unit, string which matched with the unit's definition). The second element of the tuple is just used for _remove_brackets, should be ignored.
    :rtype: tuple(list((chemdataextractor.quantities.Unit, str, str, str)), int)
    """
    current_powers = []
    i = 0
    while i in range(len(powers)):
        if powers[i][1] == '(':
            returned = _remove_brackets(powers[i + 1:],
                                       base_power=powers[i][2])
            current_powers = current_powers + returned[0]
            i = i + returned[1] + 2

        elif powers[i][1] == ')':
            corrected = []
            for current_power in current_powers:
                corrected.append((current_power[0], current_power[1], current_power[2] * powers[i][2], current_power[3]))
            return (corrected, i)
        else:
            current_powers.append((powers[i][0], powers[i][1], powers[i][2] * base_power, powers[i][3]))
            i += 1
    return (current_powers, i)


def _find_units(powers_cleaned, dimensions, strict):
    """
    Finds the powers associated with each of the units

    :param list((chemdataextractor.quantities.Unit, str, str, str)) powers_cleaned: The units found, in the format (units found, string in which this occured, power associated with the unit, string which matched with the unit's definition)
    :param Dimension dimensions: The dimensions that the units found are expected to have.
    :param bool strict: Whether the dimensions of the results will be checked against the dimensions give.
    :returns: The units found from the list given.
    :rtype: chemdataextractor.quantities.Unit
    """
    powers = {}
    for power in powers_cleaned:
        original_string = power[1]
        matched = power[3]
        if matched is not None:
            original_string = re.sub(matched, '', original_string, 1)
        exp = 0.
        if original_string != '':
            for exponent in exponents_dict.keys():
                for result in exponent.scan([[original_string, 'a']]):
                    exp = exponents_dict[exponent]
        powers[power[0](exponent=exp)] = power[2]
    end_unit = DimensionlessUnit()
    for unit, power in powers.items():
        log.debug(unit, '^', power)
        end_unit = end_unit * (unit ** power)
    if strict:
        if end_unit.dimensions == dimensions:
            return end_unit
        else:
            raise TypeError('Parsed with Dimensions ' + end_unit.dimensions + ', expected' + dimensions)
    else:
        return end_unit
