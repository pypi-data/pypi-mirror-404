# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import time
from datetime import timedelta

from qa_testing_utils.thread_utils import sleep_for


def should_sleep_for_specified_duration():
    start = time.monotonic()
    sleep_for(timedelta(milliseconds=120))
    elapsed = time.monotonic() - start
    # Allow some tolerance for timing imprecision
    assert elapsed >= 0.11
    assert elapsed < 0.5
