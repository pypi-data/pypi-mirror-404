# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import inspect
import logging
from dataclasses import dataclass
from functools import cached_property, wraps
from typing import Callable, ClassVar, Final, ParamSpec, TypeVar, cast, final

import allure
from qa_testing_utils.object_utils import classproperty
from qa_testing_utils.string_utils import EMPTY_STRING, LF
from qa_testing_utils.thread_utils import ThreadLocal

_P = ParamSpec('_P')
_R = TypeVar('_R')


@dataclass
@final
class Context:
    """Per-thread context for reporting and logging, allowing dynamic formatting of messages."""
    _THREAD_LOCAL: ClassVar[ThreadLocal['Context']]
    _formatter: Final[Callable[[str], str]]

    @classmethod
    def default(cls) -> "Context":
        """
        Returns a default Context instance with a no-op formatter.

        Returns:
            Context: A Context instance with the identity formatter.
        """
        return cls(lambda _: _)  # no formatter

    @classproperty
    def _format(cls) -> Callable[[str], str]:
        return cls._THREAD_LOCAL.get()._formatter

    @classmethod
    def set(cls, context_fn: Callable[[str], str]) -> None:
        """Sets per-thread context function to be used for formatting report and log messages."""
        cls._THREAD_LOCAL.set(Context(context_fn))

    @classmethod
    def traced(cls, func: Callable[_P, _R]) -> Callable[_P, _R]:
        """
        Decorator to log function entry, arguments, and return value at DEBUG level.

        Also adds an Allure step for reporting. Use on methods where tracing is useful
        for debugging or reporting.

        Example:
            @Context.traced
            def my_method(self, x):
                ...

        Args:
            func (Callable[P, R]): The function to be decorated.
            *args (Any): Positional arguments to be passed to the function.
            **kwargs (Any): Keyword arguments to be passed to the function.

        Returns:
            Callable[P, R]: The result of the function call.
        """
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            # NOTE: each time a decorated function is called this logic will be
            # re-evaluated.
            signature = inspect.signature(func)
            parameters = list(signature.parameters.keys())

            if parameters and parameters[0] == 'self' and len(args) > 0:
                instance = args[0]
                logger = logging.getLogger(f"{instance.__class__.__name__}")
                logger.debug(f">>> "
                             + cls._format(
                                 f"{func.__name__} "
                                 f"{", ".join([str(arg) for arg in args[1:]])} "
                                 f"{LF.join(
                                     f"{key}={str(value)}"
                                     for key, value in kwargs.items()) if kwargs else EMPTY_STRING}"))

                with allure.step(  # type: ignore
                    cls._format(
                        f"{func.__name__} "
                        f"{', '.join([str(arg) for arg in args[1:]])}")):
                    result = func(*args, **kwargs)

                if result == instance:
                    logger.debug(f"<<< " + cls._format(f"{func.__name__}"))
                else:
                    logger.debug(
                        f"<<< " + cls._format(f"{func.__name__} {result}"))

                return result
            else:
                logger = logging.getLogger(func.__name__)
                logger.debug(f">>> {func.__name__} {args} {kwargs}")
                result = func(*args, **kwargs)
                logger.debug(f"<<< {func.__name__} {result}")
                return result

        return wrapper


# NOTE: python does not support static initializers, so we init here.
Context._THREAD_LOCAL = ThreadLocal(Context.default())  # type: ignore


def trace[T](value: T) -> T:
    """Logs at debug level using the invoking module name as the logger."""
    frame = inspect.currentframe()
    try:
        if frame is not None:
            caller_frame = frame.f_back
            if caller_frame is not None:
                caller_module = inspect.getmodule(caller_frame)
                logger_name = caller_module.__name__ if caller_module else '__main__'
                logger = logging.getLogger(logger_name)
                logger.debug(f"=== {value}")
            else:
                logging.getLogger(__name__).debug(f"=== {value}")
        else:
            logging.getLogger(__name__).debug(f"=== {value}")
    finally:
        del frame

    return value


def logger[T:type](cls: T) -> T:
    """
    Class decorator that injects a logger into the decorated class.

    Adds a `log` property to the class, providing a logger named after the class.
    Useful for adding logging to any class without boilerplate.

    Args:
        cls (type): The class to decorate.

    Returns:
        type: The decorated class with a `log` property.
    """
    cls._logger = logging.getLogger(cls.__name__)

    @property
    def log(self: T) -> logging.Logger:
        return cast(logging.Logger, getattr(self, '_logger', None))

    cls.log = log

    return cls


class LoggerMixin:
    """
    Mixin that provides a `log` property for convenient class-based logging.

    Inherit from this mixin to get a `self.log` logger named after the class.
    Useful for adding debug/info/error logging to any class without boilerplate.

    Example:
        class MyClass(LoggerMixin):
            def do_something(self):
                self.log.info("Doing something")
    """
    @final
    @cached_property
    def log(self) -> logging.Logger:
        """
        Returns a logger named after the class.

        Returns:
            logging.Logger: The logger instance for this class.
        """
        return logging.getLogger(self.__class__.__name__)

    @final
    def trace[T](self, value: T) -> T:
        """
        Logs value at DEBUG level using this logger.

        Use to log something as a value, usually in a lambda expression::

            then.eventually_assert_that(
                lambda: self.trace(...call some API...),
                greater_that(0)) \
                .and_....other verifications may follow...

        Args:
            value (T): The value to log.

        Returns:
            T: The value (unchanged).
        """
        self.log.debug(f"=== {value}")
        return value
