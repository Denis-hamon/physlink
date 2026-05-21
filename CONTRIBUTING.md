# Contributing to PhysLink

## GPU Test Protocol (v0.1)

The `test-gpu` CI job runs on a self-hosted T4 GPU runner. In v0.1, the
maintainer runs this manually before each release:

1. Run on a Google Colab T4 instance:
   ```
   git clone https://github.com/<owner>/physlink.git && cd physlink
   pip install -e ".[dev]"
   pip install torch --extra-index-url https://download.pytorch.org/whl/cu121
   pytest -m "gpu" tests/ -v
   pytest tests/perf/ --benchmark-json=tests/perf/baselines/benchmark_baseline.json
   ```
2. Commit the updated `benchmark_baseline.json` if benchmarks change.
3. Always preserve the `"hardware": "T4 GPU"` annotation in the baseline file.

## RC Community Process (v0.2+)

Before each minor release (v0.2.0, v0.3.0, ...):
1. Publish a release candidate (RC) tag: `vX.Y.0rc1`
2. Allow 48h for community testing
3. Promote to final release only if no regressions reported

## GPU CI Automation

The `test-gpu` job will be automated after the first external contributor
PR is merged. Until then, maintainer-run Colab T4 tests are the gate.

## PyPI Publication (OIDC Trusted Publisher)

### One-Time PyPI Setup

Before the first release, configure a Trusted Publisher on PyPI:
1. Log in to pypi.org → project settings → Publishing → Add a new pending publisher
2. Enter:
   - Owner: `<github-username-or-org>`
   - Repository: `physlink`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi`
3. Create the matching GitHub Actions environment: repository Settings → Environments → New environment → name: `pypi`

No credentials are stored — PyPI validates the OIDC token from GitHub Actions automatically.

### Release Process

For each release:
1. Update `notebooks/quickstart.ipynb` cell 1 to `!pip install physlink==X.Y.Z`
2. Update `version = "X.Y.Z"` in `pyproject.toml`
3. Update `CHANGELOG.md` with the release entry (`## [X.Y.Z] - YYYY-MM-DD`)
4. Commit all changes: `git commit -m "chore: release vX.Y.Z"`
5. Push the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
6. `publish.yml` triggers automatically — notebook pin is validated, package is built and published, smoke test confirms the install works

**Important:** Ensure `test-cpu` CI passes on the release commit before pushing the tag.
