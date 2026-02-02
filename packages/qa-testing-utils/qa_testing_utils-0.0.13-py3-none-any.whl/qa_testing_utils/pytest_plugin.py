# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

"""
QA Testing Utils – Pytest Plugin
================================

This pytest plugin provides shared testing infrastructure for Python monorepos
or standalone projects using the `qa-testing-utils` module.

Features
---------

1. **Per-module logging configuration**:
   - During test session startup, the plugin searches for a `logging.ini` file:
     - First under `tests/**/logging.ini`
     - Then under `src/**/logging.ini`
     - Falls back to `qa-testing-utils/src/qa_testing_utils/logging.ini`
   - This enables consistent, per-module logging without requiring repeated boilerplate.

2. **Source code inclusion in test reports**:
   - Adds a `body` section to each test report with the source code of the test function
     (via `inspect.getsource()`), useful for HTML/Allure/custom reporting.

3. **Command-line config overrides** (parsed but not yet consumed):
   - Adds a `--config` option that accepts `section:key=value,...` strings.
   - Intended for runtime configuration injection (e.g., overriding .ini files or test settings).

Usage
------

1. Declare the plugin in your module's `pytest_plugins` (if not auto-loaded via PDM entry point):
   pytest_plugins = ["qa_testing_utils.pytest_plugin"]

2. Place a logging.ini file under your module's tests/ or src/ directory.
   If none is found, the fallback from qa-testing-utils will be used.

3. Run your tests, optionally with runtime overrides:

pytest --config my_section:key1=val1,key2=val2

Notes:
This plugin is designed to be generic and reusable across any module
consuming qa-testing-utils.

Compatible with VSCode gutter test launching and monorepo test execution.
"""

import inspect
import logging.config
from pathlib import Path
from typing import Final

import pytest
from qa_testing_utils.string_utils import COLON, COMMA, EQUAL

_config_overrides: Final[dict[str, dict[str, str]]] = {}


def pytest_addoption(parser: pytest.Parser) -> None:
    """Adds the `--config` command-line option for runtime config overrides."""
    parser.addoption(
        "--config",
        action="append",
        default=[],
        help="Override config values using section:key=value format, comma-separated"
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configures the pytest session, loading logging.ini and parsing config overrides."""
    from qa_testing_utils import __file__ as utils_ini

    test_args = [Path(arg.split("::")[0])
                 for arg in config.args if Path(arg.split("::")[0]).is_file()]
    root = test_args[0].parent.parent if test_args else Path.cwd()

    # Collect all logging.ini files under tests/ and src/
    logging_inis = (
        list(root.glob("tests/**/logging.ini"))
        + list(root.glob("src/**/logging.ini")))

    if logging_inis:
        # Prefer the one under tests/ if it exists
        selected_ini = logging_inis[0]
        logging.config.fileConfig(selected_ini)
        print(f"loaded logging.ini from {selected_ini}")
    else:
        fallback_ini = Path(utils_ini).parent / "logging.ini"
        logging.config.fileConfig(fallback_ini)
        print(f"loaded fallback logging.ini from {fallback_ini}")

    config_arg = config.getoption("--config")
    if config_arg:
        _parse_config_overrides(config_arg)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> pytest.TestReport:
    """Generates a test report with the source code of the test function."""
    report = pytest.TestReport.from_item_and_call(item, call)

    if call.when == "call":
        report.sections.append(('body', _get_test_body(item)))

    return report


def get_config_overrides() -> dict[str, dict[str, str]]:
    """
    Returns parsed `--config` overrides passed to pytest.
    Safe to call from anywhere (e.g., BaseConfiguration).
    """
    return _config_overrides


def _get_test_body(item: pytest.Item) -> str:
    function = getattr(item, 'function', None)
    if function is None:
        return "No function found for this test item."

    try:
        return inspect.getsource(function)
    except Exception as e:
        return f"Could not get source code: {str(e)}"


def _parse_config_overrides(config_arg: list[str]) -> None:
    global _config_overrides
    _config_overrides.clear()

    for override_str in config_arg:
        try:
            if COLON not in override_str:
                raise ValueError("missing section delimiter")

            section, keyvals_str = override_str.split(COLON, 1)
            section = section.strip()
            if not section:
                raise ValueError("section name cannot be empty")

            keyvals: dict[str, str] = {}
            for pair in keyvals_str.split(COMMA):
                if EQUAL not in pair:
                    raise ValueError(f"invalid key=value pair: '{pair}'")
                key, val = pair.split(EQUAL, 1)
                keyvals[key.strip()] = val.strip()

            _config_overrides.setdefault(section, {}).update(keyvals)

        except Exception as e:
            import warnings
            warnings.warn(
                f"invalid --config override '{override_str}': {e}",
                RuntimeWarning)
