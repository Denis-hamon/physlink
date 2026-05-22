"""Story 2.6 AC #1: Google-style docstring completeness on all public symbols.

Validates that every public function in physlink.core/ and physlink.utils/ has
the required Google-style sections and that from __future__ import annotations
is present in all core/*.py modules.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from physlink.core.spaces import ActionSpace, ObservationSpace
from physlink.utils.diagnostics import doctor


def _docstring_sections(obj: object) -> set[str]:
    """Return Google-style section header names found in obj's docstring."""
    doc = inspect.getdoc(obj)
    if not doc:
        return set()
    sections: set[str] = set()
    for line in doc.splitlines():
        stripped = line.strip()
        if (
            stripped.endswith(":")
            and not stripped.startswith(">>>")
            and " " not in stripped.rstrip(":")
        ):
            sections.add(stripped[:-1])
    return sections


class TestObservationSpaceDocstrings:
    def test_class_docstring_exists(self) -> None:
        assert inspect.getdoc(ObservationSpace) is not None

    def test_class_docstring_non_empty(self) -> None:
        doc = inspect.getdoc(ObservationSpace)
        assert doc is not None and len(doc.strip()) > 0

    def test_from_proprioception_docstring_exists(self) -> None:
        assert inspect.getdoc(ObservationSpace.from_proprioception) is not None

    def test_from_proprioception_has_args(self) -> None:
        sections = _docstring_sections(ObservationSpace.from_proprioception)
        assert "Args" in sections, (
            "ObservationSpace.from_proprioception docstring missing Args: section (AC #1)"
        )

    def test_from_proprioception_has_returns(self) -> None:
        sections = _docstring_sections(ObservationSpace.from_proprioception)
        assert "Returns" in sections, (
            "ObservationSpace.from_proprioception docstring missing Returns: section (AC #1)"
        )

    def test_from_proprioception_has_raises(self) -> None:
        sections = _docstring_sections(ObservationSpace.from_proprioception)
        assert "Raises" in sections, (
            "ObservationSpace.from_proprioception docstring missing Raises: section (AC #1)"
        )

    def test_from_proprioception_has_example(self) -> None:
        sections = _docstring_sections(ObservationSpace.from_proprioception)
        assert "Example" in sections, (
            "ObservationSpace.from_proprioception docstring missing Example: section (AC #1)"
        )

    def test_explain_docstring_exists(self) -> None:
        assert inspect.getdoc(ObservationSpace.explain) is not None

    def test_explain_has_returns(self) -> None:
        sections = _docstring_sections(ObservationSpace.explain)
        assert "Returns" in sections, (
            "ObservationSpace.explain docstring missing Returns: section (AC #1)"
        )

    def test_explain_has_example(self) -> None:
        sections = _docstring_sections(ObservationSpace.explain)
        assert "Example" in sections, (
            "ObservationSpace.explain docstring missing Example: section (AC #1)"
        )


class TestActionSpaceDocstrings:
    def test_class_docstring_exists(self) -> None:
        assert inspect.getdoc(ActionSpace) is not None

    def test_class_docstring_non_empty(self) -> None:
        doc = inspect.getdoc(ActionSpace)
        assert doc is not None and len(doc.strip()) > 0

    def test_continuous_docstring_exists(self) -> None:
        assert inspect.getdoc(ActionSpace.continuous) is not None

    def test_continuous_has_args(self) -> None:
        sections = _docstring_sections(ActionSpace.continuous)
        assert "Args" in sections, (
            "ActionSpace.continuous docstring missing Args: section (AC #1)"
        )

    def test_continuous_has_returns(self) -> None:
        sections = _docstring_sections(ActionSpace.continuous)
        assert "Returns" in sections, (
            "ActionSpace.continuous docstring missing Returns: section (AC #1)"
        )

    def test_continuous_has_raises(self) -> None:
        sections = _docstring_sections(ActionSpace.continuous)
        assert "Raises" in sections, (
            "ActionSpace.continuous docstring missing Raises: section (AC #1)"
        )

    def test_continuous_has_example(self) -> None:
        sections = _docstring_sections(ActionSpace.continuous)
        assert "Example" in sections, (
            "ActionSpace.continuous docstring missing Example: section (AC #1)"
        )

    def test_explain_docstring_exists(self) -> None:
        assert inspect.getdoc(ActionSpace.explain) is not None

    def test_explain_has_returns(self) -> None:
        sections = _docstring_sections(ActionSpace.explain)
        assert "Returns" in sections, (
            "ActionSpace.explain docstring missing Returns: section (AC #1)"
        )

    def test_explain_has_example(self) -> None:
        sections = _docstring_sections(ActionSpace.explain)
        assert "Example" in sections, (
            "ActionSpace.explain docstring missing Example: section (AC #1)"
        )


class TestDoctorDocstring:
    def test_doctor_docstring_exists(self) -> None:
        assert inspect.getdoc(doctor) is not None

    def test_doctor_has_returns(self) -> None:
        sections = _docstring_sections(doctor)
        assert "Returns" in sections, (
            "doctor() docstring missing Returns: section (AC #1)"
        )

    def test_doctor_has_example(self) -> None:
        sections = _docstring_sections(doctor)
        assert "Example" in sections, (
            "doctor() docstring missing Example: section (AC #1)"
        )


class TestFutureAnnotationsInCore:
    """AC #1: from __future__ import annotations must be present in all core/*.py."""

    @pytest.fixture
    def core_dir(self) -> Path:
        return Path(__file__).parent.parent.parent / "src" / "physlink" / "core"

    def test_types_has_future_annotations(self, core_dir: Path) -> None:
        assert "from __future__ import annotations" in (core_dir / "_types.py").read_text()

    def test_spaces_has_future_annotations(self, core_dir: Path) -> None:
        assert "from __future__ import annotations" in (core_dir / "spaces.py").read_text()

    def test_exceptions_has_future_annotations(self, core_dir: Path) -> None:
        assert "from __future__ import annotations" in (core_dir / "exceptions.py").read_text()

    def test_adapter_has_future_annotations(self, core_dir: Path) -> None:
        assert "from __future__ import annotations" in (core_dir / "adapter.py").read_text()

    def test_validation_has_future_annotations(self, core_dir: Path) -> None:
        assert "from __future__ import annotations" in (core_dir / "validation.py").read_text()
