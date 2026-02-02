# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from typing import Callable, Union

import attr
import pytest
from functional import seq
from hamcrest import is_  # type: ignore
from hamcrest import all_of, assert_that, has_item, has_property
from qa_testing_utils.matchers import *
from qa_testing_utils.object_utils import *
from qa_testing_utils.string_utils import *
from qa_testing_utils.string_utils import to_string


@to_string()
@attr.define  # provides semantic equality based on attribute values
class Foo(WithMixin):
    id: int = 8
    name: str = "kuku"


def should_match():
    # NOTE this is how a basic assertion framework would be implemented
    # luckily, we have PyHamcrest
    # https://github.com/hamcrest/PyHamcrest
    def asserter[T](actual: T, rule: Callable[[T], bool]):
        assert rule(actual)

    def is_[T](expected: T) -> Callable[[T], bool]:
        def matcher(actual: T) -> bool:
            return actual == expected
        return matcher

    def has_len(expected: int) -> Callable[[str], bool]:
        def matcher(actual: str) -> bool:
            return len(actual) == expected
        return matcher

    asserter("123456", has_len(6))
    asserter("123", is_("123"))
    # NOTE Foo is defined with semantic equality, hence this works
    asserter(Foo(), is_(Foo()))


def should_match_properties():
    assert_that(
        Foo(),
        all_of(
            has_property("id", 8),
            has_property("name", "kuku")))


def should_adapt_object():
    # NOTE: instead of assert_that(Foo().id, is_(8)), can use this:
    assert_that(Foo(), adapted_object(lambda foo: foo.id, is_(8)))


def should_have_item():
    assert_that([Foo(), Foo().with_(name="muku")],
                has_item(Foo().with_(name="muku")))


def should_adapt_sequence():
    # NOTE: instead of building full object, can adapt to specific field:
    assert_that([Foo(), Foo().with_(name="muku")],
                adapted_sequence(lambda foo: foo.name,  # type: ignore -- seq
                                 has_item(is_("muku"))))  # type: ignore -- seq


def should_match_item_in_iterator():
    assert_that(iter([Foo(), Foo().with_(name="muku")]),
                yields_item(Foo()))


def should_match_items_in_iterator():
    assert_that(iter([Foo(), Foo().with_(name="muku"), Foo().with_(
        name="kuku")]), yields_items([Foo().with_(name="muku"), Foo()]))


def should_match_all_in_iterator():
    assert_that(
        iter(
            [Foo(),
             Foo().with_(name="muku"),
             Foo().with_(name="kuku")]),
        yields_every(has_property("name")))


def should_adapt_iterator():
    assert_that(iter([Foo(), Foo().with_(name="muku")]), adapted_iterator(
        lambda foo: foo.name, yields_item(is_("muku"))))


def should_adapt_stream():
    '''
    Proves than iterators/streams are lazily consumed, in this case Foo(other)
    is not verified at all. If the items are yielded from a communication
    channel or file, it means skipping unnecessary items.
    '''
    assert_that(iter(seq([Foo(), Foo().with_(name="muku"),
                          Foo().with_(name="other")])
                     .peek(print)),   # type: ignore -- seq
                adapted_iterator(lambda foo: foo.name,  # type: ignore -- seq
                                 yields_item(is_("muku"))))


@pytest.mark.parametrize(
    "test_date, start_date, end_date",
    [
        (datetime(2023, 6, 15), datetime(2023, 1, 1), datetime(2023, 12, 31)),
        (datetime(2023, 6, 15), None, datetime(2023, 7, 1)),
        (datetime(2023, 6, 15), datetime(2023, 6, 1), None),
        (datetime(2023, 1, 1), datetime(2023, 1, 1), datetime(2023, 12, 31)),
        (datetime(2023, 12, 31), datetime(2023, 1, 1), datetime(2023, 12, 31)),
    ]
)
def should_match_within_dates(
        test_date: datetime,
        start_date: Union[datetime, None],
        end_date: Union[datetime, None]):
    assert_that(test_date, within_dates(start_date, end_date))


@pytest.mark.parametrize(
    "test_date, start_date, end_date",
    [
        (None, datetime(2023, 1, 1), datetime(2023, 12, 31)),
        (datetime(2022, 12, 31), datetime(2023, 1, 1), datetime(2023, 12, 31)),
        (datetime(2024, 1, 1), datetime(2023, 1, 1), datetime(2023, 12, 31)),
    ]
)
def should_fail_not_within_dates(
        test_date: datetime,
        start_date: Union[datetime, None],
        end_date: Union[datetime, None]):
    with pytest.raises(AssertionError):
        assert_that(test_date, within_dates(start_date, end_date))


def should_match_contains_string_ignoring_case():
    assert_that("Hello World", contains_string_ignoring_case("hello"))
    assert_that("Hello World", contains_string_ignoring_case("WORLD"))
    # Should fail if not present
    with pytest.raises(AssertionError):
        assert_that("Hello World", contains_string_ignoring_case("bye"))


def should_match_iterator_yielding():
    # Should match if any element matches
    assert_that(iter([1, 2, 3]), yields_item(2))
    # Should fail if none match
    with pytest.raises(AssertionError):
        assert_that(iter([1, 2, 3]), yields_item(5))


def should_match_stream_containing_every():
    # Should match if all elements match
    assert_that(iter([2, 2, 2]), yields_every(2))
    # Should fail if any element does not match
    with pytest.raises(AssertionError):
        assert_that(iter([2, 2, 3]), yields_every(2))


def should_match_iterator_yielding_all():
    # Should match if all specified items are yielded at least once
    assert_that(iter([1, 2, 3]), yields_items([1, 2]))
    # Should fail if any specified item is not yielded
    with pytest.raises(AssertionError):
        assert_that(iter([1, 2, 3]), yields_items([1, 4]))
