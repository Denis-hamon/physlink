"""MkDocs documentation site validation — Story 2.5.

Validates that the documentation infrastructure (mkdocs.yml, docs/ pages,
CI docs job, GitHub Pages deploy workflow, README badge) satisfies all
Acceptance Criteria for Story 2.5 without actually running mkdocs build
or making network requests.
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

PROJECT_ROOT = Path(__file__).parent.parent.parent
MKDOCS_YML = PROJECT_ROOT / "mkdocs.yml"
DOCS_DIR = PROJECT_ROOT / "docs"
CI_YML = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
DOCS_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "docs.yml"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
README = PROJECT_ROOT / "README.md"


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required — run: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# AC #1: mkdocs build produces site/ without errors
# ---------------------------------------------------------------------------


class TestMkdocsYmlExists:
    """AC #1: mkdocs.yml must exist at project root and be valid YAML."""

    def test_mkdocs_yml_exists(self) -> None:
        assert MKDOCS_YML.exists(), (
            f"mkdocs.yml not found at {MKDOCS_YML}.\n"
            "Story 2.5 Task 2 requires creating this file at the project root."
        )

    def test_mkdocs_yml_is_valid_yaml(self) -> None:
        config = _load_yaml(MKDOCS_YML)
        assert config, "mkdocs.yml must not be empty"
        assert isinstance(config, dict), "mkdocs.yml must parse as a YAML mapping"


class TestMkdocsYmlRequiredFields:
    """AC #1: mkdocs.yml must define site_name, theme material, and plugins."""

    def test_site_name_is_physlink(self) -> None:
        config = _load_yaml(MKDOCS_YML)
        assert config.get("site_name") == "PhysLink", (
            f"mkdocs.yml site_name must be 'PhysLink', got: {config.get('site_name')!r}"
        )

    def test_theme_is_material(self) -> None:
        config = _load_yaml(MKDOCS_YML)
        theme = config.get("theme", {})
        assert theme.get("name") == "material", (
            f"mkdocs.yml theme.name must be 'material', got: {theme.get('name')!r}\n"
            "Architecture AR-09 specifies MkDocs Material."
        )

    def test_search_plugin_present(self) -> None:
        config = _load_yaml(MKDOCS_YML)
        plugins = config.get("plugins", [])
        plugin_names = [
            (p if isinstance(p, str) else list(p.keys())[0]) for p in plugins
        ]
        assert "search" in plugin_names, (
            "mkdocs.yml must include the 'search' plugin (required for usable docs site)"
        )

    def test_mkdocstrings_plugin_present(self) -> None:
        config = _load_yaml(MKDOCS_YML)
        plugins = config.get("plugins", [])
        plugin_names = [
            (p if isinstance(p, str) else list(p.keys())[0]) for p in plugins
        ]
        assert "mkdocstrings" in plugin_names, (
            "mkdocs.yml must include the 'mkdocstrings' plugin (Story 2.5 Task 2, AC #1)"
        )

    def test_site_url_uses_your_org_placeholder(self) -> None:
        config = _load_yaml(MKDOCS_YML)
        site_url = config.get("site_url", "")
        assert "YOUR-ORG" not in site_url, (
            f"mkdocs.yml site_url still contains the 'YOUR-ORG' template placeholder, got: {site_url!r}\n"
            "Fix: replace YOUR-ORG with the actual GitHub owner deploying this fork."
        )
        assert re.match(
            r"^https://[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?\.github\.io/physlink/?$",
            site_url,
        ), (
            f"mkdocs.yml site_url must be 'https://<owner>.github.io/physlink/', got: {site_url!r}"
        )

    def test_mike_version_provider_configured(self) -> None:
        config = _load_yaml(MKDOCS_YML)
        extra = config.get("extra", {})
        version = extra.get("version", {})
        assert version.get("provider") == "mike", (
            "mkdocs.yml extra.version.provider must be 'mike' (architecture: versioning via mike from v0.2)"
        )


