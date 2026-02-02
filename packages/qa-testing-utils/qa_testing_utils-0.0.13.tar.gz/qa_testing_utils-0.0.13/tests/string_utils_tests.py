# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import logging
from enum import Enum
from typing import List

from qa_testing_utils.string_utils import *


class Status(Enum):
    OK = 0


@to_string(show_static=True)
class Bar:
    name: str = "bar"


@to_string(show_static=True)
class Baz:
    bar: Bar = Bar()


@to_string(show_static=True)
class Foo:
    baz: Baz = Baz()


@to_string(show_static=True, depth=3)
class Goo(Foo):
    name: str = "goo"
    _status: Status = Status.OK
    strings: List[str] = ["abc", "def"]

    @property
    def status(self) -> Status:
        return self._status


def should_render_object():
    logging.getLogger(__name__).debug(">>>" + str(Goo()))
