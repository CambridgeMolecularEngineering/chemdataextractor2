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
import copy
from fractions import Fraction
from deprecation import deprecated

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
                  R('µ|μ|(micro)|(mu)|\u03bc', group=0): -6.,
                  R('n(ano)?', group=0): -9.,
                  R('p(ico)?', group=0): -12.}

# A regex pattern to match a number which can potentially have a decimal point and numbers after it, e.g. 123.4
_number_pattern = re.compile('(\d+\.?(?:\d+)?)')
# A regex pattern to match a number which can potentially have a decimal point and also a minus sign, e.g. -123.4
_negative_number_pattern = re.compile('(-?\d+\.?(?:\d+)?)')
# A regex pattern to match simple numbers (i.e. those without a decimal point), e.g. 123
_simple_number_pattern = re.compile('(\d+(?!\d+))')
# A regex pattern to match a number with an error attached to it, e.g. 123.4±5
_error_pattern = re.compile('(\d+\.?(?:\d+)?)|(±)')
# A regex pattern to match a potentially negative number (potentially with numbers below the decimal point) in a fraction, e.g. -123.4/5
_fraction_or_decimal_pattern = re.compile('-?\d\d*(\.\d\d*)?(/?-?\d\d*(\.\d\d*)?)?')
# A regex pattern to match a forward slash (/) that is not followed by a digit. Used to disambiguate between units to the power of fractions and
# units divided by other units.
_unit_fraction_pattern = re.compile('(/[^\d])')
# A regex pattern to match either opening or closing brackets
_brackets_pattern = re.compile('(\()|(\))')
# A regex pattern to match forward slashes
_slash_pattern = re.compile('/')
# A regex pattern to match a closing bracket
_end_bracket_pattern = re.compile('\)\w*')
# A regex pattern to match an opening bracket
_open_bracket_pattern = re.compile('/\(')
# A regex pattern to match a unit being divided by another
_division_pattern = re.compile('[/]\D*')
# A regex pattern containing all the shorthand single letter magnitude indicators, that could be misconstrued as units
_magnitude_indicators = re.compile('[pnµmTGMkc]')


def value_element(units=None):
    """
    Create a Parse element that can extract all sorts of values.
    """
    pure_number = R(r'^(([\+\-–−~∼˜]?\d+(([\.・,\d])+)?)|(\<nUm\>)|(×))+$')
    spaced_power_number = pure_number + R(r'^×$') + pure_number
    fraction = R(r'^(([\+\-–−]?\d+/\d+)|(\<nUm\>))$') | (R(r'^(([\+\-–−]?\d+)|(\<nUm\>))$') + R(r'^/$') + R(r'^((\d+)|(\<nUm\>))$')).add_action(merge)
    number = spaced_power_number | fraction | pure_number
    joined_range = R(r'^[\+\-–−~∼˜]?\d+(([\.・,\d])+)?[\-–−~∼˜]\d+(([\.・,\d])+)?$')('raw_value').add_action(merge)
    if units is not None:
        spaced_range = (number + Optional(units).hide() + (R(r'^[\-–−~∼˜]$') + number | number))('raw_value').add_action(merge)
        to_range = (number + Optional(units).hide() + I('to') + number)('raw_value').add_action(join)
    else:
        spaced_range = (number + R(r'^[\-–−~∼˜]$') + number)('raw_value').add_action(merge)
        to_range = (number + I('to') + number)('raw_value').add_action(join)
    plusminus_range = (number + R('±') + number)('raw_value').add_action(join)
    bracket_range = R('^' + _number_pattern.pattern + '\(\d+\)' + '$')('raw_value')
    spaced_bracket_range = (pure_number + W('(') + pure_number + W(')')).add_action(merge)('raw_value')
    between_range = (I('between').hide() + number + I('and') + number).add_action(join)
    value_range = (Optional(R('^[\-–−]$')) + (plusminus_range | joined_range | spaced_range | to_range | between_range | bracket_range | spaced_bracket_range))('raw_value').add_action(merge)
    value_single = (Optional(R('^[~∼˜\<\>]$')) + Optional(R('^[\-–−]$')) + number)('raw_value').add_action(merge)
    value = Optional(lbrct).hide() + (value_range | value_single)('raw_value') + Optional(rbrct).hide()
    if units is not None:
        value = value + units
    return value


@memoize
@deprecated(deprecated_in="2.1", details="Deprecated in favour of calling value_element with no arguments.")
def value_element_plain():
    return value_element()


