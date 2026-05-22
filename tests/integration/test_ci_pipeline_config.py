"""CI pipeline configuration validation — Story 1.4.

Validates that .github/workflows/ci.yml satisfies the AC requirements
for both test-cpu and test-gpu jobs without actually running GitHub Actions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

PROJECT_ROOT = Path(__file__).parent.parent.parent
CI_YML = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
BASELINE_JSON = PROJECT_ROOT / "tests" / "perf" / "baselines" / "benchmark_baseline.json"
CONTRIBUTING_MD = PROJECT_ROOT / "CONTRIBUTING.md"


def _load_yaml(path: Path) -> dict:
    """Load a YAML file using PyYAML or pyyaml fallback."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required — run: pip install pyyaml")
    with open(path) as f:
        return yaml.safe_load(f)


class TestCIWorkflowExists:
    """AC #1/#2: the CI workflow file must exist and be valid YAML."""

    def test_ci_yml_exists(self) -> None:
        assert CI_YML.exists(), (
            f".github/workflows/ci.yml not found at {CI_YML}.\n"
            "Story 1.4 Task 1 requires creating this file."
        )

    def test_ci_yml_is_valid_yaml(self) -> None:
        config = _load_yaml(CI_YML)
        assert config, "ci.yml must not be empty"
        assert isinstance(config, dict), "ci.yml must parse as a YAML mapping"


class TestCIWorkflowTriggers:
    """AC #1: test-cpu triggers on PR and push to main; test-gpu on version tags.

    Note: PyYAML safe_load parses the 'on' key as Python True (YAML boolean).
    We access triggers via the True key.
    """

    def test_push_trigger_on_main(self) -> None:
        config = _load_yaml(CI_YML)
        # 'on' is parsed as Python True by PyYAML safe_load
        triggers = config[True]
        push = triggers["push"]
        assert "main" in push["branches"], (
            "ci.yml must trigger on push to main (AC #1 — PR gating)"
        )

    def test_pull_request_trigger_on_main(self) -> None:
        config = _load_yaml(CI_YML)
        triggers = config[True]
        pr = triggers["pull_request"]
        assert "main" in pr["branches"], (
            "ci.yml must trigger on pull_request to main (AC #1 — PR gating)"
        )

    def test_tag_trigger_for_releases(self) -> None:
        config = _load_yaml(CI_YML)
        triggers = config[True]
        push = triggers["push"]
        tags = push.get("tags", [])
        assert any(t.startswith("v") or "v*" in t for t in tags), (
            "ci.yml must trigger on version tags (v*) for test-gpu (AC #2)"
        )


class TestCIWorkflowPermissions:
    """AC #1: workflow must have minimal permissions (contents: read)."""

    def test_top_level_permissions_contents_read(self) -> None:
        config = _load_yaml(CI_YML)
        perms = config.get("permissions", {})
        assert perms.get("contents") == "read", (
            "ci.yml must set 'permissions.contents: read' at workflow scope (security hardening)"
        )


class TestCPUJob:
    """AC #1: test-cpu job runs on ubuntu-latest with correct steps."""

    def _cpu_job(self) -> dict:
        config = _load_yaml(CI_YML)
        jobs = config.get("jobs", {})
        assert "test-cpu" in jobs, "test-cpu job must be defined in ci.yml"
        return jobs["test-cpu"]

    def test_cpu_job_runs_on_ubuntu(self) -> None:
        job = self._cpu_job()
        assert job["runs-on"] == "ubuntu-latest", (
            "test-cpu must run on ubuntu-latest (zero GPU dependency, AC #1)"
        )

    def test_cpu_job_uses_python_312(self) -> None:
        job = self._cpu_job()
        steps = job["steps"]
        setup_steps = [s for s in steps if "actions/setup-python" in str(s.get("uses", ""))]
        assert setup_steps, "test-cpu must have a actions/setup-python step"
        py_version = setup_steps[0]["with"]["python-version"]
        assert py_version == "3.12", (
            f"test-cpu must use Python 3.12, got: {py_version}"
        )

    def test_cpu_job_has_pip_cache(self) -> None:
        job = self._cpu_job()
        steps = job["steps"]
        setup_steps = [s for s in steps if "actions/setup-python" in str(s.get("uses", ""))]
        assert setup_steps, "test-cpu must have actions/setup-python step"
        cache = setup_steps[0].get("with", {}).get("cache")
        assert cache == "pip", (
            "test-cpu must enable pip caching via actions/setup-python (AC #1 — Task 1)"
        )

    def test_cpu_job_runs_ruff_check(self) -> None:
        job = self._cpu_job()
        all_runs = " ".join(s.get("run", "") for s in job["steps"])
        assert "ruff check src/" in all_runs, (
            "test-cpu must run 'ruff check src/' (not --fix) — CI validates, pre-commit fixes"
        )

    def test_cpu_job_runs_mypy_strict_on_core(self) -> None:
        job = self._cpu_job()
        all_runs = " ".join(s.get("run", "") for s in job["steps"])
        assert "mypy --strict src/physlink/core/" in all_runs, (
            "test-cpu must run 'mypy --strict src/physlink/core/' (ADR-001: core/ only)"
        )

    def test_cpu_job_excludes_gpu_tests(self) -> None:
        job = self._cpu_job()
        all_runs = " ".join(s.get("run", "") for s in job["steps"])
        assert 'pytest -m "not gpu"' in all_runs or "pytest -m 'not gpu'" in all_runs, (
            "test-cpu must exclude GPU tests with: pytest -m 'not gpu' tests/ (AC #1)"
        )

    def test_cpu_job_has_no_needs(self) -> None:
        job = self._cpu_job()
        assert "needs" not in job, (
            "test-cpu must NOT have 'needs:' — it is the gating job with no dependency (AC #1)"
        )


