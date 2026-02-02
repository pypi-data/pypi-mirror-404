# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import functools
import logging
from typing import Any, Callable

from qa_testing_utils.stream_utils import Supplier
from returns.maybe import Maybe, Nothing, Some


def safely[T](supplier: Supplier[T]) -> Maybe[T]:
    """
    Calls a function safely, wrapping its result in Maybe, and swallowing any exceptions.
    The function should be a no-argument callable::

        safely(lambda: call_something_that_may_fail(params))

    Args:
        supplier (Supplier[T]): The supplier to be called.

    Returns:
        Maybe[T]: The result wrapped in Maybe, or Nothing if an exception occurs.
    """
    try:
        return Some(supplier())
    except Exception as e:
        logging.exception(f"Exception occurred: {e}")
        return Nothing


def swallow(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorates a function to swallow any exceptions.

    If an exception will occur, None will be returned.

    Args:
        func (Callable): the function, supplied by the run-time

    Returns:
        Callable: the decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return safely(lambda: func(*args, **kwargs)).value_or(None)

    return wrapper