# @memoize
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
        if hasattr(model, 'dimensions_to_look_for'):
            for dimension in model.dimensions_to_look_for:
                units_dict.update(dimension.units_dict)
        elif hasattr(model, 'dimensions') and model.dimensions.units_dict is not None:
            units_dict.update(model.dimensions.units_dict)
    if len(units_dict) == 0:
        return None
    # Case where we have a token that's just brackets
    units_regex += '(\((?!\d))|(\)|\])|\-|'
    # Handle all the units
    for element, unit in six.iteritems(units_dict):
        # if unit is not None:
        units_regex += '(' + element.pattern + ')|'
    units_regex += '(\/)'
    # Case when we have powers, or one or more units
    units_regex2 = units_regex + '|([\+\-–−]?\d+(\.\d+)?)'
    units_regex2 += '))+$'
    units_regex += '))+'
    units_regex += (units_regex2[:-2] + '*')
    units_regex = '^((?P<split>[\+\-–−]?\d+([\.\-\−]?\d+)?)|((?P<split2>.*)(\(|\/|\[)))' + units_regex
    units_regex += '$'
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
    index = 0
    while index < len(new_split_by_num):
        value = new_split_by_num[index]
        if value == '×' and index != len(new_split_by_num) - 1:
            remaining = new_split_by_num[index + 1:]
            if remaining[0] == '10':
                string_power = remaining[1]
                index += 2
            elif remaining[0][:2] == '10':
                string_power = remaining[0][2:]
                index += 1
            exponent = 10 ** float(string_power)
            values[-1] = values[-1] * exponent
        try:
            float_val = float(value)
            values.append(float_val)
        except ValueError:
            try:
                values.append(float(Fraction(value)))
            except (ValueError, ZeroDivisionError):
                pass
        index += 1
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
        split_by_num.extend([r for r in re.split(_number_pattern, elem) if r])
    split_by_num_merge_minus = []
    merge_next_in = False
    for index, value in enumerate(split_by_num):
        if value == "-" and (index == 0 or split_by_num[index - 1] == "10"):
            merge_next_in = True
        elif merge_next_in:
            split_by_num_merge_minus.append(split_by_num[index - 1] + value)
            merge_next_in = False
        else:
            split_by_num_merge_minus.append(value)

    # Merging-back fractions
    if len(split_by_num_merge_minus) == 3 and split_by_num_merge_minus[1] == '/':
        split_by_num_merge_minus = [''.join(split_by_num_merge_minus)]
    return split_by_num_merge_minus


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
    if string[0] == '[' and string[-1] == ']':
        string = string[1:-1]
    # Split string at numbers, /s, and brackets, so we have the units tokenized into the right units for later processing stages.
    try:
        split_string = _split(string)
    except IndexError as e:
        if not strict:
            return None
        else:
            raise TypeError('Failed to successfully split string: ', string)
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
    split_by_num = re.split(_simple_number_pattern, string)
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
        split = re.split(_unit_fraction_pattern, element)
        split_by_slash += split

    # Split at brackets
    split_by_bracket = []
    for element in split_by_slash:
        split = re.split(_brackets_pattern, element)
        split_by_bracket += split

    # Merge bits that were split too much
    final_list = []
    for element in split_by_bracket:
        if element is not None:
            # Merge /s with forward brackets, or text,
            # e.g. ['/', '('] -> ['/('] and ['/n', 's'] -> ['/ns']
            # Also merge numbers
            if (re.match(_fraction_or_decimal_pattern, element)
                or (final_list != [] and re.match(_division_pattern, final_list[-1])
                    and not re.match(_end_bracket_pattern, element) and not re.match(_open_bracket_pattern, final_list[-1]))
                    and not re.match(_slash_pattern, element)):
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
        # Find the potential matches for each of the units using the regex supplied by the user in units_dict
        all_results = []
        found_units = {}
        for unit in units_dict.keys():
            matches = [res for res in re.finditer(unit.pattern, element)]
            if matches is not None:
                for match in matches:
                    text = match.group(0)
                    span = match.span()
                    all_results.append((text, span[0], span[1]))
                    found_units[text] = units_dict[unit]
        # If none found, then return the original string and that no units were found.
        if len(found_units) == 0:
            units_list.append((None, element, None))
        else:
            # Filter the results to remove any overlapping ranges
            filtered_results = _remove_subranges(all_results)
            # Sort the results to make splitting the string into each unit's tokens easier
            sorted_results = sorted(filtered_results, key=lambda el: el[1])
            # Split into each unit's token
            split = []
            prev_index = 0
            for result in sorted_results:
                if prev_index != result[1]:
                    split.append(element[prev_index: result[1]])
                split.append(element[result[1]: result[2]])
                prev_index = result[2]
            if prev_index < len(element):
                split.append(element[prev_index: len(element)])

            # Iterate through the substrings to find the occurences of the units.
            # Constructs a list of tuples of (Unit, string in which the unit was found, string corresponding to the unit itself)
            # Algorithm is as follows:
            # - If the token corresponds to a unit (path 1):
            #   + Append it and its string to the units_list, (path 1a), unless
            #   + The token corresponds to the same unit as the previous token, then that probably represents a magnitude (e.g. mm),
            #     so add the string to the 'string in which the unit was found' for the previous tuple (path 1b).
            #   + The previous token is a string that can indicate magnitude, but was determined to be a unit (eg. the m in mA assigned as meters).
            #     so update the unit to contain the order and change update the unit type (path 1c).
            # - If the token's a number, it's a power of some sort, so add it to the previous tuple (path 2).
            # - Else add it to the current_string so that it's incorporated in the next unit that comes along's tuple, as it
            # represents a magnitude of some sort, e.g. kilo or mega (path 3).
            prev_unit = None
            current_string = ''
            for index, string in enumerate(split):
                if string in found_units.keys():
                    # path 1
                    if found_units[string] == prev_unit:
                        # path 1b
                        units_list[-1] = (prev_unit, units_list[-1][1] + string, units_list[-1][2])
                    elif prev_unit and re.fullmatch(_magnitude_indicators, split[index - 1]) and split[index - 1] in found_units.keys():
                        # path 1c
                        units_list[-1] = (found_units[string], units_list[-1][1] + string, string)
                    else:
                        # path 1a
                        units_list.append((found_units[string], current_string + string, string))
                    current_string = ''
                    prev_unit = found_units[string]
                elif re.match(_fraction_or_decimal_pattern, string):
                    # path 2
                    units_list[-1] = (units_list[-1][0], units_list[-1][1] + string, units_list[-1][2])
                else:
                    # path 3
                    current_string += string
                    if index == len(split) - 1:
                        units_list[-1] = (units_list[-1][0], units_list[-1][1] + current_string, units_list[-1][2])
    return units_list


