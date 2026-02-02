# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import random
from datetime import timedelta
from typing import Any, final

import attr
import pytest
from hamcrest import assert_that, is_  # type: ignore
from qa_testing_utils.exceptions import *
from qa_testing_utils.logger import *
from qa_testing_utils.logger import Context
from qa_testing_utils.thread_utils import *
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)


@final
class SelfTests(LoggerMixin):
    @classmethod
    def setup_class(cls):
        logging.getLogger(cls.__name__).debug(
            "setup_class: called once before all tests in this class")

    @classmethod
    def teardown_class(cls):
        logging.getLogger(cls.__name__).debug(
            "teardown_class: called once after all tests in this class")

    def setup_method(self, method: str):
        self.log.debug(f"before {method}")

    def teardown_method(self, method: str):
        self.log.debug(f"after {method}")

    def should_print(self):
        """Test that print statement works (placeholder/self-test)."""
        print("hello")

    @Context.traced
    def should_assert_true(self):
        """Test that a traced assertion passes (decorator coverage)."""
        assert True

    # @pytest.mark.skip
    @pytest.mark.xfail(reason="tests a known failing assertion")
    def should_fail(self):
        # NOTE: failure description is:
        # Assertion failed
        assert_that(False)

        # NOTE: failure description is:
        #     Expected: <False>
        #          but: was <True>
        # assert_that(True, is_(False))

        # while here the failure description is assert True == False
        # assert True == False

    def should_assert_equality(self):
        @attr.define
        # @dataclass -- or this one, both define eq method based on contents
        class Foo:
            value: Any

        assert_that(Foo("something"), is_(Foo("something")))

    def should_assert_defaults(self):
        @attr.define
        class Foo:
            id: int
            mandatory: str
            name: str = attr.ib(default="kuku")

        assert_that(Foo(id=1, mandatory="present").__str__(),
                    is_("Foo(id=1, mandatory='present', name='kuku')"))

    def should_retry(self):
        """Test retry logic for a function that may fail multiple times."""
        retry_policy = retry(
            stop=stop_after_attempt(1000),
            wait=wait_fixed(timedelta(milliseconds=1)),
            retry=retry_if_exception_type(TestException),
            before_sleep=before_sleep_log(self.log, logging.DEBUG)
        )

        @retry_policy
        def do_something_unreliable():
            if random.randint(0, 10) > 5:
                raise TestException("failed")
            else:
                return "ok"

        do_something_unreliable()
