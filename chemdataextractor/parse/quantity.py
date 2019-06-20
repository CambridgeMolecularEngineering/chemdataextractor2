# -*- coding: utf-8 -*-
"""
Parser for finding quantities and units

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re
import six
from fractions import Fraction
from abc import abstractproperty

from .common import lbrct, rbrct
from .actions import merge, join
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore
from ..utils import memoize

log = logging.getLogger(__name__)

magnitudes_dict = {R('c(enti)?', group=0): -2.,
                  R('k(ilo)?', group=0): 3.,
                  R('M(ega)?', group=0): 6.,
                  R('G(iga)?', group=0): 9.,
                  R('T(era)?', group=0): 12.,
                  R('m(illi)?', group=0): -3.,
                  R('µ|(micro)|(mu)', group=0): -6.,
                  R('n(ano)?', group=0): -9.,
                  R('p(ico)?', group=0): -12.}


def value_element(units=(OneOrMore(T('NN')) | OneOrMore(T('NNP')) | OneOrMore(T('NNPS')) | OneOrMore(T('NNS')))('raw_units').add_action(merge)):
    """
    Returns an Element for values with given units. By default, uses tags to guess that a unit exists.

    :param BaseParserElement units: (Optional) A parser element for the units that are to be looked for. Default option looks for nouns.
    :returns: An Element to look for values and units.
    :rtype: BaseParserElement
    """
    number = R('^[\+\-–−]?\d+(([\.・,\d])+)?$')
    joined_range = R('^[\+\-–−]?\d+(([\.・,\d])+)?[\-–−~∼˜]\d+(([\.・,\d])+)?$')('raw_value').add_action(merge)
    spaced_range = (number + Optional(units).hide() + (R('^[\-–−~∼˜]$') + number | number))('raw_value').add_action(merge)
    to_range = (number + Optional(units).hide() + I('to') + number)('raw_value').add_action(join)
    plusminus_range = (number + R('±') + number)('raw_value').add_action(join)
    bracket_range = R(number.pattern[:-1] + '\(\d+\)' + '$')('raw_value')
    between_range = (I('between').hide() + number + I('and') + number).add_action(join)
    value_range = (Optional(R('^[\-–−]$')) + (bracket_range | plusminus_range | joined_range | spaced_range | to_range | between_range))('raw_value').add_action(merge)
    value_single = (Optional(R('^[~∼˜\<\>]$')) + Optional(R('^[\-–−]$')) + number)('raw_value').add_action(merge)
    value = Optional(lbrct).hide() + (value_range | value_single)('raw_value') + Optional(rbrct).hide()
    return value + units


@memoize
def value_element_plain():
    """
    Returns an element similar to value_element but without any units.

    :returns: An Element to look for values.
    :rtype: BaseParserElement
    """
    number = R('^[\+\-–−]?\d+(([\.・,\d])+)?$')
    joined_range = R('^[\+\-–−]?\d+(([\.・,\d])+)?[\-–−~∼˜]\d+(([\.・,\d])+)?$')('raw_value').add_action(merge)
    spaced_range = (number + R('^[\-–−~∼˜]$') + number)('raw_value').add_action(merge)
    to_range = (number + I('to') + number)('raw_value').add_action(join)
    plusminus_range = (number + R('±') + number)('raw_value').add_action(join)
    bracket_range = R(number.pattern[:-1] + '\(\d+\)' + '$')('raw_value')
    between_range = (I('between').hide() + number + I('and') + number).add_action(join)
    value_range = (Optional(R('^[\-–−]$')) + (plusminus_range | joined_range | spaced_range | to_range | between_range | bracket_range))('raw_value').add_action(merge)
    value_single = (Optional(R('^[~∼˜\<\>]$')) + Optional(R('^[\-–−]$')) + number)('raw_value').add_action(merge)
    value = Optional(lbrct).hide() + (value_range | value_single)('raw_value') + Optional(rbrct).hide()
    return value


@memoize
def construct_quantity_re(*models):
    # Handle all the magnitudes
    units_regex = '(('
    for element in magnitudes_dict.keys():
        units_regex += '(' + element.pattern + ')|'
    units_regex = units_regex[:-1]
    units_regex += ')?'
    units_regex += '('
    units_dict = {}
    for model in models:
        if hasattr(model, 'dimensions') and model.dimensions.units_dict is not None:
            units_dict.update(model.dimensions.units_dict)
    if len(units_dict) == 0:
        return None
    # Case where we have a token that's just brackets
    units_regex += '(\((?!\d))|(\))|\-|'
    # Handle all the units
    for element, unit in six.iteritems(units_dict):
        if unit is not None:
            units_regex += '(' + element.pattern + ')|'
    units_regex += '(\/)'
    # Case when we have powers, or one or more units
    units_regex2 = units_regex + '|([\+\-–−]?\d+(\.\d+)?)'
    units_regex2 += '))+$'
    units_regex += '))+'
    units_regex += (units_regex2[:-2] + '*')
    units_regex = '^((?P<split>[\+\-–−]?\d+([\.\-\−]?\d+)?)|((?P<split2>.*)(\(|\/)))' + units_regex
    units_regex += '$'
    # print(units_regex)
    return re.compile(units_regex)


def extract_error(string):
    """
    Extract the error from a string

    Usage::

        test_string = '150±5'
        end_value = extract_error(test_string)
        print(end_value) # 5

    :param str string: A representation of the value and error as a string
    :returns: The error expressed as a float .
    :rtype: float
    """
    if string is None:
        return None
    string = _clean_value_string(string)
    split_by_num_and_error = [r for r in re.split('(\d+\.?(?:\d+)?)|(±)|(\()', string) if r and r != " "]
    error = None
    for index, value in enumerate(split_by_num_and_error):
        if value == '±':
            try:
                error = float(split_by_num_and_error[index + 1])
                break
            except ValueError:
                pass
        elif value == '(':
            error = _extract_brackets_error(string)
            break
    return error


def extract_value(string):
    """
    Takes a string and returns a list of floats representing the string given.

    Usage::

        test_string = '150 to 160'
        end_value = extract_value(test_string)
        print(end_value) # [150., 160.]

    :param str string: A representation of the values as a string
    :returns: The value expressed as a list of floats of length 1 if the value had no range,
        and as a list of floats of length 2 if it was a range.
    :rtype: list(float)
    """
    if string is None:
        return None
    new_split_by_num = _find_value_strings(string)
    values = []
    for index, value in enumerate(new_split_by_num):
        try:
            float_val = float(value)
            values.append(float_val)
        except ValueError:
            pass
    return values


def _find_value_strings(string):
    """
    Finds the string(s) containing the value from the string given.

    :param str string: A representation of the values as a string
    :returns: The strings pertaining to the value as a list
    :rtype: list(str)
    """
    if string is None:
        return None
    string = _clean_value_string(string)
    string = string.split("±")[0]
    string = string.split("(")[0]
    split_by_space = [r for r in re.split(' |(-)', string) if r]
    split_by_num = []
    for elem in split_by_space:
        split_by_num.extend([r for r in re.split('(\d+\.?(?:\d+)?)', elem) if r])
    if split_by_num[0] == "-":
        split_by_num[0] = "-" + split_by_num.pop(1)
    flag = 0
    new_split_by_num = []
    for index, value in enumerate(split_by_num):
        if flag == 2:
            new_split_by_num.append(split_by_num[index - 2])
            new_split_by_num.append(split_by_num[index - 1] + value)
            flag = 0
        elif flag == 1 and re.match('(-?\d+\.?(?:\d+)?)', value):
            new_split_by_num.append(split_by_num[index - 1])
            new_split_by_num.append(value)
            flag = 0
        elif not re.match('(-?\d+\.?(?:\d+)?)', value):
            flag += 1
        else:
            new_split_by_num.append(value)
    return new_split_by_num


def _clean_value_string(string):
    """
    Function to clean and standardise a string containing a value. Also converts from
    European formats (commas instead of full stops)

    :param str string: A representation of the values as a string
    :returns: A cleaned version of the string
    :rtype: str
    """
    string = string.replace("-", "-")
    string = string.replace("–", "-")
    string = string.replace("−", "-")
    string = string.replace("・", ".")
    string = string.replace("·", ".")
    split_by_comma = string.split(",")
    if len(split_by_comma) != 1:
        if len(split_by_comma) == 2:
            if "." not in split_by_comma[1] \
               and len(split_by_comma[1]) != 3:
                string = _convert_from_european_format(string)
            else:
                string = string.replace(",", "")
        else:
            string = string.replace(",", "")
    return string


def _extract_brackets_error(string):
    """
    Extract errors from a string when it is expressed in the form of 123(4).

    :param str string: A representation of the value and error as a string
    :returns: The error
    :rtype: float
    """
    split_by_brackets = [r for r in re.split('(\))|(\()', string) if r]
    val_string = _find_value_strings(string)[0]
    magnitude = _get_magnitude(val_string)
    magnitude = magnitude if magnitude < 0 else 0
    if len(split_by_brackets) == 4:
        error_unadjusted = float(split_by_brackets[2])
        return error_unadjusted * 10. ** magnitude
    else:
        raise ValueError(string + " does not contain the right number of brackets")


def _get_magnitude(string):
    """
    Get the magnitude of the smallest significant value in the string

    :param str string: A representation of the value as a string
    :returns: The magnitude of the value in the string. e.g. for 102, the magnitude is 0, and for 102.03 it is -2
    :rtype: int
    """
    split_by_period = string.split(".")
    if len(split_by_period) == 2:
        return -1 * len(split_by_period[-1])
    elif len(split_by_period) == 1:
        return len(string) - len(string.rstrip('0'))
    else:
        raise ValueError(string + " does not contain a value")


def _convert_from_european_format(string):
    """
    Conver the string given in the European format (commas as decimal points,
    full stops as the equivalent of commas), e.g. 1,200.5 would be written as
    1.200,5 in the European format.

    :param str string: A representation of the value as a string
    :returns: The string converted to standard format
    :rtype: str
    """
    string = string.replace(".", "")
    string = string.replace(",", ".")
    return string


@memoize
def extract_units(string, dimensions, strict=False):
    """
    Takes a string and returns a Unit.
    Raises TypeError if strict and the dimensions do not match the expected dimensions
    or the string has extraneous characters, e.g. if a string Fe was given, and we were
    looking for a temperature, strict=False would return Fahrenheit, strinct=True would
    raise a TypeError.

    Usage::

        dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
        test_string = 'Kh2/(km/s)-1/2'
        end_units = extract_units(test_string, dimensions, strict=True)
        print(end_units) # Units of: (10^1.5) * Hour^(2.0)  Meter^(0.5)  Second^(-0.5)  Kelvin^(1.0)

    :param str string: A representation of the units as a string
    :param bool strict: (Optional) Whether to raise a TypeError if the dimensions of the parsed units do not have the expected dimensions.
    :returns: The string expressed as a Unit
    :rtype: chemdataextractor.quantities.Unit
    """
    if string is None and not strict:
        return None
    elif string is None:
        raise TypeError('None was passed in')
    string = string.replace("-", "-")
    string = string.replace("–", "-")
    string = string.replace("−", "-")
    string = string.replace(' ', '')
    # Split string at numbers, /s, and brackets, so we have the units tokenized into the right units for later processing stages.
    split_string = _split(string)
    # Find the units by matching strings, e.g. K for Kelvin, m for Meter
    unit_types = _find_unit_types(split_string, dimensions)
    # Find the powers associated with each unit
    try:
        powers = _find_powers(unit_types)
    except ValueError as e:
        if not strict:
            return None
        else:
            raise TypeError('Error extracting power: \n' + str(e) + '\n encountered during parsing')
    # Deal with things like kilo, mega, or milli that modify the magnitude of the units found
    end_unit = _find_units(powers, dimensions, strict)
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
        split = re.split('(\()|(\))', element)
        split_by_bracket += split

    # Merge bits that were split too much
    final_list = []
    for element in split_by_bracket:
        if element is not None:
            # Merge /s with forward brackets, or text,
            # e.g. ['/', '('] -> ['/('] and ['/n', 's'] -> ['/ns']
            # Also merge numbers
            if (re.match('-?\d\d*(\.\d\d*)?(/?-?\d\d*(\.\d\d*)?)?', element)
                or (final_list != [] and re.match('[\/]\D*', final_list[-1])
                    and not re.match('\)\w*', element) and not re.match('\/\(', final_list[-1]))
                    and not re.match('/', element)):
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
    :returns: A list containing tuples of the found units and the string split by the units, in the format (unit, string containing the unit, the substring that caused the unit to be recognised)
    :rtype: list((chemdataextractor.quantities.Unit, str, str))
    """
    units_dict = {}
    for key, value in six.iteritems(dimensions.units_dict):
        if value is not None:
            units_dict[key] = value
    units_list = []
    # This is O(m*n), m being the length of the units dictionary, n the number of components of powers.
    for element in tokenized_sentence:
        # Find the elements first, but don't look for the locations
        found_units = {}
        # splitting_symbols is used to split the string into the parts pertaining to each element later
        splitting_symbols = '('
        for unit in units_dict.keys():
            for result in unit.scan([[element, 'a']]):
                found_units[result[0].text] = units_dict[unit]
                splitting_symbols += result[0].text + '|'
        # If none found, then return the original string and that no units were found.
        if len(found_units) == 0:
            units_list.append((None, element, None))
        else:
            # Split into substrings for each unit
            splitting_symbols = splitting_symbols[:-1]
            splitting_symbols += ')'
            split = re.split(splitting_symbols, element)

            # Iterate through the substrings to find the occurences of the units.
            # Constructs a list of tuples of (Unit, string in which the unit was found, string corresponding to the unit itself)
            # Algorithm is as follows:
            # - If the token corresponds to a unit (path 1):
            #   + Append it and its string to the units_list, (path 1a), unless
            #   + The token corresponds to the same unit as the previous token, then that probably represents a magnitude (e.g. mm),
            #     so add the string to the 'string in which the unit was found' for the previous tuple (path 1b).
            # - If the token's a number, it's a power of some sort, so add it to the previous tuple (path 2).
            # - Else add it to the current_string so that it's incorporated in the next unit that comes along's tuple, as it
            # represents a magnitude of some sort, e.g. kilo or mega (path 3).
            prev_unit = None
            current_string = ''
            for index, string in enumerate(split):
                if string in found_units.keys():
                    # path 1
                    if found_units[string] == prev_unit:
                        # path 1a
                        units_list[-1] = (prev_unit, units_list[-1][1] + string, units_list[-1][2])
                    else:
                        # path 1b
                        units_list.append((found_units[string], current_string + string, string))
                    current_string = ''
                    prev_unit = found_units[string]
                elif re.match('-?\d\d*(\.\d\d*)?(/?-?\d\d*(\.\d\d*)?)?', string):
                    # path 2
                    units_list[-1] = (units_list[-1][0], units_list[-1][1] + string, units_list[-1][2])
                else:
                    # path 3
                    current_string += string
                    if index == len(split) - 1:
                        units_list[-1] = (units_list[-1][0], units_list[-1][1] + current_string, units_list[-1][2])
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
    # base_power to account for examples such as K/km2s, where a series of units after the division should be accounted for
    base_power = 1.0
    # Go through list of found units/substrings and associate a power with each of them. Ignores brackets in the loop, which are handled in _remove_brackets
    while i in range(len(units_list)):

        element = units_list[i][1]
        power = base_power
        if element[0] == '/':
            power = -1.0
            base_power = -1.0
            element = re.split('/', element)[1]
        # Reset base_power at end of brackets, to account for cases like K/(km/s)-1/2
        # Without this, this would be parsed as Kkm-1/2s1/2 as the base_power would carry to the
        # -1/2 after the end of the brackets
        elif element[0] == ')':
            power = 1.0
            base_power = 1.0
        # Look for strings involving numbers.
        found_power = re.search('-?\d\d*(\.\d\d*)?(/?-?\d\d*(\.\d\d*)?)?', element)
        if found_power is not None:
            power = power * float(sum(Fraction(s) for s in found_power.group(0).split()))
            element = re.split(found_power.group(0), element)[0]
        powers.append((units_list[i][0], element, power, units_list[i][2]))
        # Reset base_power at the start of a bracket, as that's handled by _remove_brackets
        # This also ensures desired behaviour on e.g. K/(km/s)A, which should resolve to
        # KAskm-1
        if element[0] == '(':
            base_power = 1.0
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
    # This function assumes that the brackets match up correctly.
    current_powers = []
    i = 0
    while i in range(len(powers)):
        if powers[i][1] == '(':
            # Call self with the substrings beyond the opening brackets. base_power is set in case the opening bracket had a division operator before it.
            returned = _remove_brackets(powers[i + 1:], base_power=powers[i][2])
            current_powers = current_powers + returned[0]
            i = i + returned[1] + 2

        elif powers[i][1] == ')':
            # Go back to the function that called this if there's a closing bracket.
            corrected = []
            for current_power in current_powers:
                corrected.append((current_power[0], current_power[1], current_power[2] * powers[i][2], current_power[3]))
            return (corrected, i)
        else:
            # If it's not a bracket, then just append that element
            current_powers.append((powers[i][0], powers[i][1], powers[i][2] * base_power, powers[i][3]))
            i += 1
    return (current_powers, i)


