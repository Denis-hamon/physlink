# PhysLink — Architecture

## Executive Summary

PhysLink is a backend-agnostic Python library that connects physical simulation environments to ML frameworks. It provides a universal space API, a DreamerV3 adaptation loop, invariant validation, and environment diagnostics — all in a single `pip install physlink`.

**Version:** 0.1.2  
**Language:** Python 3.10+  
**Architecture pattern:** Layered library (core / adapters / utils)  
**Repository type:** Monolith (src layout)  
**Distribution:** PyPI wheel (`physlink-0.1.2-py3-none-any.whl`)

---

## Technology Stack

| Category | Technology | Version | Notes |
|----------|-----------|---------|-------|
| Language | Python | ≥ 3.10 | strict typing via mypy |
| Build backend | setuptools | ≥ 68 | src-layout, `find_packages(where=["src"])` |
| Dependency resolver | uv | — | lockfile at `uv.lock` |
| Core deps | numpy | ≥ 1.24 | trajectory data |
| Core deps | rich | ≥ 13.0 | progress bar, debug panel |
| Core deps | matplotlib | ≥ 3.7 | triptych GIF, compliance plot |
| Core deps | pyyaml | ≥ 6.0 | AdaptationConfig serialization |
| Core deps | safetensors | ≥ 0.4 | checkpoint storage |
| Core deps | Pillow | ≥ 9.0 | GIF rendering |
| Optional (GPU) | torch | any | DreamerV3 training; detected at runtime |
| Linter | ruff | ≥ 0.4 | E, F, W, I, N, UP, ANN, RUF rules |
| Type checker | mypy | ≥ 1.9 | strict on `core/`; relaxed on `adapters/`, `utils/` |
| Test runner | pytest | ≥ 8.0 | markers: `gpu` |
| Benchmarks | pytest-benchmark | ≥ 4.0 | baseline in `tests/perf/baselines/` |
| Pre-commit | ruff | v0.4.10 | auto-fix + format |
| Docs | mkdocs-material | ≥ 9.5 | with mkdocstrings (Google style) |
| Docs versioning | mike | ≥ 2.1 | GitHub Pages multi-version |

---

## Architecture Pattern: Layered Library

```
physlink (public API — 7 symbols)
├── core/           ← pure Python, no GPU deps at import time
│   ├── exceptions  ← PhysLinkError hierarchy
│   ├── spaces      ← ObservationSpace, ActionSpace
│   ├── _types      ← TrajectoryBatch, TrajectoryBuffer, AdaptationConfig, AdaptationRun
│   ├── adapter     ← BaseAdapter ABC
│   └── validation  ← register_invariant, ComplianceReport
├── adapters/       ← backend-specific; imports torch lazily
│   └── dreamer     ← DreamerV3Adapter
└── utils/          ← standalone utilities; lazy ML deps
    ├── diagnostics ← doctor()
    └── visualization ← render_triptych()
```

**Key invariant:** `core/` has zero ML framework imports at module level. `torch` is only imported inside function bodies in `adapters/` and `utils/`. This allows `import physlink` and `physlink.doctor()` to work even when PyTorch is not installed.

---

## Public API Surface

The stable public API for v0.1.x is exactly **7 symbols** exported from `physlink.__all__`:

| Symbol | Type | Source module | Purpose |
|--------|------|---------------|---------|
| `doctor` | function | `utils/diagnostics.py` | Go/No-Go env diagnostic |
| `ObservationSpace` | class | `core/spaces.py` | Proprioceptive obs space |
| `ActionSpace` | class | `core/spaces.py` | Continuous action space |
| `DreamerV3Adapter` | class | `adapters/dreamer.py` | DreamerV3 adaptation loop |
| `register_invariant` | function | `core/validation.py` | Attach invariant check to adapter |
| `ComplianceReport` | class | `core/validation.py` | Invariant compliance results |
| `PhysLinkError` | exception | `core/exceptions.py` | Base exception class |

Advanced types available but not in `__all__`: `AdaptationConfig`, `AdaptationRun`, `TrajectoryBatch`, `TrajectoryBuffer` (import from `physlink.core._types`).

---

## Component Deep-Dive

### `core/exceptions.py` — Exception Hierarchy

