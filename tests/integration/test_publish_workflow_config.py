"""Publish workflow and release artifact validation — Story 1.5.

Validates that .github/workflows/publish.yml satisfies the OIDC Trusted Publisher
requirements, and that notebooks/quickstart.ipynb and CONTRIBUTING.md meet the
release-process ACs without actually running GitHub Actions or PyPI.
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

PROJECT_ROOT = Path(__file__).parent.parent.parent
PUBLISH_YML = PROJECT_ROOT / ".github" / "workflows" / "publish.yml"
NOTEBOOK = PROJECT_ROOT / "notebooks" / "quickstart.ipynb"
CONTRIBUTING_MD = PROJECT_ROOT / "CONTRIBUTING.md"


def _load_yaml(path: Path) -> dict:
    """Load a YAML file using PyYAML."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required — run: pip install pyyaml")
    with open(path) as f:
        return yaml.safe_load(f)


class TestPublishWorkflowExists:
    """AC #1: the publish workflow file must exist and be valid YAML."""

    def test_publish_yml_exists(self) -> None:
        assert PUBLISH_YML.exists(), (
            f".github/workflows/publish.yml not found at {PUBLISH_YML}.\n"
            "Story 1.5 Task 1 requires creating this file."
        )

    def test_publish_yml_is_valid_yaml(self) -> None:
        config = _load_yaml(PUBLISH_YML)
        assert config, "publish.yml must not be empty"
        assert isinstance(config, dict), "publish.yml must parse as a YAML mapping"


class TestPublishWorkflowTriggers:
    """AC #1: publish.yml must only trigger on version tags (v*), not on PRs or branch pushes."""

    def test_triggers_only_on_version_tags(self) -> None:
        config = _load_yaml(PUBLISH_YML)
        # 'on' is parsed as Python True by PyYAML safe_load
        triggers = config[True]
        push = triggers.get("push", {})
        tags = push.get("tags", [])
        assert tags, (
            "publish.yml must trigger only on tags (not branches) — release-only workflow (AC #1)"
        )
        assert any("v*" in t or t.startswith("v") for t in tags), (
            f"publish.yml push.tags must match 'v*' version tags, got: {tags}"
        )

    def test_does_not_trigger_on_pull_request(self) -> None:
        config = _load_yaml(PUBLISH_YML)
        triggers = config[True]
        assert "pull_request" not in triggers, (
            "publish.yml must NOT trigger on pull_request — only on version tags (AC #1)"
        )

    def test_does_not_trigger_on_branches(self) -> None:
        config = _load_yaml(PUBLISH_YML)
        triggers = config[True]
        push = triggers.get("push", {})
        assert "branches" not in push, (
            "publish.yml push must NOT list branches — only tags trigger this workflow (AC #1)"
        )


class TestPublishWorkflowPermissions:
    """AC #1: publish.yml requires id-token:write at workflow level for OIDC."""

    def test_id_token_write_at_workflow_level(self) -> None:
        config = _load_yaml(PUBLISH_YML)
        perms = config.get("permissions", {})
        assert perms.get("id-token") == "write", (
            "publish.yml must set 'permissions.id-token: write' at workflow scope.\n"
            "pypa/gh-action-pypi-publish requires OIDC token exchange — cannot be at job level (AC #1)."
        )

    def test_contents_read_at_workflow_level(self) -> None:
        config = _load_yaml(PUBLISH_YML)
        perms = config.get("permissions", {})
        assert perms.get("contents") == "read", (
            "publish.yml must set 'permissions.contents: read' at workflow scope (security hardening, AC #1)"
        )


