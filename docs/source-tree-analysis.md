# PhysLink — Source Tree Analysis

## Repository Overview

| Field | Value |
|-------|-------|
| Type | Monolith (single Python library) |
| Layout | `src/` layout (PEP 517) |
| Entry point | `src/physlink/__init__.py` |
| Public package | `physlink` (7 exported symbols) |
| Distributed as | `physlink-0.1.2-py3-none-any.whl` |

---

## Annotated Directory Tree

```
physlink/                              ← project root
│
├── src/
│   └── physlink/                      ← installable package root
│       ├── __init__.py                ← public API: 7 symbols exported in __all__
│       │                                (doctor, ObservationSpace, ActionSpace,
│       │                                 DreamerV3Adapter, register_invariant,
│       │                                 ComplianceReport, PhysLinkError)
│       │
│       ├── core/                      ← pure Python; zero ML imports at module level
│       │   ├── __init__.py
│       │   ├── exceptions.py          ← PhysLinkError hierarchy (6 classes)
│       │   │                            All messages follow Got/Expected/Fix template
│       │   ├── spaces.py              ← ObservationSpace, ActionSpace
│       │   │                            Factory classmethods, validate-on-construction
│       │   ├── _types.py              ← TrajectoryBatch, TrajectoryBuffer,
│       │   │                            AdaptationConfig (frozen), AdaptationRun
│       │   ├── adapter.py             ← BaseAdapter ABC
│       │   │                            Defines fit(), visualize(), export(), explain()
│       │   └── validation.py          ← register_invariant(), ComplianceReport
│       │                                Invariant system with hard/soft modes
│       │
│       ├── adapters/                  ← backend-specific; torch imported lazily inside fns
│       │   ├── __init__.py
│       │   └── dreamer.py             ← DreamerV3Adapter (main implementation)
│       │                                WorldModel + Actor + Critic (PyTorch nn.Module)
│       │                                Rich progress bar, debug panel, checkpointing
│       │
│       └── utils/                     ← standalone; ML deps imported lazily
│           ├── __init__.py
│           ├── diagnostics.py         ← doctor() — 5-check Go/No-Go diagnostic
│           │                            Zero torch dependency at import time
│           └── visualization.py       ← render_triptych() → 3-panel GIF
│
├── tests/
│   ├── conftest.py                    ← synthetic_trajectories fixture (1000 dicts, seed 42)
│   ├── unit/
│   │   ├── core/
│   │   │   ├── test_exceptions.py
│   │   │   ├── test_spaces.py
│   │   │   ├── test_types.py
│   │   │   └── test_validation.py
│   │   ├── adapters/
│   │   │   ├── test_dreamer_cpu.py    ← no GPU marker
│   │   │   └── test_dreamer_gpu.py    ← @pytest.mark.gpu
│   │   ├── utils/
│   │   │   ├── test_diagnostics.py
│   │   │   └── test_visualization.py
│   │   └── test_package_scaffold.py   ← verifies __all__, version, importability
│   ├── integration/                   ← cross-layer; validates contracts & infra
│   │   ├── test_api_stability.py
│   │   ├── test_changelog_content.py
│   │   ├── test_ci_pipeline_config.py
│   │   ├── test_core_boundary.py      ← asserts core/ has no torch import
│   │   ├── test_core_no_torch_import.py
│   │   ├── test_docs_infrastructure.py
│   │   ├── test_docstring_completeness.py
│   │   ├── test_domain_scientist_notebook.py
│   │   ├── test_domain_scientists_page.py
│   │   ├── test_github_templates.py
│   │   ├── test_lab_adoption_guide.py
│   │   ├── test_publish_workflow_config.py
│   │   ├── test_readme_content.py
│   │   ├── test_readme_domain_scientist_link.py
│   │   └── test_toolchain_compliance.py
│   └── perf/
│       ├── test_nfr_benchmarks.py     ← pytest-benchmark suite
│       └── baselines/
│           └── benchmark_baseline.json ← T4 GPU baseline (must preserve "hardware": "T4 GPU")
│
├── docs/                              ← MkDocs source + AI dev context
│   ├── index.md                       ← MkDocs home + AI master index
│   ├── getting-started.md             ← User-facing quickstart
│   ├── domain-scientists.md           ← Domain scientist guide (physical invariants)
│   ├── lab-adoption-guide.md          ← Institutional evaluation guide
│   ├── changelog.md                   ← Keep-a-Changelog format
│   ├── api/
│   │   └── index.md                   ← API reference (mkdocstrings)
│   ├── architecture.md                ← [AI context] Full architecture document
│   ├── source-tree-analysis.md        ← [AI context] This file
│   ├── development-guide.md           ← [AI context] Dev setup and workflow
│   ├── deployment-guide.md            ← [AI context] Release and CI/CD
│   └── contribution-guide.md          ← [AI context] Contribution process
│
├── notebooks/
│   ├── quickstart.ipynb               ← Colab quick-start (pinned to release version)
│   └── domain-scientist-colab.ipynb   ← Domain scientist CFD walkthrough
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                     ← test-cpu + docs + test-gpu jobs
│   │   ├── docs.yml                   ← MkDocs deploy to GitHub Pages
│   │   └── publish.yml                ← PyPI OIDC publish on tag
│   ├── ISSUE_TEMPLATE/                ← GitHub issue templates
│   └── PULL_REQUEST_TEMPLATE.md       ← GitHub PR template
│
├── physlink_checkpoints/              ← Default checkpoint output directory (gitignored)
│   └── checkpoint_step_N.safetensors
│
├── dist/                              ← Built wheel + sdist (gitignored)
│   ├── physlink-0.1.2-py3-none-any.whl
│   └── physlink-0.1.2.tar.gz
│
├── site/                              ← MkDocs built output (gitignored)
│
├── .venv/                             ← Virtual environment (gitignored)
│
├── pyproject.toml                     ← Project metadata, deps, tool config
├── mkdocs.yml                         ← MkDocs site configuration
├── uv.lock                            ← Locked dependency versions
├── .pre-commit-config.yaml            ← ruff hook (v0.4.10, pinned)
├── README.md                          ← Project README with badges
├── CONTRIBUTING.md                    ← GPU test protocol, release process
├── CHANGELOG.md                       ← Version history (Keep a Changelog)
└── LICENSE                            ← MIT
```

