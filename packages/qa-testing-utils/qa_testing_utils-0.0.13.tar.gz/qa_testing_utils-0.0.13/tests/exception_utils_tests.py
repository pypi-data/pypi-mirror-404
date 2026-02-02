# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from qa_testing_utils.exception_utils import *


def should_return_nothing_when_exception_is_raised():
    def trouble(p: Any) -> str:
        raise Exception("trouble")

    assert safely(lambda: trouble(7)).value_or("nada") == "nada"


def should_return_value_when_no_exception_occurs():
    def ok() -> int:
        return 42
    assert safely(ok).value_or(-1) == 42


def should_return_result_when_swallow_decorator_and_no_exception():
    @swallow
    def ok(x: int) -> int:
        return x * 2
    assert ok(3) == 6


def should_return_none_when_swallow_decorator_and_exception():
    @swallow
    def fail() -> None:
        raise RuntimeError("fail!")
    assert fail() is None