class TestPublishJob:
    """AC #1: publish job must use OIDC Trusted Publisher without stored credentials."""

    def _publish_job(self) -> dict:
        config = _load_yaml(PUBLISH_YML)
        jobs = config.get("jobs", {})
        assert "publish" in jobs, "publish job must be defined in publish.yml (AC #1)"
        return jobs["publish"]

    def test_publish_job_runs_on_ubuntu(self) -> None:
        job = self._publish_job()
        assert job["runs-on"] == "ubuntu-latest", (
            "publish job must run on ubuntu-latest (AC #1)"
        )

    def test_publish_job_uses_pypi_environment(self) -> None:
        job = self._publish_job()
        env = job.get("environment")
        if isinstance(env, dict):
            env_name = env.get("name", "")
        else:
            env_name = env or ""
        assert env_name == "pypi", (
            f"publish job must use 'environment: pypi' for OIDC Trusted Publisher, got: {env_name!r}\n"
            "The GitHub Actions environment 'pypi' is where the Trusted Publisher is configured (AC #1)."
        )

    def test_publish_job_uses_pypi_publish_action(self) -> None:
        job = self._publish_job()
        steps = job.get("steps", [])
        publish_steps = [
            s for s in steps
            if "pypa/gh-action-pypi-publish" in str(s.get("uses", ""))
        ]
        assert publish_steps, (
            "publish job must use pypa/gh-action-pypi-publish action (AC #1 — OIDC Trusted Publisher)"
        )

    def test_publish_action_uses_release_v1_ref(self) -> None:
        job = self._publish_job()
        steps = job.get("steps", [])
        publish_steps = [
            s for s in steps
            if "pypa/gh-action-pypi-publish" in str(s.get("uses", ""))
        ]
        assert publish_steps, "pypa/gh-action-pypi-publish step not found"
        action_ref = publish_steps[0]["uses"]
        assert "release/v1" in action_ref, (
            f"pypa/gh-action-pypi-publish must use 'release/v1' floating ref (PyPA canonical form), got: {action_ref!r}"
        )

    def test_publish_action_has_no_stored_credentials(self) -> None:
        job = self._publish_job()
        steps = job.get("steps", [])
        publish_steps = [
            s for s in steps
            if "pypa/gh-action-pypi-publish" in str(s.get("uses", ""))
        ]
        assert publish_steps, "pypa/gh-action-pypi-publish step not found"
        step_with = publish_steps[0].get("with") or {}
        assert "password" not in step_with, (
            "publish action must NOT have 'with.password' — OIDC Trusted Publisher requires no credentials (AC #1)"
        )
        assert "user" not in step_with, (
            "publish action must NOT have 'with.user' — OIDC Trusted Publisher requires no credentials (AC #1)"
        )

    def test_publish_job_has_no_needs(self) -> None:
        job = self._publish_job()
        assert "needs" not in job, (
            "publish job must NOT have 'needs:' — GitHub Actions cannot express cross-workflow needs.\n"
            "Release process requires maintainer to verify CI passes before pushing the tag (AC #1, CONTRIBUTING.md)."
        )

    def test_publish_job_uses_python_312(self) -> None:
        job = self._publish_job()
        steps = job.get("steps", [])
        setup_steps = [
            s for s in steps
            if "actions/setup-python" in str(s.get("uses", ""))
        ]
        assert setup_steps, "publish job must have actions/setup-python step"
        py_version = setup_steps[0]["with"]["python-version"]
        assert py_version == "3.12", (
            f"publish job must use Python 3.12, got: {py_version}"
        )

    def test_publish_job_has_pip_cache(self) -> None:
        job = self._publish_job()
        steps = job.get("steps", [])
        setup_steps = [
            s for s in steps
            if "actions/setup-python" in str(s.get("uses", ""))
        ]
        assert setup_steps, "publish job must have actions/setup-python step"
        cache = setup_steps[0].get("with", {}).get("cache")
        assert cache == "pip", (
            "publish job must enable pip caching via actions/setup-python (build speed)"
        )

    def test_publish_job_builds_package(self) -> None:
        job = self._publish_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert "python -m build" in all_runs, (
            "publish job must build the package with 'python -m build' (AC #1)"
        )


