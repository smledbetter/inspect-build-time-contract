"""inspect-build-time-contract: lint Inspect AI tasks for deterministic-when-available scorers.

See README.md for usage.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable

logger = logging.getLogger("inspect_build_time_contract")


DETERMINISTIC_BUILTINS: set[str] = {
    "match",
    "includes",
    "pattern",
    "exact",
    "f1",
    "answer",
    "choice",
    "math",
}

MODEL_GRADED_BUILTINS: set[str] = {
    "model_graded_qa",
    "model_graded_fact",
}


def _scorer_verification(scorer: Any) -> str:
    """Return 'deterministic' | 'model_graded' | 'unknown' for a single scorer.

    Uses Inspect's registry (`registry_info`) to resolve the scorer's
    registered name, since scorer factory functions return inner closures
    whose `__name__` is uninformative.
    """
    try:
        from inspect_ai._util.registry import registry_info
    except ImportError:
        return "unknown"

    try:
        info = registry_info(scorer)
    except Exception:
        return "unknown"

    name = info.name.rsplit("/", 1)[-1]

    if name in DETERMINISTIC_BUILTINS:
        return "deterministic"
    if name in MODEL_GRADED_BUILTINS:
        return "model_graded"
    return "unknown"


def _task_verification(task: Any) -> str | None:
    """Resolve the verification class of a Task's scorer(s).

    Returns:
        - "deterministic" if all scorers are deterministic
        - "model_graded" if any scorer is model-graded
        - "unknown" if any scorer cannot be classified and none are model-graded
        - None if the task has no scorer
    """
    scorers = getattr(task, "scorer", None)
    if scorers is None:
        return None

    if not isinstance(scorers, (list, tuple)):
        scorers = [scorers]

    if not scorers:
        return None

    classes = {_scorer_verification(s) for s in scorers}

    if "model_graded" in classes:
        return "model_graded"
    if "unknown" in classes:
        return "unknown"
    return "deterministic"


def _strict_mode() -> bool:
    """Strict mode: warnings become errors. Configurable via env var."""
    return os.environ.get("INSPECT_BUILD_TIME_CONTRACT_STRICT", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def verifiable_task(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator wrapping Inspect's @task to enforce a verifiable contract.

    A task wrapped with @verifiable_task is expected to use a deterministic
    scorer. If the registered scorer is model-graded (or unknown), a warning
    is emitted at task-load time. In strict mode (env var
    INSPECT_BUILD_TIME_CONTRACT_STRICT=1), the warning becomes an error.

    Use Inspect's @task directly (without this wrapper) for tasks that
    genuinely cannot be deterministically scored.
    """
    from inspect_ai import task as inspect_task

    def checked_loader(*args: Any, **kwargs: Any) -> Any:
        task_instance = fn(*args, **kwargs)
        verification = _task_verification(task_instance)

        if verification in (None, "deterministic"):
            return task_instance

        msg = (
            f"Task {fn.__name__!r} is decorated with @verifiable_task but its "
            f"scorer is classified as {verification!r}. Consider a deterministic "
            f"alternative (match, includes, pattern, exact, f1, answer, choice, "
            f"math, or a custom scorer) or use Inspect's @task directly. "
            f"(Set INSPECT_BUILD_TIME_CONTRACT_STRICT=1 to escalate to error.)"
        )

        if _strict_mode():
            raise RuntimeError(msg)
        logger.warning(msg)
        return task_instance

    checked_loader.__name__ = fn.__name__
    checked_loader.__qualname__ = getattr(fn, "__qualname__", fn.__name__)
    checked_loader.__doc__ = fn.__doc__
    checked_loader.__module__ = fn.__module__

    return inspect_task(checked_loader)


__version__ = "0.1.0"

__all__ = [
    "__version__",
    "verifiable_task",
    "DETERMINISTIC_BUILTINS",
    "MODEL_GRADED_BUILTINS",
]
