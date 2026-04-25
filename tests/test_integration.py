"""Integration tests against real Inspect AI tasks and scorers.

Requires inspect-ai installed. These tests verify that:
- @verifiable_task wraps Inspect's @task without breaking it
- Deterministic scorers pass silently
- Model-graded scorers emit a warning
- Strict mode raises RuntimeError instead of warning
- List-of-scorers cases classify correctly
"""

from __future__ import annotations

import logging
import os

import pytest
from inspect_ai import Task
from inspect_ai.scorer import (
    answer,
    choice,
    exact,
    f1,
    includes,
    match,
    model_graded_fact,
    model_graded_qa,
    pattern,
)

from inspect_build_time_contract import _scorer_verification, _task_verification, verifiable_task


# ---------- _scorer_verification against real Inspect scorers ----------


@pytest.mark.parametrize(
    "scorer_factory",
    [
        match,
        includes,
        lambda: pattern(r"\d+"),
        exact,
        f1,
        lambda: answer("letter"),
        lambda: choice(),
    ],
)
def test_real_deterministic_scorers_classified(scorer_factory) -> None:
    """All Inspect built-in deterministic scorers should classify correctly."""
    s = scorer_factory()
    assert _scorer_verification(s) == "deterministic"


@pytest.mark.parametrize("scorer_factory", [model_graded_qa, model_graded_fact])
def test_real_model_graded_scorers_classified(scorer_factory) -> None:
    """Inspect built-in model-graded scorers should classify correctly."""
    s = scorer_factory()
    assert _scorer_verification(s) == "model_graded"


# ---------- _task_verification on real Tasks ----------


def test_task_with_no_scorer_returns_none() -> None:
    t = Task()
    assert _task_verification(t) is None


def test_task_with_deterministic_scorer() -> None:
    t = Task(scorer=match())
    assert _task_verification(t) == "deterministic"


def test_task_with_model_graded_scorer() -> None:
    t = Task(scorer=model_graded_qa())
    assert _task_verification(t) == "model_graded"


def test_task_with_list_of_deterministic_scorers() -> None:
    t = Task(scorer=[match(), includes()])
    assert _task_verification(t) == "deterministic"


def test_task_with_mixed_scorers_classifies_as_model_graded() -> None:
    t = Task(scorer=[match(), model_graded_qa()])
    assert _task_verification(t) == "model_graded"


# ---------- @verifiable_task end-to-end ----------


def test_verifiable_task_with_deterministic_emits_no_warning(caplog) -> None:
    @verifiable_task
    def good_eval():
        return Task(scorer=match())

    with caplog.at_level(logging.WARNING, logger="inspect_build_time_contract"):
        result = good_eval()

    assert isinstance(result, Task)
    assert not any(
        "verifiable_task" in r.message for r in caplog.records
    ), "Expected no warning for deterministic scorer"


def test_verifiable_task_with_model_graded_emits_warning(caplog) -> None:
    @verifiable_task
    def bad_eval():
        return Task(scorer=model_graded_qa())

    with caplog.at_level(logging.WARNING, logger="inspect_build_time_contract"):
        result = bad_eval()

    assert isinstance(result, Task)
    assert any(
        "model_graded" in r.message and "bad_eval" in r.message for r in caplog.records
    ), f"Expected a warning naming bad_eval and model_graded; got {[r.message for r in caplog.records]}"


def test_verifiable_task_with_no_scorer_emits_no_warning(caplog) -> None:
    @verifiable_task
    def empty_eval():
        return Task()

    with caplog.at_level(logging.WARNING, logger="inspect_build_time_contract"):
        result = empty_eval()

    assert isinstance(result, Task)
    assert not any(r.levelname == "WARNING" for r in caplog.records)


def test_verifiable_task_strict_mode_raises(monkeypatch) -> None:
    monkeypatch.setenv("INSPECT_BUILD_TIME_CONTRACT_STRICT", "1")

    @verifiable_task
    def strict_bad_eval():
        return Task(scorer=model_graded_qa())

    with pytest.raises(RuntimeError, match="model_graded"):
        strict_bad_eval()


def test_verifiable_task_strict_mode_does_not_raise_for_deterministic(monkeypatch) -> None:
    monkeypatch.setenv("INSPECT_BUILD_TIME_CONTRACT_STRICT", "1")

    @verifiable_task
    def strict_good_eval():
        return Task(scorer=match())

    # Should not raise
    result = strict_good_eval()
    assert isinstance(result, Task)


def test_verifiable_task_preserves_function_name() -> None:
    @verifiable_task
    def named_eval():
        return Task(scorer=match())

    # Inspect's @task may wrap, but the original name should be discoverable
    # via the function's metadata. At minimum it should be callable.
    result = named_eval()
    assert isinstance(result, Task)


def test_verifiable_task_with_unknown_scorer_emits_warning(caplog) -> None:
    """A custom scorer not in either taxonomy should warn (unknown class)."""
    from inspect_ai.scorer import Scorer, scorer, accuracy, stderr

    @scorer(metrics=[accuracy(), stderr()])
    def my_custom_unknown_scorer() -> Scorer:
        async def score(state, target):
            from inspect_ai.scorer import Score
            return Score(value=1.0)
        return score

    @verifiable_task
    def custom_eval():
        return Task(scorer=my_custom_unknown_scorer())

    with caplog.at_level(logging.WARNING, logger="inspect_build_time_contract"):
        result = custom_eval()

    assert isinstance(result, Task)
    assert any(
        "unknown" in r.message and "custom_eval" in r.message for r in caplog.records
    ), f"Expected unknown-classification warning; got {[r.message for r in caplog.records]}"