class TestNotebookPinValidation:
    """AC #3: publish.yml must validate notebook version pin BEFORE building/publishing."""

    def _publish_job(self) -> dict:
        config = _load_yaml(PUBLISH_YML)
        return config["jobs"]["publish"]

    def _step_index(self, job: dict, marker: str) -> int:
        """Return the index of the first step whose run/name contains marker."""
        for i, step in enumerate(job.get("steps", [])):
            if marker in step.get("run", "") or marker in step.get("name", ""):
                return i
        return -1

    def test_notebook_validation_step_exists(self) -> None:
        job = self._publish_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert "pip install physlink==" in all_runs or "quickstart.ipynb" in all_runs, (
            "publish job must have a notebook pin validation step (AC #3)"
        )

    def test_notebook_validation_checks_pin_pattern(self) -> None:
        job = self._publish_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert "quickstart.ipynb" in all_runs, (
            "publish job notebook validation must grep notebooks/quickstart.ipynb for the version pin (AC #3)"
        )

    def test_notebook_validation_runs_before_build(self) -> None:
        job = self._publish_job()
        steps = job.get("steps", [])
        notebook_idx = next(
            (i for i, s in enumerate(steps) if "quickstart.ipynb" in s.get("run", "")),
            -1,
        )
        build_idx = next(
            (i for i, s in enumerate(steps) if "python -m build" in s.get("run", "")),
            -1,
        )
        assert notebook_idx != -1, "notebook validation step not found"
        assert build_idx != -1, "python -m build step not found"
        assert notebook_idx < build_idx, (
            f"notebook validation (step {notebook_idx}) must run BEFORE build (step {build_idx}) — fail fast (AC #3)"
        )

    def test_publish_job_has_smoke_test_step(self) -> None:
        job = self._publish_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert "physlink.__all__" in all_runs or ("import physlink" in all_runs and "assert" in all_runs), (
            "publish job must have a post-publish smoke test verifying physlink.__all__ symbols (AC #2, #3)"
        )

    def test_smoke_test_runs_after_publish(self) -> None:
        job = self._publish_job()
        steps = job.get("steps", [])
        publish_idx = next(
            (i for i, s in enumerate(steps) if "pypa/gh-action-pypi-publish" in str(s.get("uses", ""))),
            -1,
        )
        smoke_idx = next(
            (
                i for i, s in enumerate(steps)
                if "physlink.__all__" in s.get("run", "") or (
                    "import physlink" in s.get("run", "") and "assert" in s.get("run", "")
                )
            ),
            -1,
        )
        assert publish_idx != -1, "pypa/gh-action-pypi-publish step not found"
        assert smoke_idx != -1, "smoke test step not found"
        assert smoke_idx > publish_idx, (
            f"smoke test (step {smoke_idx}) must run AFTER publish (step {publish_idx}) (AC #3)"
        )


