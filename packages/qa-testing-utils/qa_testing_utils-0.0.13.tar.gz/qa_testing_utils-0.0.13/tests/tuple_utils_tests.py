# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import attr
from hamcrest import assert_that, is_  # type: ignore
from qa_testing_utils.tuple_utils import *


def should_assert_from_tuple():
    @attr.define
    class Foo(FromTupleMixin):
        id: int
        name: str

    assert_that(str(Foo.from_tuple((1, "kuku"))),
                is_("Foo(id=1, name='kuku')"))


def should_assert_from_tuple_with_frozen_dataclass():
    import dataclasses

    @dataclasses.dataclass(frozen=True)
    class Bar(FromTupleMixin):
        x: int
        y: str
    bar = Bar.from_tuple((42, "baz"))
    assert bar.x == 42
    assert bar.y == "baz"
    assert isinstance(bar, Bar)


def should_assert_from_tuple_with_vanilla_class():
    class Baz(FromTupleMixin):
        a: int
        b: str

        def __init__(self, a: int, b: str):
            self.a = a
            self.b = b
    baz = Baz.from_tuple((7, "qux"))
    assert baz.a == 7
    assert baz.b == "qux"
    assert isinstance(baz, Baz)
