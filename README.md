# inspect-build-time-contract

[![PyPI version](https://img.shields.io/pypi/v/inspect-build-time-contract.svg)](https://pypi.org/project/inspect-build-time-contract/)
[![Python](https://img.shields.io/pypi/pyversions/inspect-build-time-contract.svg)](https://pypi.org/project/inspect-build-time-contract/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Opt-in lint for [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) tasks: warn when a task you've declared verifiable uses a model-graded scorer where a deterministic alternative is available.

The Inspect AI [scorer documentation](https://inspect.aisi.org.uk/scorers.html) recommends "deterministic where possible, LLM where necessary." This package makes that recommendation mechanically checkable for tasks that opt in.

## Install

```bash
pip install inspect-build-time-contract
```

## Usage

```python
from inspect_ai import Task, task
from inspect_ai.scorer import match, model_graded_qa
from inspect_build_time_contract import verifiable_task

# Deterministic scorer on a verifiable task: silent.
@verifiable_task
def my_factoid_eval():
    return Task(dataset=..., scorer=match())

# Model-graded scorer on a verifiable task: WARNING at task load.
@verifiable_task
def my_judged_eval():
    return Task(dataset=..., scorer=model_graded_qa())
# WARNING:inspect_build_time_contract:Task 'my_judged_eval' is decorated with
#         @verifiable_task but its scorer is classified as 'model_graded'.
#         Consider a deterministic alternative ... or use Inspect's @task directly.

# Task with no claim about verifiability: use Inspect's @task as normal.
@task
def my_genuinely_subjective_eval():
    return Task(dataset=..., scorer=model_graded_qa())
```

## CI mode

Set `INSPECT_BUILD_TIME_CONTRACT_STRICT=1` to escalate warnings to a `RuntimeError`:

```bash
INSPECT_BUILD_TIME_CONTRACT_STRICT=1 inspect eval my_eval.py
# Warnings now raise; CI fails on contract violations.
```

## Scorer taxonomy

| Class | Inspect built-ins |
|---|---|
| `deterministic` | `match`, `includes`, `pattern`, `exact`, `f1`, `answer`, `choice`, `math` |
| `model_graded` | `model_graded_qa`, `model_graded_fact` |
| `unknown` | Any custom or third-party scorer the package doesn't recognize |

Custom scorers are classified as `"unknown"` and fire the warning. To suppress, either use Inspect's `@task` directly (you've opted out of the verifiable contract) or fork the package and add your scorer to `DETERMINISTIC_BUILTINS` / `MODEL_GRADED_BUILTINS`.

## What this is not

- It does **not** force any task to use a deterministic scorer.
- It does **not** override any existing Inspect API. `@task` continues to work exactly as before.
- It does **not** run at eval time. It's a pre-flight check at task load.

## Why this exists

I built [Jig](https://github.com/smledbetter/jig) around the idea that an LLM-eval framework should make "declare your deterministic check at build time" a first-class concept. A pre-registered N=50 study on BIRD-SQL ([results](https://github.com/smledbetter/jig/tree/main/experiments/bird_sql/results)) found a Sonnet 4.6 LLM-as-judge had a 40% false-approval rate against the deterministic execution-based scorer; a Haiku 4.5 judge had 10% false-approval rate. Even when the deterministic check is sitting right there, choosing model-graded is a measurable accuracy cost.

This extension is a small experiment in surfacing that choice at task-definition time inside Inspect AI specifically. An upstream issue proposing the taxonomy + lint as in-core features will be filed at [`UKGovernmentBEIS/inspect_ai`](https://github.com/UKGovernmentBEIS/inspect_ai/issues); this README will be updated with the link once it's open. If the upstream lands, this package will be deprecated in favor of in-core support.

## Compatibility

Tested against `inspect-ai==0.3.212`. Should work with any 0.3.200+ version. Requires Python 3.10+.

## Development

```bash
git clone https://github.com/smledbetter/inspect-build-time-contract
cd inspect-build-time-contract
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest tests/
```

## License

MIT — see [LICENSE](LICENSE).
