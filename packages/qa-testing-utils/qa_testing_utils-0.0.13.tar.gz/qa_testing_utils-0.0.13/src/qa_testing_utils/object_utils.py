# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import threading
from dataclasses import asdict, fields, is_dataclass, replace
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Optional,
    Protocol,
    final,
    runtime_checkable,
)


@runtime_checkable
class Valid(Protocol):
    """
    Specifies a method for validating objects.
    """

    def is_valid(self) -> bool:
        """
        Should be implemented by objects that need validation.

        Returns:
            bool: true, if the object is valid
        """
        ...


class ImmutableMixin:
    """
    Mixin to enforce immutability after initialization.

    Overrides __setattr__ to raise AttributeError if an attribute is modified after being set.
    Intended for use with non-dataclasses. For dataclasses, use `@dataclass(frozen=True)`.

    Limitations:
        - Does not work with WithMixin if attributes have default values.
        - Does not work if applied to a superclass with a custom __init__.

    Example:
        class MyImmutable(ImmutableMixin):
            foo: int = 1
        obj = MyImmutable()
        obj.foo = 2  # Raises AttributeError
    """

    def __setattr__(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            raise AttributeError(f"Can't modify attribute '{
                                 key}' after initialization")
        super().__setattr__(key, value)  # Properly sets the attribute


class WithMixin:
    '''
    Mixin to support copy-on-change (functional update) for objects.

    Instead of mutating an object, use `with_()` to create a copy with updated fields:
        obj2 = obj.with_(field=new_value)

    Works with both plain Python classes and dataclasses.

    Example:
        @dataclass(frozen=True)
        class Point(WithMixin):
            x: int
            y: int

        p1 = Point(1, 2)
        p2 = p1.with_(x=3)  # p2 is Point(3, 2)
    '''
    @final
    def with_[T:WithMixin](self: T, **changes: Any) -> T:
        if is_dataclass(self):
            # Directly use replace for dataclasses; it will raise an error for invalid fields
            return replace(self, **changes)

        duplicated_object = self.__class__(**self.__dict__)
        for key, value in changes.items():
            # Get the current attribute to determine its type
            current_attr = getattr(self, key, None)
            if isinstance(current_attr, Enum):
                # If the current attribute is an enum,
                # convert the value to the corresponding enum
                value = current_attr.__class__(value)
            setattr(duplicated_object, key, value)
        return duplicated_object


class ToDictMixin:
    """
    Mixin to add serialization methods to dataclasses.

    Provides:
        - to_dict(): Recursively converts a dataclass (and nested dataclasses) to a dictionary.
        - flatten(): Flattens nested structure for CSV or flat serialization.

    Example:
        @dataclass
        class User(ToDictMixin):
            name: str
            age: int

        user = User("Alice", 30)
        user.to_dict()  # {'name': 'Alice', 'age': 30}
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts a dataclass instance (with nested dataclasses) to a dictionary.
        """
        from typing import cast

        def convert(value: Any) -> Any:
            if isinstance(value, ToDictMixin):
                return value.to_dict()
            elif isinstance(value, list):
                # Provide a type hint for v
                return [convert(v) for v in cast(list[Any], value)]
            elif isinstance(value, dict):
                return {k: convert(v) for k, v in value.items()}  # type: ignore
            return value

        if not is_dataclass(self):
            raise TypeError("not a dataclass instance")

        return {key: convert(value) for key, value in asdict(self).items()}

    def flatten(self, prefix: str = "") -> Dict[str, Any]:
        """
        Flattens the nested structure into a flat dictionary for CSV serialization.
        """
        flat_dict: Dict[str, Any] = {}

        def flatten_value(key: str, value: Any) -> None:
            if isinstance(value, ToDictMixin):
                # Flatten nested ToDictMixin dataclasses
                nested_flat = value.flatten(prefix=f"{key}_")
                flat_dict.update(nested_flat)
            elif isinstance(value, list):
                # Serialize lists as JSON strings or expand into multiple columns
                for idx, item in enumerate(value):  # type: ignore
                    flat_dict[f"{key}[{idx}]"] = item
            elif isinstance(value, dict):
                # Serialize dicts as JSON strings or expand into multiple columns
                for sub_key, sub_val in value.items():  # type: ignore
                    flat_dict[f"{key}_{sub_key}"] = sub_val
            else:
                # Directly add non-nested fields
                flat_dict[key] = value

        if not is_dataclass(self):
            raise TypeError("not a dataclass instance")

        for field in fields(self):
            value = getattr(self, field.name)
            flatten_value(f"{prefix}{field.name}", value)

        return flat_dict


@final
class SingletonMeta(type):
    """
    Thread-safe singleton metaclass.

    Ensures only one instance of a class exists per process.
    Use by setting `metaclass=SingletonMeta` on your class.
    """
    _instances: ClassVar[Dict[type, object]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()  # Ensure thread-safety

    def __call__(
            cls: type,
            *args: Any, **kwargs: Any) -> "SingletonBase":
        with SingletonMeta._lock:
            if cls not in SingletonMeta._instances:
                instance = super().__call__(*args, **kwargs)  # type: ignore
                SingletonMeta._instances[cls] = instance
        return SingletonMeta._instances[cls]  # type: ignore[return-value]


class SingletonBase(metaclass=SingletonMeta):
    """
    Base class for singletons using SingletonMeta.

    Inherit from this class to make your class a singleton.
    """
    pass


class InvalidValueException(ValueError):
    """
    Raised when an object fails validation via the Valid protocol.

    Example:
        if not obj.is_valid():
            raise InvalidValueException(obj)
    """
    pass


def valid[T:Valid](value: T) -> T:
    """
    Validates the specified object, assuming it supports the Valid protocol.

    Args:
        value (T:Valid): The object to validate.

    Raises:
        InvalidValueException: If the object is invalid (is_valid() returns False).

    Returns:
        T:Valid: The validated object if valid.
    """
    if value.is_valid():
        return value

    raise InvalidValueException(value)


def require_not_none[T](
        value: Optional[T],
        message: str = "Value must not be None") -> T:
    """
    Ensures that the provided value is not None.

    Args:
        value (Optional[T]): The value to check for None.
        message (str, optional): The error message to use if value is None. Defaults to "Value must not be None".

    Raises:
        ValueError: If value is None.

    Returns:
        T: The value, guaranteed to be not None.
    """
    if value is None:
        raise ValueError(message)
    return value


@final
class classproperty[T]:
    """
    Descriptor for defining class-level properties (like @property but for classes).

    Example:
        class MyClass:
            @classproperty
            def foo(cls):
                return ...
    """

    def __init__(self, fget: Callable[[Any], T]) -> None:
        self.fget = fget

    def __get__(self, instance: Any, owner: Any) -> T:
        return self.fget(owner)
