# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

<!-- For future PRs: mark breaking changes with ⚠️ **Breaking:** followed by a > **Migration:** block.
Example:
### Changed
⚠️ **Breaking:** `DreamerV3Adapter.fit()` now returns `AdaptationRun` instead of `None`.
> **Migration:** Replace `adapter.fit(...)` with `run = adapter.fit(...)`. If you did not use the return value, no change is needed.
-->

## [0.1.3] - 2026-05-23

### Added

- `physlink.adapters.wmel_bridge.DreamerWMELAdapter` — bridge that wraps a fitted
  `DreamerV3Adapter` to satisfy the [world-model-eval-lab](https://github.com/Denis-hamon/world-model-eval-lab)
  `LeWMAdapterStub` interface. Implements random-shoot MPC in latent space via
  `encode()` / `rollout()` / `score()` / `plan()`. Requires `pip install "physlink[eval]"`.
- `examples/wmel_integration.py` — end-to-end example: synthetic data → fit adapter →
  wrap bridge → run WMEL `BenchmarkRunner`.
- `physlink[eval]` optional dependency group: installs `torch` + `wmel` from GitHub.
- `TrajectorySchema`, `TrajectoryBatch`, `TrajectoryBuffer` added to `physlink.__all__`
  (10 public symbols total, up from 7).
- `TrajectoryBatch.quality_report(schema)` — validate a batch against a `TrajectorySchema`
  and return a `TrajectoryQualityReport` with per-check results and an overall verdict.
- `ROADMAP.md` — public three-track roadmap: interface layer (complete), quality gate
  (complete), evaluation harness via WMEL bridge (complete).

## [0.1.2] - 2026-05-22

### Added

- `register_invariant(adapter, name, fn, tolerance, mode)` — attach a plain Python callable as a
  physical invariant check to a `DreamerV3Adapter`. `mode="hard"` rejects trajectories that violate
  the invariant; `mode="soft"` applies a loss penalty instead.
- `ComplianceReport` — pure data object returned by `adapter.compliance_report()`. Methods:
  - `summary()` → formatted string with pass/fail counts and overall compliance rate
  - `violations()` → list of violation records with trajectory index, residual, and cause text
  - `plot()` → matplotlib histogram of residuals (lazy import — matplotlib not required at import time)
  - `export(path)` → write a JSON compliance record suitable for audit trail and institutional review
- `TrajectoryBuffer.export(path)` — persist a trajectory dataset to disk (pickle format) to
  survive Colab session resets.
- `TrajectoryBuffer.load(path)` — reload a previously exported trajectory dataset.
- `physlink.__all__` finalized to exactly 7 symbols: `doctor`, `ObservationSpace`, `ActionSpace`,
  `DreamerV3Adapter`, `register_invariant`, `ComplianceReport`, `PhysLinkError`. This is the stable
  public API surface for the v0.1.x series.

## [0.1.1] - 2026-05-21

### Added

- `DreamerV3Adapter` — Dreamer-inspired RSSM prototype for use with `ObservationSpace`
  and `ActionSpace`. Added to `physlink.__all__` (now 5 symbols).
- `DreamerV3Adapter.fit(config)` — async training loop with rich progress bar showing step count,
  ETA, prediction health metric, and throughput (steps/s).
- `debug_hooks=True` constructor toggle — attaches per-step debug callbacks for gradient norms and
  activation statistics.
- Safetensors checkpoint auto-save at configurable intervals and automatic recovery on resume
  (`CheckpointVersionError` raised only for genuinely incompatible checkpoint schemas — not on every
  minor version mismatch).
- `DreamerV3Adapter.visualize()` — triptych GIF visualization: ground truth vs. prediction vs. delta
  rendered side-by-side.
- `DreamerV3Adapter.export()` — export trained adapter weights and metadata to a portable bundle;
  share panel included in the Colab UI via `share=True` flag.
- `AdaptationConfig` (immutable, YAML-serializable) and `AdaptationRun` (stateful run object)
  added to `physlink.core._types` as advanced API — not exported via `physlink.__all__` at this
  level, but accessible for power users as `from physlink.core._types import AdaptationConfig`.

## [0.1.0] - 2026-05-20

### Added

**Epic 1 — Installable Package & Zero-Friction Diagnostics**

- `physlink.doctor()` — environment diagnostic scan that reports Go/No-Go status in under 15 s on
  a Colab T4 GPU instance. Checks PyTorch installation, CUDA availability, and package integrity.
- `PhysLinkError` — base exception class for the physlink package, providing a structured hierarchy
  for all library-raised errors.
- GitHub Actions CI pipeline: `test-cpu` job (runs on every push/PR) and `test-gpu` job (runs on
  GPU-tagged runners; skipped with `-m not gpu` in CPU environments).
- PyPI publication via OIDC trusted publisher — no stored API tokens required.
- README shields (CI status, PyPI version, Python version, license) and dual-path action bar
  (Colab quick-start + local install).

**Epic 2 — Universal Space API**

- `ObservationSpace` — proprioception-based observation space with configurable bounds; `.explain()`
  returns a human-readable summary of the observation structure.
- `ActionSpace` — continuous action space with per-dimension bounds and dtype; `.explain()` describes
  the action semantics.
- `TrajectoryBatch` — core container type for batched trajectory data: observations, actions,
  rewards, and terminal flags stored as numpy arrays with shape validation.
- `.explain()` introspection method available on `ObservationSpace` and `ActionSpace` — returns a
  structured `Explanation` object suitable for display in notebooks and CLIs.
- MkDocs documentation site with Google-style docstrings, deployed to GitHub Pages via the `mike`
  versioning plugin.
- `physlink.__all__` = `["doctor", "ObservationSpace", "ActionSpace", "PhysLinkError"]` — the
  initial 4-symbol public API surface.

[Unreleased]: https://github.com/Denis-hamon/physlink/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/Denis-hamon/physlink/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/Denis-hamon/physlink/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Denis-hamon/physlink/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Denis-hamon/physlink/releases/tag/v0.1.0