def _find_units(powers_cleaned, dimensions, strict):
    """
    Finds the powers associated with each of the units

    :param list((chemdataextractor.quantities.Unit, str, str, str)) powers_cleaned: The units found, in the format (units found, string in which this occured, power associated with the unit, string which matched with the unit's definition)
    :param bool strict: Whether the dimensions of the results will be checked against the dimensions give.
    :returns: The units found from the list given.
    :rtype: chemdataextractor.quantities.Unit
    """
    unassociated_elements = []
    total_elements = len(powers_cleaned)
    unassociated_elements = []
    powers = {}
    for power in powers_cleaned:
        original_string = power[1]
        matched = power[3]
        # Remove the first occurence of the matched string.
        if matched is not None:
            original_string = re.sub(matched, '', original_string, 1)
        exp = 0.
        # If there's still a string left, use that to calculate the magnitude, e.g. 3 for kilo
        if original_string != '':
            for magnitude in magnitudes_dict.keys():
                for result in magnitude.scan([[original_string, 'a']]):
                    exp = magnitudes_dict[magnitude]
                    original_string = original_string.replace(result[0].text, '', 1)
        if original_string not in ['', '-']:
            unassociated_elements.append(original_string)
        # To handle cases when the units given by parsing don't match with what's expected.
        try:
            if power[0](magnitude=exp) in powers.keys():
                powers[power[0](magnitude=exp)] += power[2]
            else:
                powers[power[0](magnitude=exp)] = power[2]
        except TypeError as e:
            log.debug(e)
            powers = {}
            break
    end_unit = None
    for unit, power in powers.items():
        if end_unit is None:
            end_unit = unit ** power
        else:
            end_unit = end_unit * (unit ** power)
    if strict:
        if end_unit is not None and end_unit.dimensions == dimensions and len(unassociated_elements) == 0:
            return end_unit
        else:
            if end_unit is None:
                raise TypeError('Could not find ' + str(dimensions) + ' in given string')
            if len(unassociated_elements) != 0:
                raise TypeError('String input had extraneous elements')
            raise TypeError('Parsed with Dimensions ' + str(end_unit.dimensions) + ', expected' + str(dimensions))
    else:
        return end_unit

