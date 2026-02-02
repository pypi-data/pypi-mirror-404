# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Iterator

"""
A generic callable type alias representing a supplier of values of type T.

A Supplier is a function that takes no arguments and returns a value of type T.
This is useful for lazy evaluation, deferred computation, or providing values on demand.

Example:
    def random_int_supplier() -> int:
        import random
        return random.randint(1, 100)

    supplier: Supplier[int] = random_int_supplier
"""
type Supplier[T] = Callable[[], T]

"""
A generic callable type alias representing a predicate (boolean-valued function) over values of type T.

A Predicate is a function that takes a single argument of type T and returns a boolean.
It is commonly used for filtering, validation, or conditional logic.

Example:
    def is_even(n: int) -> bool:
        return n % 2 == 0

    even_predicate: Predicate[int] = is_even
"""
type Predicate[T] = Callable[[T], bool]


def process_next[T](i: Iterator[T], p: Predicate[T]) -> Iterator[T]:
    """
    Processes next items per specified predicate. Useful for cases in which
    the first item in a stream decides the meaning of the rest of the items.

    Args:
        i (Iterator[T]): the iterator to process
        p (Predicate[T]): the predicate to be applied on `next(i)`

    Returns:
        Iterator[T]: the original iterator if the predicate evaluated true, \
            otherwise empty iterator
    """
    return i if p(next(i)) else iter([])
