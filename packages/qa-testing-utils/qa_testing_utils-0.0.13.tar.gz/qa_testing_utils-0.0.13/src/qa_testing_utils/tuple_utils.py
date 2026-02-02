# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import fields, is_dataclass, replace
from typing import Any, Self, Tuple, Type


class FromTupleMixin:
    """
    Mixin that adds a `from_tuple` class method for instantiating objects from a tuple.

    Allows creating an instance of a class (dataclass or regular class) by passing a tuple
    whose values match the order of the class fields. Works with frozen dataclasses as well.

    Example:
        @dataclass(frozen=True)
        class Point(FromTupleMixin):
            x: int
            y: int
        p = Point.from_tuple((1, 2))
    """
    @classmethod
    def from_tuple(cls: Type[Self], data: Tuple[Any, ...]) -> Self:
        """
        Instantiates the class from a tuple of values, matching the order of class fields.

        Args:
            data (Tuple[Any, ...]): Tuple of values corresponding to the class fields.
        Returns:
            Self: An instance of the class with fields set from the tuple.
        """
        if is_dataclass(cls):
            # Retrieve all fields, including inherited ones
            cls_fields = [f.name for f in fields(cls)]

            # Create a dictionary of field names to values from the tuple
            field_values = {name: value for name,
                            value in zip(cls_fields, data)}

            # Create a new instance using `__new__`
            instance = cls.__new__(cls)

            # If the dataclass is frozen, use `replace` to set the attributes
            if getattr(cls, '__dataclass_params__').frozen:
                return replace(instance, **field_values)
            else:
                # If the dataclass is not frozen, use setattr to set attributes
                for key, value in field_values.items():
                    setattr(instance, key, value)

                # Call __init__ if defined
                instance.__init__(*data)
                return instance
        else:
            # For vanilla classes, assume fields are defined in __init__
            # Using `__init__` directly as the custom initializer
            instance = cls.__new__(cls)
            for attr, value in zip(cls.__annotations__.keys(), data):
                setattr(instance, attr, value)

            # Call __init__ if it expects parameters
            instance.__init__(*data)
            return instance
