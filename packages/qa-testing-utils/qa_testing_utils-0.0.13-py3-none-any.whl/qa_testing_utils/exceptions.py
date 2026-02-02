# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

class TestException(Exception):
    """
    Marks an exception raised by tests infrastructure. Useful to differentiate
    between unexpected run-time exceptions, which should be handled as
    programming errors, and legitimate run-time exceptions such as time-out,
    not found, etc. The former might be handled via a retry mechanism.
    """
    pass