def _remove_subranges(ranges):
    should_remove_indices = []
    for parent_index, parent in enumerate(ranges):
        parent_range = (parent[1], parent[2])
        for child_index, child in enumerate(ranges):
            if child_index != parent_index:
                child_range = (child[1], child[2])
                if child_range[0] >= parent_range[0] and child_range[1] <= parent_range[1]:
                    should_remove_indices.append(child_index)
    new_ranges = [original_range for index, original_range in enumerate(ranges) if index not in should_remove_indices]
    return new_ranges


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
            element = re.split(_slash_pattern, element)[1]
        # Reset base_power at end of brackets, to account for cases like K/(km/s)-1/2
        # Without this, this would be parsed as Kkm-1/2s1/2 as the base_power would carry to the
        # -1/2 after the end of the brackets
        elif element[0] == ')':
            power = 1.0
            base_power = 1.0
        # Look for strings involving numbers.
        found_power = re.search(_fraction_or_decimal_pattern, element)
        if found_power is not None:
            try:
                power = power * float(sum(Fraction(s) for s in found_power.group(0).split()))
            except ZeroDivisionError:
                return None
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


def infer_value(string, instance):
    """
    Infer the value expressed in the string. Intended to be used with :class:`~chemdataextractor.model.base.InferredProperty`.
    If one simply wishes to extract the value from a string, consider using the extract_value function instead.

    :param str string: String representation of the value
    :param BaseModel instance: The instance for which the value is being inferred.
    :returns: The value expressed as a list of floats of length 1 if the value had no range,
        and as a list of floats of length 2 if it was a range.
    :rtype: list(float)
    """
    value = None
    if string != 'NoValue' and string != '':
        try:
            value = extract_value(string)
        except (TypeError, IndexError) as e:
            log.debug(e)
    return value


def infer_error(string, instance):
    """
    Infer the error expressed in the string. Intended to be used with :class:`~chemdataextractor.model.base.InferredProperty`.
    If one simply wishes to extract the error from a string, consider using the extract_error function instead.

    :param str string: String representation of the error
    :param BaseModel instance: The instance for which the error is being inferred.
    :returns: The error expressed as a float.
    :rtype: float
    """
    error = None
    if string != 'NoValue':
        try:
            error = extract_error(string)
        except (TypeError, IndexError) as e:
            log.debug(e)
    return error


def infer_unit(string, instance):
    """
    Infer the units expressed in the string. Intended to be used with :class:`~chemdataextractor.model.base.InferredProperty`.
    If one simply wishes to extract the units from a string, consider using the extract_units function instead.

    :param str string: String representation of the units
    :param BaseModel instance: The instance for which the units are being inferred.
    :returns: The string expressed as a Unit
    :rtype: chemdataextractor.quantities.Unit
    """
    units = None
    try:
        units = extract_units(string, instance.dimensions)
    except TypeError as e:
        log.debug(e)
    return units


