"""Unit tests for Story 1.1 package scaffold structure.

Verifies all expected stub files exist, __all__ is empty, and core/ files
carry the mandatory from __future__ import annotations header.
"""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src" / "physlink"


EXPECTED_SOURCE_FILES = [
    SRC_ROOT / "__init__.py",
    SRC_ROOT / "core" / "__init__.py",
    SRC_ROOT / "core" / "_types.py",
    SRC_ROOT / "core" / "adapter.py",
    SRC_ROOT / "core" / "exceptions.py",
    SRC_ROOT / "core" / "spaces.py",
    SRC_ROOT / "core" / "validation.py",
    SRC_ROOT / "adapters" / "__init__.py",
    SRC_ROOT / "adapters" / "dreamer.py",
    SRC_ROOT / "utils" / "__init__.py",
    SRC_ROOT / "utils" / "diagnostics.py",
    SRC_ROOT / "utils" / "visualization.py",
]

EXPECTED_TEST_FILES = [
    PROJECT_ROOT / "tests" / "conftest.py",
    PROJECT_ROOT / "tests" / "integration" / "test_core_no_torch_import.py",
    PROJECT_ROOT / "tests" / "integration" / "test_core_boundary.py",
    PROJECT_ROOT / "tests" / "integration" / "test_api_stability.py",
    PROJECT_ROOT / "tests" / "perf" / "test_nfr_benchmarks.py",
    PROJECT_ROOT / "tests" / "perf" / "baselines" / "benchmark_baseline.json",
]

EXPECTED_UNIT_DIRS = [
    PROJECT_ROOT / "tests" / "unit" / "core",
    PROJECT_ROOT / "tests" / "unit" / "adapters",
    PROJECT_ROOT / "tests" / "unit" / "utils",
]


class TestSourceFilesExist:
    def test_all_source_stubs_present(self) -> None:
        missing = [str(f) for f in EXPECTED_SOURCE_FILES if not f.exists()]
        assert not missing, f"Missing source stubs:\n" + "\n".join(missing)

    def test_src_layout_enforced(self) -> None:
        """No physlink/ package at repo root — src/ layout constraint (AC #2)."""
        repo_root_package = PROJECT_ROOT / "physlink"
        assert not repo_root_package.exists(), (
            f"{repo_root_package} must not exist — src/ layout enforces import isolation"
        )

    def test_test_scaffold_files_present(self) -> None:
        missing = [str(f) for f in EXPECTED_TEST_FILES if not f.exists()]
        assert not missing, f"Missing test scaffold files:\n" + "\n".join(missing)

    def test_unit_subdirectories_present(self) -> None:
        missing = [str(d) for d in EXPECTED_UNIT_DIRS if not d.is_dir()]
        assert not missing, f"Missing unit test directories:\n" + "\n".join(missing)


class TestPhyslinkInit:
    def test_all_contains_physlink_error(self) -> None:
        """physlink.__all__ must contain exactly PhysLinkError at Epic 1 stage (Story 1.2+)."""
        init = SRC_ROOT / "__init__.py"
        source = init.read_text()
        tree = ast.parse(source)
        # __all__: list[str] = [] is AnnAssign; __all__ = [] is Assign
        all_node: ast.expr | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "__all__":
                all_node = node.value
                break
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "__all__":
                        all_node = node.value
                        break
        assert all_node is not None, "__all__ assignment not found in physlink/__init__.py"
        assert isinstance(all_node, ast.List), "__all__ must be a list literal"
        exported = {elt.value for elt in all_node.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)}
        assert "PhysLinkError" in exported, (
            f"PhysLinkError must be in physlink.__all__ after Story 1.2, got: {exported}"
        )

    def test_init_has_module_docstring(self) -> None:
        init = SRC_ROOT / "__init__.py"
        tree = ast.parse(init.read_text())
        docstring = ast.get_docstring(tree)
        assert docstring, "physlink/__init__.py must have a module docstring"


