# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import FrozenInstanceError, dataclass
from functools import cache

import pytest
from qa_testing_utils.object_utils import *


def should_raise_exception():
    with pytest.raises(Exception) as e:
        raise Exception("kuku")

    assert e.value.args[0] == "kuku"


def should_raise_invalid_exception():
    class Foo:
        def is_valid(self) -> bool:
            return False

    foo = Foo()
    with pytest.raises(InvalidValueException) as e:
        valid(foo)

    assert e.value.args[0] == foo


def should_enforce_immutability():
    class Foo(ImmutableMixin):
        f: int = 8

    with pytest.raises(AttributeError):
        Foo().f = 9


def should_enforce_immutability_with_dataclass():
    @dataclass(frozen=True)
    class Foo:
        f: int = 8

    with pytest.raises(FrozenInstanceError):
        # Cannot assign to attribute "f" for class "Foo"
        # "Foo" is frozen
        Foo().f = 9  # type: ignore -- f is frozen... just testing


def should_support_immutability():
    class Status(Enum):
        DEFAULT = 0
        CHANGED = 1

    class Foo():
        _status: Status = Status.DEFAULT
        f1: str = "foo"

        @property
        def status(self) -> Status:
            return self._status

        @status.setter
        def status(self, status: Status):
            self._status = status

    class Bar(Foo, WithMixin):
        f2 = "bar"

    bar = Bar()
    bar_dup_with_change = bar.with_(
        status=Status.CHANGED,
        f1="foo_changed",
        f2="bar_changed")

    assert bar.status == Status.DEFAULT
    assert bar.f1 == "foo"
    assert bar.f2 == "bar"

    assert bar_dup_with_change.status == Status.CHANGED
    assert bar_dup_with_change.f1 == "foo_changed"
    assert bar_dup_with_change.f2 == "bar_changed"


def should_be_singleton():
    class Base:
        def __init__(self):
            print("init")

    class Foo(Base):
        pass

    @cache
    class FooSingleton(Base):
        pass

    @cache
    class GooSingleton():
        def __init__(self, i: int):
            self.i = i

    class BarSingleton(metaclass=SingletonMeta):
        def __init__(self, i: int):
            self.i = i

    assert Foo() != Foo()
    assert FooSingleton() == FooSingleton()

    assert GooSingleton(1) == GooSingleton(1)
    assert GooSingleton(1) != GooSingleton(2)

    assert BarSingleton(1) == BarSingleton(2)
    assert BarSingleton(3).i == 1  # type: ignore


def should_convert_to_dict_and_flatten():
    from dataclasses import dataclass

    @dataclass
    class Address(ToDictMixin):
        city: str
        zip: int

    @dataclass
    class User(ToDictMixin):
        name: str
        age: int
        address: Address
        tags: list[str]
        meta: dict[str, int]
    user = User(
        "Alice", 30, Address("London", 12345),
        ["a", "b"],
        {"score": 10})
    # to_dict
    d = user.to_dict()
    assert d == {
        "name": "Alice",
        "age": 30,
        "address": {"city": "London", "zip": 12345},
        "tags": ["a", "b"],
        "meta": {"score": 10}
    }
    # flatten
    flat = user.flatten()
    assert flat["name"] == "Alice"
    assert flat["age"] == 30
    assert flat["address_city"] == "London"
    assert flat["address_zip"] == 12345
    assert flat["tags[0]"] == "a"
    assert flat["tags[1]"] == "b"
    assert flat["meta_score"] == 10
