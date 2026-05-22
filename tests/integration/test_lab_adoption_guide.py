"""Lab Adoption Guide content validation — Story 5.2.

Validates that docs/lab-adoption-guide.md satisfies the acceptance criteria:
correct type names (AdaptationConfig/AdaptationRun, not AdaptationJob), working
TrajectoryBuffer examples, BibTeX citation block, and benchmark performance reference.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
GUIDE = PROJECT_ROOT / "docs" / "lab-adoption-guide.md"


def _guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


class TestGuideExistence:
    """AC #1: docs/lab-adoption-guide.md must exist."""

    def test_guide_exists(self) -> None:
        assert GUIDE.exists(), (
            "docs/lab-adoption-guide.md not found — create or restore the file"
        )

    def test_guide_is_non_empty(self) -> None:
        assert GUIDE.stat().st_size > 0, "docs/lab-adoption-guide.md is empty"


class TestNamedAdaptationRunSection:
    """AC #1: guide must contain AdaptationConfig and AdaptationRun (not AdaptationJob)."""

    def test_contains_adaptation_config(self) -> None:
        text = _guide_text()
        assert "AdaptationConfig" in text, (
            "docs/lab-adoption-guide.md must reference AdaptationConfig in a code example"
        )

    def test_contains_adaptation_run(self) -> None:
        text = _guide_text()
        assert "AdaptationRun" in text, (
            "docs/lab-adoption-guide.md must reference AdaptationRun in a code example"
        )

    def test_does_not_contain_adaptation_job(self) -> None:
        text = _guide_text()
        assert "AdaptationJob" not in text, (
            "docs/lab-adoption-guide.md must NOT reference AdaptationJob — "
            "that type does not exist (it was split into AdaptationConfig + AdaptationRun)"
        )

    def test_correct_import_path_for_types(self) -> None:
        text = _guide_text()
        assert "physlink.core._types" in text, (
            "docs/lab-adoption-guide.md must show the correct import path "
            "'from physlink.core._types import ...'"
        )


class TestTrajectoryPersistenceSection:
    """AC #1: guide must contain TrajectoryBuffer.export and TrajectoryBuffer.load examples."""

    def test_contains_trajectory_buffer_export(self) -> None:
        text = _guide_text()
        assert "TrajectoryBuffer" in text, (
            "docs/lab-adoption-guide.md must reference TrajectoryBuffer"
        )
        assert re.search(r"\.export\s*\(", text), (
            "docs/lab-adoption-guide.md must include a TrajectoryBuffer.export() example"
        )

    def test_contains_trajectory_buffer_load(self) -> None:
        text = _guide_text()
        assert re.search(r"TrajectoryBuffer\.load\s*\(", text), (
            "docs/lab-adoption-guide.md must include a TrajectoryBuffer.load() class-method example"
        )


class TestBibTexCitationSection:
    """AC #1: guide must contain a BibTeX @software or @misc entry."""

    def test_contains_bibtex_entry(self) -> None:
        text = _guide_text()
        assert re.search(r"@(software|misc)\s*\{", text), (
            "docs/lab-adoption-guide.md must contain a @software or @misc BibTeX citation block"
        )

    def test_bibtex_entry_has_required_fields(self) -> None:
        text = _guide_text()
        for field in ("title", "author", "year", "url"):
            assert field in text, (
                f"BibTeX block in docs/lab-adoption-guide.md is missing required field: {field}"
            )


class TestBenchmarkPerformanceSection:
    """AC #1: guide must link to benchmark baseline JSON or CI badge for performance claims."""

    def test_contains_benchmark_baseline_json(self) -> None:
        text = _guide_text()
        assert "benchmark_baseline.json" in text, (
            "docs/lab-adoption-guide.md must reference tests/perf/baselines/benchmark_baseline.json"
        )

    def test_contains_ci_badge_reference(self) -> None:
        text = _guide_text()
        assert "test-gpu" in text, (
            "docs/lab-adoption-guide.md must reference the GPU CI workflow badge (test-gpu)"
        )