class TestMkdocstringsConfig:
    """AC #1/#2: mkdocstrings must be configured for src-layout with Google docstring style."""

    def _mkdocstrings_options(self) -> dict:
        config = _load_yaml(MKDOCS_YML)
        plugins = config.get("plugins", [])
        for plugin in plugins:
            if isinstance(plugin, dict) and "mkdocstrings" in plugin:
                return plugin["mkdocstrings"]
        return {}

    def test_python_paths_includes_src(self) -> None:
        options = self._mkdocstrings_options()
        handlers = options.get("handlers", {})
        python = handlers.get("python", {})
        paths = python.get("paths", [])
        assert "src" in paths, (
            f"mkdocstrings python handler must have 'paths: [src]', got: {paths!r}\n"
            "Without 'paths: [src]', mkdocstrings cannot resolve symbols in src/ layout — "
            "most common failure mode (Story 2.5 Dev Notes critical note)."
        )

    def test_docstring_style_is_google(self) -> None:
        options = self._mkdocstrings_options()
        handlers = options.get("handlers", {})
        python = handlers.get("python", {})
        opts = python.get("options", {})
        assert opts.get("docstring_style") == "google", (
            f"mkdocstrings python options.docstring_style must be 'google', got: {opts.get('docstring_style')!r}\n"
            "Architecture Category 4 specifies Google-style docstrings."
        )

    def test_show_source_is_false(self) -> None:
        options = self._mkdocstrings_options()
        handlers = options.get("handlers", {})
        python = handlers.get("python", {})
        opts = python.get("options", {})
        assert opts.get("show_source") is False, (
            f"mkdocstrings python options.show_source must be false, got: {opts.get('show_source')!r}"
        )


class TestMkdocsNavPages:
    """AC #1: all nav entries in mkdocs.yml must correspond to existing doc files."""

    NAV_EXPECTED = {
        "index.md": DOCS_DIR / "index.md",
        "getting-started.md": DOCS_DIR / "getting-started.md",
        "domain-scientists.md": DOCS_DIR / "domain-scientists.md",
        "api/index.md": DOCS_DIR / "api" / "index.md",
        "changelog.md": DOCS_DIR / "changelog.md",
        "lab-adoption-guide.md": DOCS_DIR / "lab-adoption-guide.md",
    }

    def test_docs_dir_exists(self) -> None:
        assert DOCS_DIR.exists() and DOCS_DIR.is_dir(), (
            f"docs/ directory not found at {DOCS_DIR}.\n"
            "Story 2.5 Task 3 requires creating all content files under docs/."
        )

    def test_all_nav_files_exist(self) -> None:
        missing = [
            rel for rel, path in self.NAV_EXPECTED.items() if not path.exists()
        ]
        assert not missing, (
            f"These nav pages referenced in mkdocs.yml do not exist:\n"
            + "\n".join(f"  docs/{rel}" for rel in missing)
            + "\nmkdocs build --strict will fail with a missing nav page error."
        )

    def test_api_directory_exists(self) -> None:
        api_dir = DOCS_DIR / "api"
        assert api_dir.exists() and api_dir.is_dir(), (
            f"docs/api/ directory not found at {api_dir}.\n"
            "Required by nav entry 'API Reference: api/index.md'."
        )


class TestDocsPyprojectOptDeps:
    """AC #1: pyproject.toml must declare the docs optional-dependencies group."""

    def _pyproject(self) -> dict:
        with open(PYPROJECT, "rb") as f:
            return tomllib.load(f)

    def test_docs_optional_deps_group_exists(self) -> None:
        data = self._pyproject()
        opt_deps = data.get("project", {}).get("optional-dependencies", {})
        assert "docs" in opt_deps, (
            "pyproject.toml must have a 'docs' group under [project.optional-dependencies].\n"
            "Required by: 'pip install -e \".[docs]\"' in CI docs job (Story 2.5 Task 1, AC #1)."
        )

    def test_docs_includes_mkdocs_material(self) -> None:
        data = self._pyproject()
        docs_deps = data["project"]["optional-dependencies"].get("docs", [])
        deps_str = " ".join(docs_deps)
        assert "mkdocs-material" in deps_str, (
            f"docs optional-dependencies must include 'mkdocs-material>=9.5', got: {docs_deps!r}"
        )

    def test_docs_includes_mkdocstrings_python(self) -> None:
        data = self._pyproject()
        docs_deps = data["project"]["optional-dependencies"].get("docs", [])
        deps_str = " ".join(docs_deps)
        assert "mkdocstrings" in deps_str, (
            f"docs optional-dependencies must include 'mkdocstrings[python]>=0.25', got: {docs_deps!r}"
        )

    def test_docs_includes_mike(self) -> None:
        data = self._pyproject()
        docs_deps = data["project"]["optional-dependencies"].get("docs", [])
        deps_str = " ".join(docs_deps)
        assert "mike" in deps_str, (
            f"docs optional-dependencies must include 'mike>=2.1' (versioning from v0.2), got: {docs_deps!r}"
        )

    def test_existing_dev_deps_group_intact(self) -> None:
        data = self._pyproject()
        opt_deps = data.get("project", {}).get("optional-dependencies", {})
        assert "dev" in opt_deps, (
            "pyproject.toml must still have the 'dev' optional-dependencies group after Story 2.5 changes.\n"
            "Adding the 'docs' group must not remove or rename the existing 'dev' group."
        )