class TestQuickstartNotebook:
    """AC #2, #3: notebooks/quickstart.ipynb must exist with proper structure."""

    def test_notebook_exists(self) -> None:
        assert NOTEBOOK.exists(), (
            f"notebooks/quickstart.ipynb not found at {NOTEBOOK}.\n"
            "Story 1.5 Task 3 requires creating this file."
        )

    def test_notebook_is_valid_json(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        assert data, "notebooks/quickstart.ipynb must not be empty"
        assert isinstance(data, dict), "notebooks/quickstart.ipynb must be a JSON object"

    def test_notebook_is_nbformat_4(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        assert data.get("nbformat") == 4, (
            f"notebook must use nbformat 4, got: {data.get('nbformat')!r} (Colab compatibility, AC #3)"
        )

    def test_notebook_has_colab_metadata(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        meta = data.get("metadata", {})
        assert "colab" in meta, (
            "notebook metadata must include 'colab' key so Google Colab recognizes the runtime (AC #2, #3)"
        )

    def test_notebook_has_kernelspec(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        meta = data.get("metadata", {})
        kernelspec = meta.get("kernelspec", {})
        assert kernelspec.get("name") == "python3", (
            f"notebook kernelspec must be 'python3', got: {kernelspec.get('name')!r} (Colab compatibility)"
        )

    def test_notebook_has_cells(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        cells = data.get("cells", [])
        assert len(cells) >= 2, (
            f"notebook must have at least 2 cells (install + smoke), got: {len(cells)}"
        )

    def test_notebook_first_cell_has_explicit_version_pin(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        cells = data.get("cells", [])
        assert cells, "notebook has no cells"
        first_source = "".join(cells[0].get("source", []))
        assert "pip install physlink==" in first_source, (
            f"notebook cell 1 must pin an explicit version: 'pip install physlink==X.Y.Z'.\n"
            f"Got: {first_source!r}\n"
            "Unversioned install breaks the publish.yml pin validation step (AC #3)."
        )

    def test_notebook_first_cell_pins_current_version(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        cells = data.get("cells", [])
        first_source = "".join(cells[0].get("source", []))
        # Read current version from pyproject.toml
        pyproject = PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            pydata = tomllib.load(f)
        current_version = pydata["project"]["version"]
        assert f"physlink=={current_version}" in first_source, (
            f"notebook cell 1 must pin current version physlink=={current_version}.\n"
            f"Got: {first_source!r}\n"
            "Update notebooks/quickstart.ipynb when bumping pyproject.toml version."
        )

    def test_notebook_has_import_physlink_cell(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        cells = data.get("cells", [])
        all_source = " ".join("".join(c.get("source", [])) for c in cells)
        assert "import physlink" in all_source, (
            "notebook must have an 'import physlink' cell to smoke-test the install (AC #2, #3)"
        )

    def test_notebook_has_doctor_call(self) -> None:
        with open(NOTEBOOK) as f:
            data = json.load(f)
        cells = data.get("cells", [])
        all_source = " ".join("".join(c.get("source", [])) for c in cells)
        assert "physlink.doctor()" in all_source or "doctor()" in all_source, (
            "notebook must call physlink.doctor() to verify the install works end-to-end (AC #2)"
        )


class TestContributingOIDCSection:
    """AC #1: CONTRIBUTING.md must document OIDC Trusted Publisher setup and release process."""

    def test_contributing_has_oidc_section(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "OIDC" in content or "Trusted Publisher" in content, (
            "CONTRIBUTING.md must have a section documenting OIDC Trusted Publisher setup (AC #1)"
        )

    def test_contributing_has_pypi_publication_section(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "PyPI Publication" in content or "pypi.org" in content.lower(), (
            "CONTRIBUTING.md must have a PyPI publication section (Story 1.5 Task 4, AC #1)"
        )

    def test_contributing_documents_trusted_publisher_setup(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "publish.yml" in content, (
            "CONTRIBUTING.md must reference publish.yml in the Trusted Publisher setup (AC #1)"
        )

    def test_contributing_documents_release_process(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "quickstart.ipynb" in content or "notebook" in content.lower(), (
            "CONTRIBUTING.md release process must mention updating notebooks/quickstart.ipynb pin (AC #1, #3)"
        )

    def test_contributing_documents_tag_push(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        assert "git tag" in content or "push origin" in content, (
            "CONTRIBUTING.md must document the 'git tag + push' release step (AC #1)"
        )

    def test_contributing_no_stored_credentials_mentioned(self) -> None:
        content = CONTRIBUTING_MD.read_text()
        lower = content.lower()
        # Positive check: OIDC/keyless auth is documented
        assert "no credentials" in lower or "oidc" in lower or "trusted publisher" in lower, (
            "CONTRIBUTING.md must document that no credentials are stored (OIDC keyless, AC #1)"
        )
