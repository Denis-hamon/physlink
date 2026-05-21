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