All exceptions follow the **Got/Expected/Fix** message template for human-readable, machine-parseable error context.

```
PhysLinkError (base)
├── ConfigurationError   — invalid constructor arguments
├── ValidationError      — runtime data violations
├── AdapterError         — PhysLink-managed I/O failures
└── CheckpointError      — checkpoint-related failures
    ├── CheckpointCorruptError   — malformed/unreadable file
    └── CheckpointVersionError   — incompatible physlink_version in metadata
                                   (carries .checkpoint_version and .current_version attrs)
```

### `core/spaces.py` — Space API

**Construction**: factory classmethods only (`from_proprioception`, `continuous`) — no direct constructor calls. All validation at creation time.

**ObservationSpace**:
- `from_proprioception(joints, include_velocity, clip_bounds, normalize)`
- `dims = joints * 2 if include_velocity else joints`
- `explain()` → JSON-serializable dict
- Hashable, equality-comparable

**ActionSpace**:
- `continuous(dims, bounds)` — per-dimension `(min, max)` tuples
- Validates: dims ≥ 1, len(bounds) == dims, each bound has min ≤ max
- `explain()` → JSON-serializable dict

### `core/_types.py` — Data Types

**TrajectoryBatch**: immutable container for `list[dict]` (at minimum `"obs"` and `"action"` keys). Created via `from_list()`. Supports `len()`, iteration.

**TrajectoryBuffer**: mutable, persistable. `export(path)` → pickle, `load(path)` → classmethod. `to_batch()` converts to TrajectoryBatch for `adapter.fit()`.

**AdaptationConfig** (frozen dataclass): serializable to dict/YAML/JSON. Fields: `obs_space`, `act_space`, `steps`, `checkpoint_interval_steps`, `checkpoint_dir`. Round-trips via `to_dict()` / `from_dict()` / `to_yaml()` / `from_yaml()`.

**AdaptationRun** (mutable dataclass): tracks live execution state. Fields: `config`, `current_step`, `checkpoint_paths`, `started_at`, `elapsed_seconds`.

### `core/validation.py` — Invariant System

**`register_invariant(adapter, name, fn, tolerance, mode)`**: attaches a callable `fn(trajectory: dict) -> float` to an adapter's `_invariants` list. Validated eagerly at registration (signature check via `inspect`, mode and tolerance validation).

- `mode="hard"` → filter trajectories with `fn(traj) > tolerance` from training batch
- `mode="soft"` → add `(residual - tolerance)` penalty to loss function per trajectory

**`ComplianceReport`**: pure data object (no side effects).
- `summary()` → per-invariant PASS/FAIL string
- `violations()` → sorted list of violation dicts
- `plot(title, show_threshold)` → matplotlib histogram (lazy import)
- `export(path)` → JSON file

### `adapters/dreamer.py` — DreamerV3Adapter

**Construction** (`__init__`): validates `obs_space.dims ≥ 4`, `act_space.dims ≥ 1`.  
**Model** (`_initialize_model`): 3 PyTorch `nn.Module` — `_WorldModel` (encoder + GRU + posterior + prior + decoder + reward_head), `_Actor`, `_Critic`. Hidden size = 256, latent = 256.

**`fit(trajectories, steps, checkpoint_interval_steps, debug_hooks, checkpoint_dir)`**:
1. Validates parameters
2. Resets training state (idempotent — safe to call multiple times)
3. Applies registered invariants (hard filter + soft penalty)
4. Pre-processes trajectories to tensors once
5. Training loop with Adam optimizer (lr=3e-4), mixed precision (AMP), gradient clipping (max_norm=100)
6. Saves safetensors checkpoint every `checkpoint_interval_steps`
7. Returns `AdaptationRun`

**`visualize(trajectories, output_path)`**: single-pass world model inference → triptych GIF via `render_triptych()`. Prints "Friday afternoon window" speedup vs 72h from-scratch baseline.

**`export(path)`**: copies triptych GIF, writes YAML config, writes summary.txt. Calls share panel (Colab clipboard copy or graceful fallback).

**`compliance_report()`**: reads `_invariants` + `_invariant_residuals` → `ComplianceReport`.

