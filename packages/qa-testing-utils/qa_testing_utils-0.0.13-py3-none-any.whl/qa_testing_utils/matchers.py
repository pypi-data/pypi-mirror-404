# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from datetime import date, datetime
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Union,
    cast,
    final,
    override,
)

from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.description import Description
from hamcrest.core.helpers.wrap_matcher import wrap_matcher
from hamcrest.core.matcher import Matcher
from qa_testing_utils.logger import LoggerMixin


class TracingMatcher[T](BaseMatcher[T], LoggerMixin):
    """
    A matcher wrapper that adds debug logging around another matcher.

    Logs the result of each match attempt using the class logger.

    Args:
        matcher (Matcher[T]): The matcher to wrap and trace.
    """

    def __init__(self, matcher: Matcher[T]) -> None:
        self._matcher = matcher

    def _matches(self, item: Any) -> bool:
        result = self._matcher.matches(item)
        self.log.debug(f"{item!r} -> {result}")
        return result

    def describe_to(self, description: Description) -> None:
        self._matcher.describe_to(description)


def tracing[T](matcher: Matcher[T]) -> TracingMatcher[T]:
    """
    Wraps a matcher with TracingMatcher to enable debug logging.

    Usage:
        assert_that(actual, traced(contains_string("hello")))

    Args:
        matcher (Matcher[T]): The matcher to wrap.
    Returns:
        TracingMatcher[T]: The wrapped matcher with tracing enabled.
    """
    return TracingMatcher(matcher)


@final
class ContainsStringIgnoringCase(BaseMatcher[str]):
    """
    Matcher that checks if a string contains a given substring, ignoring case.

    Args:
        substring (str): The substring to search for (case-insensitive).
    """

    def __init__(self, substring: str) -> None:
        self.substring: str = substring.lower()

    def _matches(self, item: Any) -> bool:
        if not isinstance(item, str):
            return False
        return self.substring in item.lower()

    def describe_to(self, description: Description) -> None:
        description.append_text(
            f"a string containing (case-insensitive) '{self.substring}'")


def contains_string_ignoring_case(substring: str) -> ContainsStringIgnoringCase:
    """
    Creates a matcher that checks if a given string contains the specified substring, ignoring case.

    Args:
        substring (str): The substring to search for within the target string, case-insensitively.

    Returns:
        ContainsStringIgnoringCase: A matcher object that evaluates whether the target string contains the specified substring, ignoring case.
    """
    return ContainsStringIgnoringCase(substring)


@final
class IsIteratorYielding[T](BaseMatcher[Iterator[T]]):
    """
    Matcher for data yielded by iterators.
    """

    def __init__(self, element_matcher: Matcher[T]) -> None:
        self.element_matcher = element_matcher

    @override
    def _matches(self, item: Iterable[T]) -> bool:
        for element in item:
            if self.element_matcher.matches(element):
                return True

        # No matching element found
        return False

    @override
    def describe_to(self, description: Description) -> None:
        description.append_text("a stream containing ") \
            .append_description_of(self.element_matcher)

# TODO IsStreamContainingEvery


@final
class IsStreamContainingEvery[T](BaseMatcher[Iterator[T]]):
    """
    Matcher to ensure every element yielded by an iterator matches a given matcher.
    """

    def __init__(self, element_matcher: Matcher[T]) -> None:
        self.element_matcher = element_matcher

    @override
    def _matches(self, item: Iterable[T]) -> bool:
        for element in item:
            if not self.element_matcher.matches(element):
                return False  # One non-matching element means failure

        # All elements matched
        return True

    @override
    def describe_to(self, description: Description) -> None:
        description.append_text("a stream where every item is ") \
            .append_description_of(self.element_matcher)


