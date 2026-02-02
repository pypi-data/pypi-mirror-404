# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from functools import wraps
from typing import Callable, ParamSpec, Self, TypeVar

from qa_pytest_rabbitmq.queue_handler import to_string
from qa_testing_utils.logger import *


def should_trace():
    @to_string(show_static=True)
    class Message:
        value: str = "hello"
        id: int = 0

    @to_string()
    class Foo(LoggerMixin):
        @Context.traced
        def run(self, message: Message) -> Self:
            self.log.debug(f"{message}")
            return self

    Foo().run(Message())


# see -- https://stackoverflow.com/questions/78891660/how-to-make-python-3-12-function-decorator-preserve-signature
def should_preserve_signature():
    P = ParamSpec('P')
    R = TypeVar('R')

    def my_decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return wrapper

    @my_decorator
    def my_func(s: str):
        '''my documentation'''
        pass

    my_func("s")

    print(my_func.__name__)  # Prints: my_func
    print(my_func.__doc__)  # Prints: my documentation


def should_return_value_and_log_with_trace():
    value = trace(123)
    assert value == 123


def should_inject_logger_with_logger_decorator():
    @logger
    class Foo:
        pass
    f = Foo()
    # The logger is injected as a property, so we access it via the property
    log = getattr(f, 'log', None)
    assert log is not None
    assert isinstance(log, logging.Logger)
    assert log.name == 'Foo'


def should_provide_log_property_with_logger_mixin():
    class Bar(LoggerMixin):
        pass
    b = Bar()
    assert hasattr(b, 'log')
    assert isinstance(b.log, logging.Logger)
    assert b.log.name == 'Bar'


def should_return_value_and_log_with_logger_mixin_trace():
    class Baz(LoggerMixin):
        pass
    b = Baz()
    value = b.trace('abc')
    assert value == 'abc'


def should_log_entry_and_exit_with_traced_decorator():
    calls: list[tuple[int, int]] = []

    @Context.traced
    def foo(x: int, y: int) -> int:
        calls.append((x, y))
        return x + y
    result: int = foo(2, 3)
    assert result == 5
    assert calls == [(2, 3)]