class TestGPUJob:
    """AC #2: test-gpu job runs on self-hosted T4, only on release tags, after test-cpu."""

    def _gpu_job(self) -> dict:
        config = _load_yaml(CI_YML)
        jobs = config.get("jobs", {})
        assert "test-gpu" in jobs, "test-gpu job must be defined in ci.yml (AC #2)"
        return jobs["test-gpu"]

    def test_gpu_job_needs_test_cpu(self) -> None:
        job = self._gpu_job()
        needs = job.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]
        assert "test-cpu" in needs, (
            "test-gpu must depend on test-cpu with 'needs: test-cpu' (AC #2 — gate ordering)"
        )

    def test_gpu_job_runs_on_self_hosted(self) -> None:
        job = self._gpu_job()
        runs_on = job["runs-on"]
        if isinstance(runs_on, str):
            runs_on = [runs_on]
        assert "self-hosted" in runs_on, (
            "test-gpu must run on [self-hosted, gpu] runner (AC #2)"
        )

    def test_gpu_job_only_runs_on_version_tags(self) -> None:
        job = self._gpu_job()
        condition = job.get("if", "")
        assert "refs/tags/v" in condition, (
            "test-gpu must only run on version tags: if: startsWith(github.ref, 'refs/tags/v') (AC #2)"
        )

    def test_gpu_job_runs_gpu_tests(self) -> None:
        job = self._gpu_job()
        all_runs = " ".join(s.get("run", "") for s in job["steps"])
        assert 'pytest -m "gpu"' in all_runs or "pytest -m 'gpu'" in all_runs, (
            "test-gpu must run: pytest -m 'gpu' tests/ (AC #2)"
        )

    def test_gpu_job_has_benchmark_compare_step(self) -> None:
        job = self._gpu_job()
        all_runs = " ".join(s.get("run", "") for s in job["steps"])
        assert "--benchmark-compare" in all_runs, (
            "test-gpu must run pytest-benchmark with --benchmark-compare (AC #2)"
        )

    def test_gpu_job_benchmark_compare_fail_threshold(self) -> None:
        job = self._gpu_job()
        all_runs = " ".join(s.get("run", "") for s in job["steps"])
        assert "--benchmark-compare-fail" in all_runs, (
            "test-gpu benchmark step must use --benchmark-compare-fail to gate on regressions (AC #2)"
        )


class TestBenchmarkBaseline:
    """AC #2: baseline JSON must have hardware annotation and be valid JSON."""

    def test_baseline_json_exists(self) -> None:
        assert BASELINE_JSON.exists(), (
            f"benchmark_baseline.json not found at {BASELINE_JSON}.\n"
            "This file must exist and must NOT be modified by Story 1.4 (Story 1.1 scaffold)."
        )

    def test_baseline_json_is_valid(self) -> None:
        with open(BASELINE_JSON) as f:
            data = json.load(f)
        assert isinstance(data, dict), "benchmark_baseline.json must be a JSON object"

    def test_baseline_has_hardware_annotation(self) -> None:
        with open(BASELINE_JSON) as f:
            data = json.load(f)
        hardware = data.get("hardware")
        assert isinstance(hardware, str) and re.search(
            r"\b(GPU|RTX|T4|A100|H100|V100|L4|L40|RTX\s*\d{4})\b", hardware
        ), (
            f"benchmark_baseline.json must declare a recognizable GPU in 'hardware' (AC #2).\n"
            f"Got: {hardware!r}\n"
            "This annotation ensures future maintainers know the baseline hardware context."
        )

    def test_baseline_has_benchmarks_key(self) -> None:
        with open(BASELINE_JSON) as f:
            data = json.load(f)
        assert "benchmarks" in data, (
            "benchmark_baseline.json must have a 'benchmarks' key (pytest-benchmark format)"
        )


class TestContributingDoc:
    """AC #2: CONTRIBUTING.md must exist with GPU protocol and RC process sections."""

    def test_contributing_md_exists(self) -> None:
        assert CONTRIBUTING_MD.exists(), (
            "CONTRIBUTING.md not found at project root.\n"
            "Story 1.4 Task 4 requires creating this file."
        )

    def test_contributing_has_gpu_test_protocol(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "GPU" in content and ("T4" in content or "gpu" in content.lower()), (
            "CONTRIBUTING.md must document the GPU Test Protocol (AC #2 — maintainer protocol)"
        )

    def test_contributing_has_rc_community_process(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "RC" in content or "release candidate" in content.lower(), (
            "CONTRIBUTING.md must document the RC community process (v0.2+ — AC #2)"
        )

    def test_contributing_has_benchmark_baseline_instruction(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "benchmark_baseline.json" in content, (
            "CONTRIBUTING.md must mention benchmark_baseline.json update procedure (AC #2)"
        )

    def test_contributing_mentions_hardware_annotation(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "T4" in content, (
            "CONTRIBUTING.md must reference T4 GPU hardware annotation (AC #2)"
        )
