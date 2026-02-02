# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import logging
from random import randint
from typing import Callable

import pytest
from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def unstable_function():
    return randint(1, 3)


@pytest.mark.flaky
def should_test_unstable_function_1():
    assert unstable_function() == 1


@pytest.mark.flaky
def should_test_unstable_function_2():
    def assert_value():
        assert unstable_function() == 1

    Retrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logging.getLogger(), logging.DEBUG)
    )(lambda: assert_value())


@pytest.mark.flaky
def should_test_unstable_function_3():
    def retry_with_assertion(
            the_function: Callable[[],
                                   int],
            the_assertion: Callable[[int],
                                    bool]):
        def assert_value(
                the_function: Callable[[],
                                       int],
                the_assertion: Callable[[int],
                                        bool]):
            assert the_assertion(the_function())

        Retrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(min=1, max=10),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(logging.getLogger(), logging.DEBUG)
        )(lambda: assert_value(the_function, the_assertion))

    retry_with_assertion(lambda: unstable_function(), lambda r: r == 1)
    # ISSUE when it fails it shows unreadable message:
    # +  where False = <function should_test_unstable_function_3.<locals>.<lambda> at 0x7f45cc285a80>(1)
    # +    where 1 = <function should_test_unstable_function_3.<locals>.<lambda> at 0x7f45cc2859e0>().
    # see the matchers_tests.py for solution with PyHamcrest
