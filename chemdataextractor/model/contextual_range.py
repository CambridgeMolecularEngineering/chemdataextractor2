from functools import total_ordering
import numbers


@total_ordering
class ContextualRange:
    @classmethod
    def _create_with_ranges(cls, ranges):
        new_instance = cls()
        new_instance._constituent_ranges = ranges
        return new_instance

    def __init__(self):
        # Constituent ranges in form {ContextualRange instance: count}
        self._constituent_ranges = {}

    @property
    def constituent_ranges(self):
        return self._constituent_ranges if self._constituent_ranges else {self: 1}

    def __add__(self, other):
        if not isinstance(other, ContextualRange):
            raise TypeError("ContextualRanges can only be added to other ContextualRanges")
        # Handle case when it's just e.g. DocumentRange
        new_ranges = {}
        # TODO(ti250): Repeated calls to the contituent_ranges method is a little wasteful.
        # I don't think this is a performance constraint right now but it may be worth
        # having some sort of memoization (or getting the dictionary once only)
        for key in self.constituent_ranges:
            if key in other.constituent_ranges:
                new_ranges[key] = self.constituent_ranges[key] + other.constituent_ranges[key]
            else:
                new_ranges[key] = self.constituent_ranges[key]
        for key in other.constituent_ranges:
            if key not in self.constituent_ranges:
                new_ranges[key] = other.constituent_ranges[key]
        return ContextualRange._create_with_ranges(new_ranges)

    def __sub__(self, other):
        if not isinstance(other, ContextualRange):
            raise TypeError("ContextualRanges can only be subtracted from other ContextualRanges")
        negative_ranges = {}
        for key in other.constituent_ranges:
            negative_ranges[key] = -1. * other.constituent_ranges[key]
        negative_contextual_range = ContextualRange._create_with_ranges(negative_ranges)
        return self + negative_contextual_range

    def __mul__(self, other):
        if isinstance(other, ContextualRange):
            raise TypeError("Cannot multiply a ContextualRange with a ContextualRange, only numbers are supported")
        elif isinstance(other, numbers.Number):
            new_ranges = {}
            for key in self.constituent_ranges:
                new_ranges[key] = self.constituent_ranges[key] * other
            return ContextualRange._create_with_ranges(new_ranges)
        else:
            raise TypeError(f"Cannot multiply a ContextualRange with a {type(other)}, only numbers are supported.")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        # Division is implemented for weighting distances by confidence
        if isinstance(other, ContextualRange):
            raise TypeError("Cannot divide a ContextualRange with a ContextualRange, only numbers are supported")
        return self.__mul__(1. / other)

    def __rtruediv__(self, other):
        raise TypeError("Cannot divide something by a ContextualRange")

    def __hash__(self):
        string = str(self.__class__.__name__)
        return string.__hash__()

    def __eq__(self, other):
        if self._constituent_ranges:
            for key in self.constituent_ranges:
                if key in other.constituent_ranges and other.constituent_ranges[key] == self.constituent_ranges[key]:
                    pass
                else:
                    return False
        else:
            if type(self) == type(other):
                return True

    def __lt__(self, other):
        # Like comparing digits, with DocumentRange being the largest.
        ranges_by_magnitude = [DocumentRange(), SectionRange(), ParagraphRange(), SentenceRange()]
        for range_type in ranges_by_magnitude:
            self_range_count = self.constituent_ranges[range_type] if range_type in self.constituent_ranges else 0
            other_range_count = other.constituent_ranges[range_type] if range_type in other.constituent_ranges else 0
            if self_range_count < other_range_count:
                return True
            elif self_range_count > other_range_count:
                return False
        return False


# TODO(ti250): Perhaps this is nicer syntactically as ContextualRange.document?
class DocumentRange(ContextualRange):
    pass


class SectionRange(ContextualRange):
    pass


class ParagraphRange(ContextualRange):
    pass


class SentenceRange(ContextualRange):
    pass


# class _NoRange(ContextualRange):
#     pass