# ---------------------------------------------------------------------------
# AC #2: API reference contains ObservationSpace, ActionSpace, doctor, PhysLinkError
# ---------------------------------------------------------------------------


class TestDocsApiReference:
    """AC #2: docs/api/index.md must declare mkdocstrings directives for all 4 symbols."""

    API_INDEX = DOCS_DIR / "api" / "index.md"

    def _content(self) -> str:
        assert self.API_INDEX.exists(), f"docs/api/index.md not found at {self.API_INDEX}"
        return self.API_INDEX.read_text(encoding="utf-8")

    def test_physlink_error_directive_present(self) -> None:
        assert "physlink.core.exceptions.PhysLinkError" in self._content(), (
            "docs/api/index.md must contain '::: physlink.core.exceptions.PhysLinkError' "
            "mkdocstrings directive (AC #2)."
        )

    def test_doctor_directive_present(self) -> None:
        assert "physlink.utils.diagnostics.doctor" in self._content(), (
            "docs/api/index.md must contain '::: physlink.utils.diagnostics.doctor' "
            "mkdocstrings directive (AC #2)."
        )

    def test_observation_space_directive_uses_full_module_path(self) -> None:
        content = self._content()
        assert "physlink.core.spaces.ObservationSpace" in content, (
            "docs/api/index.md must reference ObservationSpace via full module path "
            "'physlink.core.spaces.ObservationSpace' — not via physlink.__init__ "
            "(ObservationSpace not in __init__ until Story 2.6, AC #2 note)."
        )

    def test_action_space_directive_uses_full_module_path(self) -> None:
        content = self._content()
        assert "physlink.core.spaces.ActionSpace" in content, (
            "docs/api/index.md must reference ActionSpace via full module path "
            "'physlink.core.spaces.ActionSpace' — not via physlink.__init__ "
            "(ActionSpace not in __init__ until Story 2.6, AC #2 note)."
        )

    def test_all_four_symbols_have_directives(self) -> None:
        content = self._content()
        symbols = [
            "physlink.core.exceptions.PhysLinkError",
            "physlink.utils.diagnostics.doctor",
            "physlink.core.spaces.ObservationSpace",
            "physlink.core.spaces.ActionSpace",
        ]
        missing = [s for s in symbols if s not in content]
        assert not missing, (
            f"docs/api/index.md is missing mkdocstrings directives for:\n"
            + "\n".join(f"  ::: {s}" for s in missing)
            + "\nAC #2 requires all 4 current symbols to appear in the API reference."
        )


# ---------------------------------------------------------------------------
# AC #1/#2: docs content files exist and have expected key content
# ---------------------------------------------------------------------------


