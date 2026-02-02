# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import time
from datetime import timedelta
from threading import local
from typing import Final, Optional, cast

COMMON_EXECUTOR: Final[concurrent.futures.ThreadPoolExecutor] = concurrent.futures.ThreadPoolExecutor()
"""
A shared thread pool executor for concurrent tasks across the application.
"""


def sleep_for(duration: timedelta):
    """
    Sleep for the specified duration.

    Args:
        duration (timedelta): The amount of time to sleep.
    """
    time.sleep(duration.total_seconds())


class ThreadLocal[T]:
    """
    Thread-local storage for a value, with a default initializer.

    Provides per-thread storage for a value of type T, initialized with a default.
    """

    def __init__(self, default: Optional[T] = None):
        """
        Initializes the thread-local storage with a default value.

        Args:
            default (Optional[T]): The default value for each thread, None if not specified.
        """
        self._local = local()
        self._local.value = default

    def set(self, value: T) -> None:
        """
        Sets the thread-local value for the current thread.

        Args:
            value (T): The value to set for the current thread.
        """
        self._local.value = value

    def get(self) -> T:
        """
        Gets the thread-local value for the current thread.

        Returns:
            T: The value for the current thread.
        """
        return cast(T, self._local.value)