---

## Critical Folders

| Folder | Purpose | AI Context Notes |
|--------|---------|-----------------|
| `src/physlink/core/` | Pure Python foundation — no ML deps | The safest place to add new features without breaking the zero-torch constraint |
| `src/physlink/adapters/` | Backend integrations | Each adapter must implement BaseAdapter ABC; torch imports must stay inside function bodies |
| `src/physlink/utils/` | Standalone utilities | Same lazy-import rule as adapters |
| `tests/unit/core/` | Unit tests for core | mypy strict; no mocks allowed |
| `tests/integration/` | Contract enforcement | Many tests check file content (README, CHANGELOG, docs) — update when docs change |
| `docs/` | MkDocs source | User-facing docs and AI dev context coexist here |
| `.github/workflows/` | CI/CD | 3 workflows: ci (test+lint), docs (build), publish (PyPI) |

---

## Entry Points

| Symbol | Path | Import |
|--------|------|--------|
| `physlink.doctor` | `utils/diagnostics.py:doctor` | `from physlink import doctor` |
| `physlink.ObservationSpace` | `core/spaces.py:ObservationSpace` | `from physlink import ObservationSpace` |
| `physlink.ActionSpace` | `core/spaces.py:ActionSpace` | `from physlink import ActionSpace` |
| `physlink.DreamerV3Adapter` | `adapters/dreamer.py:DreamerV3Adapter` | `from physlink import DreamerV3Adapter` |
| `physlink.register_invariant` | `core/validation.py:register_invariant` | `from physlink import register_invariant` |
| `physlink.ComplianceReport` | `core/validation.py:ComplianceReport` | `from physlink import ComplianceReport` |
| `physlink.PhysLinkError` | `core/exceptions.py:PhysLinkError` | `from physlink import PhysLinkError` |

Advanced types (not in `__all__`):

| Symbol | Path | Import |
|--------|------|--------|
| `TrajectoryBatch` | `core/_types.py` | `from physlink.core._types import TrajectoryBatch` |
| `TrajectoryBuffer` | `core/_types.py` | `from physlink.core._types import TrajectoryBuffer` |
| `AdaptationConfig` | `core/_types.py` | `from physlink.core._types import AdaptationConfig` |
| `AdaptationRun` | `core/_types.py` | `from physlink.core._types import AdaptationRun` |
| `BaseAdapter` | `core/adapter.py` | `from physlink.core.adapter import BaseAdapter` |