README = PROJECT_ROOT / "README.md"


class TestReadmeLink:
    """AC #2: Lab Adoption Guide must be linked from the README action bar."""

    def test_readme_exists(self) -> None:
        assert README.exists(), "README.md not found at project root"

    def test_readme_has_evaluate_for_your_lab_text(self) -> None:
        text = README.read_text(encoding="utf-8")
        assert "Evaluate for your lab" in text, (
            "README.md must contain the 'Evaluate for your lab' link text (AC #2)"
        )

    def test_readme_evaluate_link_points_to_guide(self) -> None:
        text = README.read_text(encoding="utf-8")
        assert "docs/lab-adoption-guide.md" in text, (
            "README.md must link to docs/lab-adoption-guide.md (AC #2)"
        )


class TestPrerequisitesSection:
    """AC #1: guide must include prerequisites with pip install and version requirement."""

    def test_prerequisites_section_exists(self) -> None:
        text = _guide_text()
        assert re.search(r"(?i)prerequisites?", text), (
            "docs/lab-adoption-guide.md must contain a Prerequisites section"
        )

    def test_pip_install_example(self) -> None:
        text = _guide_text()
        assert "pip install" in text, (
            "docs/lab-adoption-guide.md must include a pip install example"
        )

    def test_version_requirement_present(self) -> None:
        text = _guide_text()
        assert "0.1.2" in text, (
            "docs/lab-adoption-guide.md must reference version 0.1.2"
        )

    def test_doctor_call_in_verify_step(self) -> None:
        text = _guide_text()
        assert "doctor()" in text, (
            "docs/lab-adoption-guide.md must include physlink.doctor() for environment verification"
        )


class TestCodeBlockQuality:
    """AC #1: types and imports must appear inside Python fenced code blocks, not only in prose."""

    @staticmethod
    def _python_code_blocks() -> list[str]:
        return re.findall(r"```python\n(.*?)```", _guide_text(), re.DOTALL)

    def test_adaptation_config_in_python_code_block(self) -> None:
        combined = "\n".join(self._python_code_blocks())
        assert "AdaptationConfig" in combined, (
            "AdaptationConfig must appear inside a ```python code block, not only in prose"
        )

    def test_adaptation_run_in_python_code_block(self) -> None:
        combined = "\n".join(self._python_code_blocks())
        assert "AdaptationRun" in combined, (
            "AdaptationRun must appear inside a ```python code block, not only in prose"
        )

    def test_correct_import_in_python_code_block(self) -> None:
        combined = "\n".join(self._python_code_blocks())
        assert "from physlink.core._types import" in combined, (
            "The import 'from physlink.core._types import ...' must appear inside a ```python code block"
        )

    def test_trajectory_buffer_export_in_python_code_block(self) -> None:
        combined = "\n".join(self._python_code_blocks())
        assert re.search(r"\.export\s*\(", combined), (
            "TrajectoryBuffer.export() must appear inside a ```python code block"
        )

    def test_trajectory_buffer_load_in_python_code_block(self) -> None:
        combined = "\n".join(self._python_code_blocks())
        assert re.search(r"TrajectoryBuffer\.load\s*\(", combined), (
            "TrajectoryBuffer.load() must appear inside a ```python code block"
        )


class TestBibTexCodeBlock:
    """AC #1: BibTeX citation must be in a ```bibtex fenced block with a version field."""

    @staticmethod
    def _bibtex_blocks() -> list[str]:
        return re.findall(r"```bibtex\n(.*?)```", _guide_text(), re.DOTALL)

    def test_bibtex_fenced_code_block_exists(self) -> None:
        assert self._bibtex_blocks(), (
            "docs/lab-adoption-guide.md must contain a ```bibtex fenced code block"
        )

    def test_bibtex_version_field(self) -> None:
        combined = "\n".join(self._bibtex_blocks())
        assert "version" in combined, (
            "BibTeX block must contain a version field (e.g. version = {0.1.2})"
        )