class TestCoreModuleHeaders:
    def _core_files(self) -> list[Path]:
        return list((SRC_ROOT / "core").rglob("*.py"))

    def test_all_core_files_have_future_annotations(self) -> None:
        """All core/ files must start with from __future__ import annotations (AR-11/NFR-08)."""
        violations: list[str] = []
        for filepath in self._core_files():
            source = filepath.read_text()
            tree = ast.parse(source)
            has_future = any(
                isinstance(node, ast.ImportFrom)
                and node.module == "__future__"
                and any(alias.name == "annotations" for alias in node.names)
                for node in ast.walk(tree)
            )
            if not has_future:
                violations.append(str(filepath))
        assert not violations, (
            "Missing 'from __future__ import annotations' in core/ files:\n"
            + "\n".join(violations)
        )

    def test_core_files_are_parseable(self) -> None:
        errors: list[str] = []
        for filepath in self._core_files():
            try:
                ast.parse(filepath.read_text())
            except SyntaxError as e:
                errors.append(f"{filepath}: {e}")
        assert not errors, "Syntax errors in core/ files:\n" + "\n".join(errors)


class TestPreCommitConfig:
    def test_pre_commit_config_exists(self) -> None:
        config = PROJECT_ROOT / ".pre-commit-config.yaml"
        assert config.exists(), ".pre-commit-config.yaml must exist (AC #5)"

    def test_pre_commit_config_has_ruff_hooks(self) -> None:
        import yaml  # type: ignore[import-untyped]

        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        data = yaml.safe_load(config_path.read_text())
        all_hook_ids = [
            hook["id"]
            for repo in data.get("repos", [])
            for hook in repo.get("hooks", [])
        ]
        assert "ruff" in all_hook_ids, "pre-commit config must include ruff hook"
        assert "ruff-format" in all_hook_ids, "pre-commit config must include ruff-format hook"

    def test_pre_commit_ruff_hook_has_fix_arg(self) -> None:
        import yaml  # type: ignore[import-untyped]

        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        data = yaml.safe_load(config_path.read_text())
        for repo in data.get("repos", []):
            for hook in repo.get("hooks", []):
                if hook["id"] == "ruff":
                    args = hook.get("args", [])
                    assert "--fix" in args, "ruff pre-commit hook must include --fix arg"
                    return
        raise AssertionError("ruff hook not found in .pre-commit-config.yaml")


class TestPyprojectToml:
    def _load(self) -> dict:  # type: ignore[type-arg]
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        config_path = PROJECT_ROOT / "pyproject.toml"
        with open(config_path, "rb") as f:
            return tomllib.load(f)

    def test_pyproject_toml_exists(self) -> None:
        assert (PROJECT_ROOT / "pyproject.toml").exists()

    def test_build_system_section(self) -> None:
        data = self._load()
        bs = data.get("build-system", {})
        assert "setuptools" in " ".join(bs.get("requires", [])), (
            "build-system.requires must include setuptools"
        )
        assert bs.get("build-backend"), "build-system.build-backend must be set"

    def test_project_metadata(self) -> None:
        data = self._load()
        proj = data.get("project", {})
        assert proj.get("name") == "physlink"
        assert proj.get("version")
        assert proj.get("requires-python")

    def test_setuptools_src_layout(self) -> None:
        data = self._load()
        find = data.get("tool", {}).get("setuptools", {}).get("packages", {}).get("find", {})
        assert find.get("where") == ["src"], (
            "[tool.setuptools.packages.find] where must be ['src'] to enforce src/ layout"
        )

    def test_ruff_config_present(self) -> None:
        data = self._load()
        ruff = data.get("tool", {}).get("ruff", {})
        assert ruff.get("target-version"), "ruff target-version must be set"
        assert ruff.get("line-length"), "ruff line-length must be set"

    def test_mypy_strict_enabled(self) -> None:
        data = self._load()
        mypy = data.get("tool", {}).get("mypy", {})
        assert mypy.get("strict") is True, "mypy strict must be true"

    def test_pytest_testpaths_configured(self) -> None:
        data = self._load()
        pytest_opts = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
        assert "tests" in pytest_opts.get("testpaths", [])

    def test_gpu_marker_declared(self) -> None:
        data = self._load()
        markers = data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("markers", [])
        assert any("gpu" in m for m in markers), (
            "gpu marker must be declared in [tool.pytest.ini_options]"
        )

    def test_dev_optional_deps_declared(self) -> None:
        data = self._load()
        dev_deps = (
            data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
        )
        expected_tools = ["ruff", "mypy", "pytest"]
        for tool in expected_tools:
            assert any(tool in dep for dep in dev_deps), (
                f"{tool} must be in [project.optional-dependencies] dev group"
            )
