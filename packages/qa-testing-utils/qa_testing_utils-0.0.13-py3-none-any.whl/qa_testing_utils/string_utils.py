# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Final, Literal, Type

from ppretty import ppretty  # type: ignore

EMPTY_STRING: Final[str] = ""
SPACE: Final[str] = " "
DOT: Final[str] = "."
LF: Final[str] = "\n"
COMMA: Final[str] = ","
EQUAL: Final[str] = "="
COLON: Final[str] = ":"
UTF_8: Final[str] = "utf-8"
EMPTY_BYTES: Final[Literal[b'']] = b''


def to_string[T](indent: str = '    ',
                 depth: int = 1,
                 width: int = 72,
                 seq_length: int = 15,
                 show_protected: bool = False,
                 show_private: bool = False,
                 show_static: bool = False,
                 show_properties: bool = True,
                 show_address: bool = False,
                 str_length: int = 50) -> Callable[[Type[T]], Type[T]]:
    """
    Class decorator providing a readable __str__ implementation.

    The default Python __str__ implementation, returns the type and the memory
    address of instance.

    Important for diagnostics, actually every object that is logged, must
    provide such readable __str__.

    Args:
        indent (str, optional): indentation; Defaults to '    '.
        depth (int, optional): depth in object hierarchy; defaults to 1.
        width (int, optional): width of line before line-feed; defaults to 72.
        seq_length (int, optional): how many items to include; defaults to 15.
        show_protected (bool, optional): include protected; Defaults to False.
        show_private (bool, optional): include private; defaults to False.
        show_static (bool, optional): include static; defaults to False.
        show_properties (bool, optional): include properties; defaults to True.
        show_address (bool, optional): include object's memory address; defaults to False.
        str_length (int, optional): maximum string length per item; defaults to 50.

    Returns:
        Callable[[Type[T]], Type[T]]: _description_
    """
    def decorator(cls: Type[T]) -> Type[T]:
        def __str__(self: T) -> str:
            # IMPORTANT: must not use something that calls __str__
            return ppretty(self,
                           indent=indent,
                           depth=depth,
                           width=width,
                           seq_length=seq_length,
                           show_protected=show_protected,
                           show_private=show_private,
                           show_static=show_static,
                           show_properties=show_properties,
                           show_address=show_address,
                           str_length=str_length)  # type: ignore

        cls.__str__ = __str__
        return cls

    return decorator