@final
class IsIteratorYieldingAll[T](BaseMatcher[Iterator[T]]):
    """
    Matcher to ensure that the iterator yields at least one instance of each specified matcher.
    """

    def __init__(self, element_matchers: List[Matcher[T]]) -> None:
        self.element_matchers = element_matchers

    @override
    def _matches(self, item: Iterable[T]) -> bool:
        unmatched_matchers = set(self.element_matchers)
        for element in item:
            unmatched_matchers = {
                m for m in unmatched_matchers if not m.matches(element)}
            if not unmatched_matchers:  # All matchers have been satisfied
                return True

        return False

    @override
    def describe_to(self, description: Description) -> None:
        description.append_text("a stream containing each of: ")
        for index, matcher in enumerate(self.element_matchers):
            if index > 0:
                description.append_text(", ")
            description.append_description_of(matcher)


type DateOrDateTime = Union[date, datetime]


@final
class IsWithinDates(BaseMatcher[DateOrDateTime]):
    def __init__(
            self, start_date: Optional[DateOrDateTime],
            end_date: Optional[DateOrDateTime]) -> None:
        self.start_date = start_date
        self.end_date = end_date

    def _matches(self, item: Optional[DateOrDateTime]) -> bool:
        if item is None:
            return False

        # Normalize item to datetime
        if not isinstance(item, datetime):
            item = datetime.combine(item, datetime.min.time())

        # Normalize start_date and end_date to datetime
        def to_datetime(value: Optional[DateOrDateTime]) -> Optional[datetime]:
            if value is None:
                return None
            return value if isinstance(
                value, datetime) else datetime.combine(
                value, datetime.min.time())

        start = to_datetime(self.start_date)
        end = to_datetime(self.end_date)

        if start and end:
            return start <= item <= end
        if start:
            return item >= start
        if end:
            return item <= end

        return False

    def describe_to(self, description: Description) -> None:
        if self.start_date is None:
            description.append_text(f"a date before {self.end_date}")
        elif self.end_date is None:
            description.append_text(f"a date after {self.start_date}")
        else:
            description.append_text(
                f"a date within {self.start_date} and {self.end_date}")


def within_dates(
        start_date: Optional[DateOrDateTime],
        end_date: Optional[DateOrDateTime]) -> IsWithinDates:
    """
    Creates an instance of IsWithinDates to check if a date or datetime value falls within the specified start and end dates.

    Args:
        start_date (Optional[DateOrDateTime]): The start of the date range. Can be None to indicate no lower bound.
        end_date (Optional[DateOrDateTime]): The end of the date range. Can be None to indicate no upper bound.

    Returns:
        IsWithinDates: An instance configured with the provided start and end dates.
    """
    return IsWithinDates(start_date, end_date)


def yields_item[T](match: Union[Matcher[T], T]) -> Matcher[Iterator[T]]:
    """
    Matches if any element of yielded by iterator matches a given matcher.

    :param match: The matcher to satisfy, or an expected value for
        :py:func:`~hamcrest.core.core.isequal.equal_to` matching.

    This matcher iterates the evaluated iterator, searching for any element
    that satisfies a given matcher. If a matching element is found,
    ``has_item`` is satisfied.

    If the ``match`` argument is not a matcher, it is implicitly wrapped in an
    :py:func:`~hamcrest.core.core.isequal.equal_to` matcher to check for
    equality.
    """
    return IsIteratorYielding(wrap_matcher(match))


def yields_every[T](match: Union[Matcher[T], T]) -> Matcher[Iterator[T]]:
    """
    Matches if every element yielded by the iterator matches a given matcher.

    :param match: The matcher to satisfy, or an expected value for equality matching.

    This matcher iterates through the evaluated iterator, checking that every
    element satisfies the given matcher. If any element does not match, the matcher fails.

    If the `match` argument is not a matcher, it is implicitly wrapped in an
    equality matcher.
    """
    return IsStreamContainingEvery(wrap_matcher(match))


