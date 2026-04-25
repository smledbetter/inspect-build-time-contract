# Changelog

All notable changes to `inspect-build-time-contract` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-25

Initial release.

### Added

- `verifiable_task` decorator wrapping Inspect's `@task` to enforce a
  deterministic-when-available scorer contract. Emits a `WARNING` at task
  load when the registered scorer is model-graded or unknown.
- `INSPECT_BUILD_TIME_CONTRACT_STRICT=1` environment variable escalates
  warnings to `RuntimeError`.
- Built-in scorer taxonomy:
  - **Deterministic:** `match`, `includes`, `pattern`, `exact`, `f1`,
    `answer`, `choice`, `math`
  - **Model-graded:** `model_graded_qa`, `model_graded_fact`
- `_scorer_verification` and `_task_verification` helpers (private but
  documented; useful for testing custom scorer detection logic).
- Tested against `inspect-ai==0.3.212`. Should work with any 0.3.200+
  version that exposes `inspect_ai._util.registry.registry_info`.
