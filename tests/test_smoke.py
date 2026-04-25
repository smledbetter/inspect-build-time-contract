"""Unit tests for inspect-build-time-contract.

These exercise the helpers directly. Integration tests (real Inspect
@task decorator + warning emission + strict mode) live in test_integration.py.
"""

from __future__ import annotations

import os
from unittest import mock

import pytest

from inspect_build_time_contract import (
    DETERMINISTIC_BUILTINS,
    MODEL_GRADED_BUILTINS,
    _strict_mode,
)


def test_deterministic_builtins_taxonomy() -> None:
    """The deterministic taxonomy should match Inspect's documented scorers."""
    expected = {"match", "includes", "pattern", "exact", "f1", "answer", "choice", "math"}
    assert DETERMINISTIC_BUILTINS == expected


def test_model_graded_builtins_taxonomy() -> None:
    """The model-graded taxonomy should match Inspect's documented scorers."""
    expected = {"model_graded_qa", "model_graded_fact"}
    assert MODEL_GRADED_BUILTINS == expected


def test_taxonomies_are_disjoint() -> None:
    assert DETERMINISTIC_BUILTINS & MODEL_GRADED_BUILTINS == set()


def test_strict_mode_off_by_default() -> None:
    with mock.patch.dict(os.environ, {}, clear=True):
        assert _strict_mode() is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "TRUE", "Yes"])
def test_strict_mode_on_via_env(value: str) -> None:
    with mock.patch.dict(os.environ, {"INSPECT_BUILD_TIME_CONTRACT_STRICT": value}):
        assert _strict_mode() is True


@pytest.mark.parametrize("value", ["0", "false", "no", "", "  ", "off"])
def test_strict_mode_off_for_falsy_values(value: str) -> None:
    with mock.patch.dict(os.environ, {"INSPECT_BUILD_TIME_CONTRACT_STRICT": value}):
        assert _strict_mode() is False