def yields_items[T](matches: Iterable[Union[Matcher[T],
                                            T]]) -> Matcher[Iterator[T]]:
    """
    Matches if each specified item is yielded at least once by the iterator.

    :param matches: An iterable of matchers or values, each of which should be yielded
                    at least once in the iterator for this matcher to succeed.

    This matcher will iterate through the evaluated iterator and check if it yields
    at least one instance of each specified matcher or value.
    """
    return IsIteratorYieldingAll([wrap_matcher(match) for match in matches])


def adapted_object[T, R](
        converter: Callable[[T], R],
        matcher: Matcher[R]) -> Matcher[T]:
    """
    Hamcrest matcher adapting an object of type T by specified converter and
    applying specified matcher. For example::

        adapt_object( lambda message: message.id,
                    is_greater_than(0) )

    where id being a number, and is_greater_than being a matcher that can be
    applied on numbers.

    See more on `PyHamcrest <https://github.com/hamcrest/PyHamcrest>`

    Args:
        converter (Callable[[T], R]): function converting T into R
        matcher (Matcher[R]): matcher for adapted type R

    Returns:
        Matcher[T]: matcher for target type T
    """
    @final
    class AdaptedMatcher(BaseMatcher[T]):
        @override
        def _matches(self, item: T) -> bool:
            return False if item is None \
                else matcher.matches(converter(item))

        @override
        def describe_to(self, description: Description) -> None:
            description.append_description_of(matcher)

    return AdaptedMatcher()


def adapted_sequence[T, R](
        converter: Callable[[T], R],
        matcher: Matcher[Sequence[R]]) -> Matcher[Sequence[T]]:
    """
    Hamcrest matcher adapting a Sequence of type T by specified converter and
    applying specified matcher. For example::

        adapt_sequence( lambda message: message.id,
                    has_item(is_greater_than(0)) )

    where id being a number, and is_greater_than being a matcher that can be
    applied on numbers.

    See more on `PyHamcrest <https://github.com/hamcrest/PyHamcrest>`

    Args:
        converter (Callable[[T], R]): function converting T into R
        matcher (Matcher[Sequence[R]): matcher for adapted Sequence of R

    Returns:
        Matcher[Sequence[T]]: matcher for target Sequence of type T
    """
    @final
    class AdaptedMatcher(BaseMatcher[Sequence[T]]):
        @override
        def _matches(self, item: Sequence[T]) -> bool:
            return matcher.matches([converter(x) for x in item])

        @override
        def describe_to(self, description: Description) -> None:
            description.append_description_of(matcher)

    return AdaptedMatcher()


def adapted_iterator[T, R](
        converter: Callable[[T], R],
        matcher: Matcher[Iterator[R]]) -> Matcher[Iterator[T]]:
    """
    Hamcrest matcher adapting an Iterator of type T by specified converter and
    applying specified matcher. For example::

        adapt_iterator( lambda message: message.id,
                    yields_item(is_greater_than(0)) )

    where id being a number, and is_greater_than being a matcher that can be
    applied on numbers.

    See more on `PyHamcrest <https://github.com/hamcrest/PyHamcrest>`

    Args:
        converter (Callable[[T], R]): function converting T into R
        matcher (Matcher[Iterator[R]): matcher for adapted Iterator of R

    Returns:
        Matcher[Iterator[T]]: matcher for target Iterator of type T
    """
    @final
    class AdaptedMatcher(BaseMatcher[Iterator[T]]):
        @override
        def _matches(self, item: Iterable[T]) -> bool:
            return matcher.matches(map(converter, item))

        @override
        def describe_to(self, description: Description) -> None:
            description.append_description_of(matcher)

    return AdaptedMatcher()


def match_as[T](matcher: Matcher[object]) -> Matcher[T]:  # type: ignore
    """
    Utility function to cast a generic matcher to the specific type Matcher[T].

    Args:
        matcher: The original matcher that needs to be cast.

    Returns:
        A matcher cast to Matcher[T].
    """
    return cast(Matcher[T], matcher)