class TestDocsContentFiles:
    """AC #1/#2: all docs content pages must exist and contain key content."""

    def test_index_md_exists_and_has_physlink_heading(self) -> None:
        index = DOCS_DIR / "index.md"
        assert index.exists(), "docs/index.md must exist (Story 2.5 Task 3)"
        content = index.read_text(encoding="utf-8")
        assert "PhysLink" in content, (
            "docs/index.md must mention 'PhysLink' — it is the home page of the docs site"
        )

    def test_getting_started_md_exists_and_covers_5_steps(self) -> None:
        page = DOCS_DIR / "getting-started.md"
        assert page.exists(), "docs/getting-started.md must exist (Story 2.5 Task 3, DD-001 Hugo path)"
        content = page.read_text(encoding="utf-8")
        assert "ObservationSpace" in content, (
            "docs/getting-started.md must cover ObservationSpace (Hugo DD-001 step 3)"
        )
        assert "ActionSpace" in content, (
            "docs/getting-started.md must cover ActionSpace (Hugo DD-001 step 4)"
        )
        assert "doctor" in content, (
            "docs/getting-started.md must cover physlink.doctor() (Hugo DD-001 step 2)"
        )

    def test_domain_scientists_md_exists(self) -> None:
        page = DOCS_DIR / "domain-scientists.md"
        assert page.exists(), (
            "docs/domain-scientists.md must exist (Story 2.5 Task 3, DD-003 Samuel path)"
        )

    def test_changelog_md_exists(self) -> None:
        page = DOCS_DIR / "changelog.md"
        assert page.exists(), "docs/changelog.md must exist (Story 2.5 Task 3)"

    def test_lab_adoption_guide_md_exists(self) -> None:
        page = DOCS_DIR / "lab-adoption-guide.md"
        assert page.exists(), (
            "docs/lab-adoption-guide.md must exist (Story 2.5 Task 3, DD-002 Petra path)"
        )

    def test_no_docs_page_is_empty(self) -> None:
        pages = [
            DOCS_DIR / "index.md",
            DOCS_DIR / "getting-started.md",
            DOCS_DIR / "domain-scientists.md",
            DOCS_DIR / "changelog.md",
            DOCS_DIR / "lab-adoption-guide.md",
            DOCS_DIR / "api" / "index.md",
        ]
        empty = [str(p.relative_to(PROJECT_ROOT)) for p in pages if p.exists() and not p.read_text(encoding="utf-8").strip()]
        assert not empty, (
            f"These docs pages are empty (mkdocs --strict may warn):\n"
            + "\n".join(f"  {p}" for p in empty)
        )


# ---------------------------------------------------------------------------
# AC #3: GitHub Pages deploy workflow
# ---------------------------------------------------------------------------


class TestDocsWorkflowExists:
    """AC #3: .github/workflows/docs.yml must exist and be valid YAML."""

    def test_docs_workflow_exists(self) -> None:
        assert DOCS_WORKFLOW.exists(), (
            f".github/workflows/docs.yml not found at {DOCS_WORKFLOW}.\n"
            "Story 2.5 Task 5 requires creating this GitHub Pages deploy workflow."
        )

    def test_docs_workflow_is_valid_yaml(self) -> None:
        config = _load_yaml(DOCS_WORKFLOW)
        assert config, "docs.yml must not be empty"
        assert isinstance(config, dict), "docs.yml must parse as a YAML mapping"


class TestDocsWorkflowTrigger:
    """AC #3: docs.yml must only trigger on push to main branch."""

    def test_triggers_on_push_to_main_only(self) -> None:
        config = _load_yaml(DOCS_WORKFLOW)
        triggers = config[True]
        push = triggers.get("push", {})
        branches = push.get("branches", [])
        assert "main" in branches, (
            f"docs.yml must trigger on push to main, got branches: {branches!r} (AC #3)"
        )

    def test_does_not_trigger_on_pull_request(self) -> None:
        config = _load_yaml(DOCS_WORKFLOW)
        triggers = config[True]
        assert "pull_request" not in triggers, (
            "docs.yml must NOT trigger on pull_request — deploy only on merge to main (AC #3)"
        )

    def test_does_not_trigger_on_tags(self) -> None:
        config = _load_yaml(DOCS_WORKFLOW)
        triggers = config[True]
        push = triggers.get("push", {})
        tags = push.get("tags", [])
        assert not tags, (
            f"docs.yml push must NOT trigger on tags, got: {tags!r} — deploy is triggered by merges to main only (AC #3)"
        )


class TestDocsWorkflowPermissions:
    """AC #3: docs.yml requires contents:write to push to the gh-pages branch."""

    def test_contents_write_permission(self) -> None:
        config = _load_yaml(DOCS_WORKFLOW)
        perms = config.get("permissions", {})
        assert perms.get("contents") == "write", (
            f"docs.yml must set 'permissions.contents: write', got: {perms.get('contents')!r}\n"
            "mkdocs gh-deploy pushes to the gh-pages branch and requires write access (AC #3)."
        )


