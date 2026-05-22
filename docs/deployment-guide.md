# PhysLink — Deployment Guide

## Release Process

### Prerequisites

Before the first release: configure a PyPI OIDC Trusted Publisher (see `CONTRIBUTING.md`).

### Standard Release Steps

1. **Update notebook version pin**  
   In `notebooks/quickstart.ipynb` cell 1, set:
   ```
   !pip install physlink==X.Y.Z
   ```

2. **Update version in `pyproject.toml`**
   ```toml
   [project]
   version = "X.Y.Z"
   ```

3. **Update `CHANGELOG.md`**  
   Add entry: `## [X.Y.Z] - YYYY-MM-DD`

4. **Commit changes**
   ```bash
   git commit -m "chore: release vX.Y.Z"
   ```

5. **Push tag** — this triggers the publish pipeline
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

**Important**: ensure `test-cpu` CI passes on the release commit before pushing the tag.

---

## CI/CD Pipelines

### `ci.yml` — Continuous Integration

Triggered on: `push` to `main`, `pull_request` to `main`, any `v*` tag.

**`test-cpu` job** (ubuntu-latest, Python 3.12):
```
actions/checkout@v4
actions/setup-python@v5
pip install -e ".[dev]"
ruff check src/
mypy --strict src/physlink/core/
pytest -m "not gpu" tests/ -v
```

**`docs` job** (ubuntu-latest, Python 3.12):
```
pip install -e ".[docs]"
mkdocs build --strict
```

**`test-gpu` job** (self-hosted T4, release tags only, requires `test-cpu`):
```
pip install -e ".[dev]"
pip install torch --extra-index-url https://download.pytorch.org/whl/cu121
pytest -m "gpu" tests/ -v
pytest tests/perf/ --benchmark-compare=tests/perf/baselines/benchmark_baseline.json \
  --benchmark-compare-fail=min:10%
```

### `publish.yml` — PyPI Publication

Triggered on: `v*` tag push.  
Permissions: `contents: read`, `id-token: write` (OIDC).  
Environment: `pypi` (linked to PyPI Trusted Publisher).

Steps:
1. Validate `notebooks/quickstart.ipynb` contains `pip install physlink=={tag_version}`
2. `pip install build`
3. `python -m build`
4. `pypa/gh-action-pypi-publish@release/v1` (OIDC — no stored credentials)
5. Smoke test: `pip install "physlink=={version}"` + import check for `doctor` and `PhysLinkError`

### `docs.yml` — GitHub Pages Deployment

Deploys MkDocs site to GitHub Pages on release tags, using `mike` for versioning.

---

## Authentication

**PyPI**: OIDC Trusted Publisher configured on pypi.org. No API tokens stored. GitHub Actions generates a short-lived OIDC token; PyPI validates it automatically.  
No `TWINE_PASSWORD`, `TWINE_USERNAME`, or `PYPI_TOKEN` secrets are needed or used.

---

## GPU Testing Protocol

GPU tests run on a **self-hosted T4 runner** and are only triggered by `v*` tags.

Manual protocol (v0.1 — before self-hosted runner is available):
1. On a Colab T4 instance:
   ```bash
   git clone https://github.com/Denis-hamon/physlink.git && cd physlink
   pip install -e ".[dev]"
   pip install torch --extra-index-url https://download.pytorch.org/whl/cu121
   pytest -m "gpu" tests/ -v
   pytest tests/perf/ --benchmark-json=tests/perf/baselines/benchmark_baseline.json
   ```
2. Commit updated `benchmark_baseline.json` if benchmarks change.
3. Always preserve the `"hardware": "T4 GPU"` annotation in the baseline file.

GPU CI automation will be enabled after the first external contributor PR is merged.

---

## RC Community Process (v0.2+)

Before each minor release:
1. Publish RC tag: `vX.Y.0rc1`
2. Allow 48 hours for community testing
3. Promote to final release only if no regressions reported

---

## Infrastructure Requirements

| Component | Provider | Notes |
|-----------|---------|-------|
| Source | GitHub | `Denis-hamon/physlink` |
| PyPI | pypi.org | Trusted Publisher configured |
| Docs | GitHub Pages | Deployed via `mike` on tags |
| GPU CI | Self-hosted | T4 GPU runner (future) |
| GPU CI (v0.1) | Google Colab | Manual protocol |

---

## Build Output

```
dist/
├── physlink-X.Y.Z-py3-none-any.whl    ← pure Python wheel
└── physlink-X.Y.Z.tar.gz              ← source distribution
```

Built with `python -m build` (setuptools backend, src layout).

---

## Troubleshooting

**`publish.yml` fails at notebook validation**:  
Update `notebooks/quickstart.ipynb` cell 1 to `!pip install physlink==X.Y.Z` and commit before pushing the tag.

**`test-gpu` fails benchmark comparison**:  
The benchmark regressed by >10% vs the T4 baseline. Profile the change or update the baseline if the regression is intentional (commit new `benchmark_baseline.json` with updated measurements and the `"hardware": "T4 GPU"` annotation preserved).

**Smoke test fails** (PyPI propagation delay):  
The publish workflow waits 60 seconds after upload. If the package is still not available, re-run the workflow after a few minutes.
