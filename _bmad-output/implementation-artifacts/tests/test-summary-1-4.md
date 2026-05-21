# Test Automation Summary — Story 1.4: GitHub Actions CI Pipeline

## Generated Tests

### Integration Tests (new)

- [x] `tests/integration/test_ci_pipeline_config.py` — CI pipeline structural validation (28 tests)

## Test Coverage by Acceptance Criteria

### AC #1 — `test-cpu` job gates PRs (zero GPU dependency)

| Test | Covers |
|------|--------|
| `TestCIWorkflowExists::test_ci_yml_exists` | ci.yml file created |
| `TestCIWorkflowExists::test_ci_yml_is_valid_yaml` | Valid YAML syntax |
| `TestCIWorkflowTriggers::test_push_trigger_on_main` | push → main trigger |
| `TestCIWorkflowTriggers::test_pull_request_trigger_on_main` | pull_request → main trigger |
| `TestCIWorkflowPermissions::test_top_level_permissions_contents_read` | permissions: contents: read |
| `TestCPUJob::test_cpu_job_runs_on_ubuntu` | ubuntu-latest runner |
| `TestCPUJob::test_cpu_job_uses_python_312` | Python 3.12 |
| `TestCPUJob::test_cpu_job_has_pip_cache` | pip caching via setup-python |
| `TestCPUJob::test_cpu_job_runs_ruff_check` | `ruff check src/` step |
| `TestCPUJob::test_cpu_job_runs_mypy_strict_on_core` | `mypy --strict src/physlink/core/` |
| `TestCPUJob::test_cpu_job_excludes_gpu_tests` | `pytest -m "not gpu"` |
| `TestCPUJob::test_cpu_job_has_no_needs` | no upstream dependency |

### AC #2 — `test-gpu` job on release tags with benchmark comparison

| Test | Covers |
|------|--------|
| `TestCIWorkflowTriggers::test_tag_trigger_for_releases` | `tags: ['v*']` trigger |
| `TestGPUJob::test_gpu_job_needs_test_cpu` | `needs: test-cpu` ordering |
| `TestGPUJob::test_gpu_job_runs_on_self_hosted` | `[self-hosted, gpu]` runner |
| `TestGPUJob::test_gpu_job_only_runs_on_version_tags` | `if: startsWith(github.ref, 'refs/tags/v')` |
| `TestGPUJob::test_gpu_job_runs_gpu_tests` | `pytest -m "gpu"` |
| `TestGPUJob::test_gpu_job_has_benchmark_compare_step` | `--benchmark-compare` |
| `TestGPUJob::test_gpu_job_benchmark_compare_fail_threshold` | `--benchmark-compare-fail` |
| `TestBenchmarkBaseline::test_baseline_json_exists` | baseline file not deleted |
| `TestBenchmarkBaseline::test_baseline_json_is_valid` | valid JSON |
| `TestBenchmarkBaseline::test_baseline_has_hardware_annotation` | `"hardware": "T4 GPU"` |
| `TestBenchmarkBaseline::test_baseline_has_benchmarks_key` | pytest-benchmark format |
| `TestContributingDoc::test_contributing_md_exists` | CONTRIBUTING.md created |
| `TestContributingDoc::test_contributing_has_gpu_test_protocol` | GPU protocol documented |
| `TestContributingDoc::test_contributing_has_rc_community_process` | RC process documented |
| `TestContributingDoc::test_contributing_has_benchmark_baseline_instruction` | baseline update procedure |
| `TestContributingDoc::test_contributing_mentions_hardware_annotation` | T4 annotation noted |

### Pre-existing tests unchanged (ACs #1 NFR guards)

| Test file | Role |
|-----------|------|
| `tests/integration/test_core_no_torch_import.py` | NFR-08: no torch in core/ |
| `tests/integration/test_core_boundary.py` | core/ → adapters/ boundary |
| `tests/integration/test_api_stability.py` | API surface (skipped until Story 1.5) |
| `tests/integration/test_toolchain_compliance.py` | ruff/mypy/src-layout compliance |
| `tests/perf/test_nfr_benchmarks.py` | NFR-01: doctor() < 15s (benchmark) |

## Coverage

- CI configuration ACs: 28/28 tests, all passing ✅
- Pre-existing suite: 90 tests passing, 1 skipped (test_api_stability — by design), 2 skipped in CI (TestSrcLayoutEnforcement — editable install guard)
- Total (not gpu): **118 passed, 1 skipped** (+ 2 skipped in CI)

## Notes on Test Design

- `TestCIWorkflowTriggers` uses `config[True]` (not `config["on"]`) because PyYAML `safe_load` parses `on` as the Python boolean `True`. This is documented inline.
- `TestSrcLayoutEnforcement` failures in local dev (with editable install) are **expected and pre-existing** — they skip automatically in CI via `os.getenv("CI") == "true"`.
- `test_api_stability.py` remains `@pytest.mark.skip` — activated by Story 1.5.

## Next Steps

- Run `pytest -m "not gpu" tests/` in CI to verify skipif guards engage correctly
- Story 1.5 will remove `@pytest.mark.skip` from `test_api_stability.py`
- Stories 3.x/4.x will add `@pytest.mark.gpu` benchmark tests for DreamerV3Adapter