class TestDocsDeployJob:
    """AC #3: deploy job must use correct Python, full git history, and mkdocs gh-deploy."""

    def _deploy_job(self) -> dict:
        config = _load_yaml(DOCS_WORKFLOW)
        jobs = config.get("jobs", {})
        assert jobs, "docs.yml must define at least one job"
        return next(iter(jobs.values()))

    def test_deploy_job_runs_on_ubuntu(self) -> None:
        job = self._deploy_job()
        assert job.get("runs-on") == "ubuntu-latest", (
            f"docs.yml deploy job must run on ubuntu-latest, got: {job.get('runs-on')!r}"
        )

    def test_checkout_uses_full_history(self) -> None:
        job = self._deploy_job()
        steps = job.get("steps", [])
        checkout_steps = [s for s in steps if "actions/checkout" in str(s.get("uses", ""))]
        assert checkout_steps, "deploy job must have actions/checkout step"
        fetch_depth = checkout_steps[0].get("with", {}).get("fetch-depth")
        assert fetch_depth == 0, (
            f"docs.yml checkout must set fetch-depth: 0, got: {fetch_depth!r}\n"
            "mkdocs gh-deploy needs full git history to avoid force-push conflicts with gh-pages branch (AC #3)."
        )

    def test_deploy_job_uses_python_312(self) -> None:
        job = self._deploy_job()
        steps = job.get("steps", [])
        setup_steps = [s for s in steps if "actions/setup-python" in str(s.get("uses", ""))]
        assert setup_steps, "deploy job must have actions/setup-python step"
        py_version = setup_steps[0]["with"]["python-version"]
        assert py_version == "3.12", (
            f"docs.yml deploy job must use Python 3.12, got: {py_version!r}"
        )

    def test_deploy_job_installs_docs_deps(self) -> None:
        job = self._deploy_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert ".[docs]" in all_runs, (
            "docs.yml deploy job must install docs dependencies with 'pip install -e \".[docs]\"' (AC #3)"
        )

    def test_deploy_uses_gh_deploy_not_mike(self) -> None:
        job = self._deploy_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert "mkdocs gh-deploy" in all_runs, (
            "docs.yml deploy job must use 'mkdocs gh-deploy' (not 'mike deploy').\n"
            "Architecture specifies: mike versioning deferred to v0.2. For v0.1 use mkdocs gh-deploy (AC #3)."
        )
        assert "mike deploy" not in all_runs, (
            "docs.yml must NOT use 'mike deploy' — mike versioning is deferred to v0.2 per architecture."
        )

    def test_deploy_uses_force_flag(self) -> None:
        job = self._deploy_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert "gh-deploy --force" in all_runs, (
            "docs.yml deploy must use 'mkdocs gh-deploy --force' to overwrite gh-pages on each deploy (AC #3)"
        )

    def test_deploy_job_has_no_needs(self) -> None:
        config = _load_yaml(DOCS_WORKFLOW)
        jobs = config.get("jobs", {})
        for job in jobs.values():
            assert "needs" not in job, (
                "docs.yml deploy job must NOT have 'needs:' — it is a standalone deploy workflow (AC #3)"
            )


# ---------------------------------------------------------------------------
# AC #1 (CI): docs job in ci.yml
# ---------------------------------------------------------------------------


