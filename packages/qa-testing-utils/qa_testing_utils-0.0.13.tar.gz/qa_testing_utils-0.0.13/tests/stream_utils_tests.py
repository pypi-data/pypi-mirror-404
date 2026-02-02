# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

# NOTE: there is another streaming library named pystreamapi.
# In contrast with pyfunctional it is type annotated.
# However, it eagerly consumes its underlying stream, defeating its purpose...
# ISSUE see https://github.com/PickwickSoft/pystreamapi/issues/94
# hence, we'll ignore type warnings:
# type: ignore

from typing import Iterator

from functional import seq
from more_itertools import peekable
from qa_testing_utils.stream_utils import *


def gen() -> Iterator[int]:
    yield -1
    for i in range(1, 4):
        print(">>")
        yield i


def should_stream0():
    '''demonstrates lazy consumption'''
    for i in gen():
        print(i)


def should_stream():
    '''lazy consumption too'''
    seq([gen()]) \
        .flat_map(lambda gen: process_next(gen, lambda i: i == -1)) \
        .map(lambda i: str(i)) \
        .for_each(print)


def should_not_stream():
    seq(process_next(gen(), lambda i: i == -2)) \
        .map(lambda i: str(i)) \
        .for_each(print)


def should_collect():
    print(seq(["a", "b", "c"])
          .fold_left("", lambda current, next: current + next))
    print(seq([b"\x00", b"\x01", b"\x02"])
          .fold_left(b"", lambda current, next: current + next))


def should_flat_map():
    class Foo:
        bars = [1, 2]

    (seq([Foo(), Foo()])
     .flat_map(lambda foo: foo.bars)
     .for_each(lambda bar: print(bar)))


def should_validate_all():
    assert (seq([True, True, True]).all())


def should_iterate_lazily():
    s = peekable(
        seq([1, 2, 3])
        .peek(lambda x: print(f">>> {x}"))
        .map(lambda x: x * 2))

    while s.peek(None) is not None:
        print(next(s))