**Checkpoint system**:
- Save: `safetensors.save_file()` with metadata dict (`physlink_version`, `adapter_class`, `timestamp`, `checkpoint_step`)
- Load: `_check_checkpoint_metadata()` validates format and major.minor version compatibility before loading weights
- Errors: `CheckpointCorruptError` (bad file), `CheckpointVersionError` (incompatible version)

### `utils/diagnostics.py` — `doctor()`

5 sequential checks, no torch import at module level:
1. Python version ≥ 3.10
2. PyTorch presence (via `importlib.util.find_spec`)
3. CUDA availability (`torch.cuda.is_available()`)
4. VRAM (WARN if < 4 GB, OK if ≥ 4 GB)
5. Colab session detection (env var or `google.colab` import)

Returns `DiagnosticReport(checks, verdict="GO"|"NO-GO", elapsed_seconds)`. Prints formatted table to stdout. Target: < 15 s on Colab T4.

### `utils/visualization.py` — `render_triptych()`

3-panel matplotlib figure (Imagination | Real | Difference) saved as GIF via Pillow. All dims plotted as line series. Output: absolute path to saved file. From-scratch baseline constant: 72 hours (7-DOF arm, Colab T4).

---

## Data Flow

```
User data (list[dict])
    │
    ▼ TrajectoryBatch.from_list() / TrajectoryBuffer.to_batch()
TrajectoryBatch
    │
    ▼ DreamerV3Adapter._apply_invariants()
filtered TrajectoryBatch (hard-mode violations removed)
    │
    ▼ DreamerV3Adapter.fit()
AdaptationRun + checkpoint files (.safetensors)
    │
    ├── compliance_report() → ComplianceReport → summary/plot/export
    │
    └── visualize() → triptych GIF
            │
            └── export() → artifact bundle (GIF + YAML + summary.txt)
```

---

## Testing Strategy

| Suite | Location | Description |
|-------|----------|-------------|
| Unit — core | `tests/unit/core/` | exceptions, spaces, types, validation |
| Unit — adapters | `tests/unit/adapters/` | DreamerV3 CPU + GPU |
| Unit — utils | `tests/unit/utils/` | diagnostics, visualization |
| Integration | `tests/integration/` | API stability, CI config, docs infra, docstring completeness, GitHub templates, lab guide, README, toolchain compliance, domain scientist notebook |
| Performance | `tests/perf/` | NFR benchmarks vs baseline JSON |

**Markers**: `gpu` — excludes from CPU CI job. Run with `pytest -m "not gpu"` for CPU-only.

**Fixture**: `synthetic_trajectories` (conftest.py) — 1000 NumPy-only trajectories (7-dim obs, 3-dim action), seed 42.

---

## CI/CD Pipeline

```
push/PR to main ──► test-cpu job
                    ├── ruff check src/
                    ├── mypy --strict src/physlink/core/
                    └── pytest -m "not gpu" tests/ -v

push/PR to main ──► docs job
                    └── mkdocs build --strict

push tag v* ──────► test-cpu → test-gpu (self-hosted T4)
                    ├── pytest -m "gpu" tests/ -v
                    └── pytest-benchmark --compare vs baseline (fail if >10% regression)

push tag v* ──────► publish job (environment: pypi)
                    ├── validate notebook version pin
                    ├── python -m build
                    ├── pypa/gh-action-pypi-publish (OIDC — no stored token)
                    └── smoke test: pip install physlink=={version}; import check
```

---

## Key Design Decisions

**No ML deps at import time**: All torch imports are inside function bodies. `import physlink` works without PyTorch. Enables `doctor()` to diagnose missing torch.

**Factory classmethods for spaces**: Validation errors surface at construction time, not buried in training loops. `bool` check precedes `int` check in validators (bool is a subclass of int in Python).

**Idempotent `fit()`**: `_reset_training_state()` runs at every `fit()` call. Safe to call multiple times without side effects from previous runs.

**`safetensors` for checkpoints**: Safer than pickle (no arbitrary code execution). Metadata dict carries `physlink_version` for compatibility detection before loading weights.

**`Got/Expected/Fix` error messages**: Every exception carries structured context usable by both humans and automated tooling.

**`type: ignore` only in ADR-documented locations**: `adapters/` and `utils/` have relaxed mypy config (`ignore_missing_imports = true`) because PyTorch/matplotlib stubs are incomplete. `core/` is fully strict.