class TestCIDocsJob:
    """AC #1: ci.yml must have a parallel 'docs' job running mkdocs build --strict."""

    def _docs_job(self) -> dict:
        config = _load_yaml(CI_YML)
        jobs = config.get("jobs", {})
        assert "docs" in jobs, (
            "ci.yml must define a 'docs' job (Story 2.5 Task 4, AC #1).\n"
            "The docs job runs 'mkdocs build --strict' to catch broken nav links before merge."
        )
        return jobs["docs"]

    def test_docs_job_exists(self) -> None:
        self._docs_job()

    def test_docs_job_runs_on_ubuntu(self) -> None:
        job = self._docs_job()
        assert job.get("runs-on") == "ubuntu-latest", (
            f"CI docs job must run on ubuntu-latest, got: {job.get('runs-on')!r}"
        )

    def test_docs_job_uses_python_312(self) -> None:
        job = self._docs_job()
        steps = job.get("steps", [])
        setup_steps = [s for s in steps if "actions/setup-python" in str(s.get("uses", ""))]
        assert setup_steps, "CI docs job must have actions/setup-python step"
        py_version = setup_steps[0]["with"]["python-version"]
        assert py_version == "3.12", (
            f"CI docs job must use Python 3.12, got: {py_version!r}"
        )

    def test_docs_job_has_pip_cache(self) -> None:
        job = self._docs_job()
        steps = job.get("steps", [])
        setup_steps = [s for s in steps if "actions/setup-python" in str(s.get("uses", ""))]
        assert setup_steps
        cache = setup_steps[0].get("with", {}).get("cache")
        assert cache == "pip", (
            "CI docs job must enable pip caching via actions/setup-python (build speed)"
        )

    def test_docs_job_installs_docs_deps(self) -> None:
        job = self._docs_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert ".[docs]" in all_runs, (
            "CI docs job must install docs dependencies with 'pip install -e \".[docs]\"' (AC #1)"
        )

    def test_docs_job_runs_mkdocs_build_strict(self) -> None:
        job = self._docs_job()
        all_runs = " ".join(s.get("run", "") for s in job.get("steps", []))
        assert "mkdocs build --strict" in all_runs, (
            "CI docs job must run 'mkdocs build --strict'.\n"
            "'--strict' turns warnings into errors: catches broken nav links and unresolvable "
            "mkdocstrings references before merge (AC #1)."
        )

    def test_docs_job_is_parallel_no_needs(self) -> None:
        job = self._docs_job()
        assert "needs" not in job, (
            "CI docs job must NOT have 'needs:' — it runs in parallel with test-cpu (AC #1).\n"
            "Parallel execution keeps PR gating fast."
        )


# ---------------------------------------------------------------------------
# AC #4: README docs badge
# ---------------------------------------------------------------------------


class TestReadmeDocsBadge:
    """AC #4: README.md must contain the Docs badge linking to GitHub Pages URL."""

    def _readme(self) -> str:
        return README.read_text(encoding="utf-8")

    def test_docs_badge_present(self) -> None:
        assert "shields.io/badge/docs-GitHub%20Pages" in self._readme(), (
            "README.md must contain the Docs badge 'shields.io/badge/docs-GitHub%20Pages-blue.svg'.\n"
            "Story 2.5 Task 6, AC #4 — researchers must see the docs link in the README."
        )

    def test_docs_badge_links_to_github_pages(self) -> None:
        assert "github.io/physlink/" in self._readme(), (
            "README.md docs badge must link to the GitHub Pages URL 'YOUR-ORG.github.io/physlink/'.\n"
            "AC #4: researchers navigate from README to the docs site via this link."
        )

    def test_docs_badge_uses_your_org_placeholder(self) -> None:
        readme = self._readme()
        assert "YOUR-ORG.github.io/physlink/" not in readme, (
            "README.md docs badge URL still uses the 'YOUR-ORG' template placeholder. "
            "Fix: replace YOUR-ORG with the actual GitHub owner deploying this fork."
        )
        assert re.search(
            r"https://[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?\.github\.io/physlink/",
            readme,
        ), (
            "README.md docs badge must link to '<owner>.github.io/physlink/' "
            "(real GitHub Pages URL — Story 2.5 Dev Notes)."
        )

    def test_docs_badge_positioned_between_ci_and_arxiv(self) -> None:
        readme = self._readme()
        ci_pos = readme.find("workflows/ci.yml/badge.svg")
        docs_pos = readme.find("shields.io/badge/docs-GitHub%20Pages")
        arxiv_pos = readme.find("shields.io/badge/arXiv")
        assert ci_pos != -1, "CI badge not found in README (prerequisite for position check)"
        assert docs_pos != -1, "Docs badge not found in README"
        assert arxiv_pos != -1, "arXiv badge not found in README (prerequisite for position check)"
        assert ci_pos < docs_pos < arxiv_pos, (
            f"Docs badge must appear BETWEEN the CI badge and arXiv badge in README.\n"
            f"  CI badge at char {ci_pos}, docs badge at {docs_pos}, arXiv badge at {arxiv_pos}.\n"
            "Story 2.5 Task 6 specifies insertion between CI and arXiv badges."
        )
