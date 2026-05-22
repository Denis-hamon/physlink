"""Domain Scientists landing page content validation — Story 6.2.

Validates that docs/domain-scientists.md satisfies the acceptance criteria:
explicit "physical hallucinations" in Philosophy section, mass_conservation
worked example with correct API and exact PASS output format, and CTA link
to the Domain Scientist Colab notebook.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
GUIDE = PROJECT_ROOT / "docs" / "domain-scientists.md"


def _guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def _python_code_blocks() -> list[str]:
    return re.findall(r"```python\n(.*?)```", _guide_text(), re.DOTALL)


class TestPageExistence:
    """docs/domain-scientists.md must exist and be non-empty."""

    def test_guide_exists(self) -> None:
        assert GUIDE.exists(), (
            "docs/domain-scientists.md not found\n"
            "  Fix: create the file as specified in Story 6.2"
        )

    def test_guide_is_non_empty(self) -> None:
        assert GUIDE.stat().st_size > 0, (
            "docs/domain-scientists.md is empty\n"
            "  Fix: write content per Story 6.2 AC #1, #2, #3"
        )


class TestPhysicalHallucinationsPhilosophy:
    """AC #1: Philosophy section must name 'physical hallucinations' explicitly."""

    def test_physical_hallucinations_verbatim(self) -> None:
        text = _guide_text()
        assert "physical hallucinations" in text, (
            "'physical hallucinations' does not appear verbatim in docs/domain-scientists.md\n"
            "  Fix: add the exact phrase 'physical hallucinations' — do not paraphrase"
        )

    def test_physics_blind_ml_explanation(self) -> None:
        text = _guide_text()
        assert "physics-blind" in text or "blind to physical" in text or "physics blind" in text, (
            "Philosophy section must explain that standard ML is physics-blind\n"
            "  Fix: add explanation of why standard ML models hallucinate physically impossible outputs"
        )


class TestMassConservationExample:
    """AC #2: mass_conservation worked example with correct API and exact output format."""

    def test_mass_conservation_fn_in_python_block(self) -> None:
        combined = "\n".join(_python_code_blocks())
        assert "mass_conservation" in combined, (
            "'mass_conservation' function definition must appear inside a ```python code block\n"
            "  Fix: add the mass_conservation fn definition in a fenced python block"
        )

    def test_register_invariant_call_in_python_block(self) -> None:
        combined = "\n".join(_python_code_blocks())
        assert "register_invariant(" in combined, (
            "'register_invariant(' call must appear inside a ```python code block\n"
            "  Fix: add the register_invariant() call in a fenced python block"
        )

    def test_pass_output_format(self) -> None:
        text = _guide_text()
        assert "mass_conservation: PASS" in text, (
            "PASS output line 'mass_conservation: PASS' not found in docs/domain-scientists.md\n"
            "  Fix: add exact output line 'mass_conservation: PASS (max_residual=X, threshold=Y, violations=Z/N)'"
        )

    def test_violations_zero_format(self) -> None:
        text = _guide_text()
        assert "violations=0/" in text, (
            "Exact format 'violations=0/N' not found in docs/domain-scientists.md\n"
            "  Fix: output line must contain 'violations=0/' matching format violations=0/N"
        )

    def test_pass_output_complete_format(self) -> None:
        """Full PASS line must include max_residual=, threshold=, violations=0/N (AC #2 exact format)."""
        text = _guide_text()
        assert re.search(
            r"mass_conservation: PASS \(max_residual=[\d.]+, threshold=[\d.]+, violations=0/\d+\)",
            text,
        ), (
            "PASS output is missing the full format with max_residual and threshold\n"
            "  Fix: output line must match "
            "'mass_conservation: PASS (max_residual=X, threshold=Y, violations=0/N)'"
        )

    def test_correct_import_path(self) -> None:
        """Import must use top-level physlink package, not physlink.compliance (wrong pre-Epic-4 path)."""
        combined = "\n".join(_python_code_blocks())
        assert "from physlink import" in combined, (
            "Correct import 'from physlink import ...' not found in python code block\n"
            "  Fix: use 'from physlink import DreamerV3Adapter, register_invariant'"
        )

    def test_wrong_import_absent(self) -> None:
        """The pre-Epic-4 wrong import path must not appear in any code block."""
        combined = "\n".join(_python_code_blocks())
        assert "from physlink.compliance import" not in combined, (
            "Wrong import 'from physlink.compliance import ...' found — this path does not exist\n"
            "  Fix: use 'from physlink import register_invariant' (top-level export)"
        )

    def test_fn_returns_float_type_hint(self) -> None:
        """fn must declare '-> float' return type per register_invariant API contract."""
        combined = "\n".join(_python_code_blocks())
        assert "-> float" in combined, (
            "Function return type hint '-> float' not found in python code block\n"
            "  Fix: mass_conservation fn must declare 'def mass_conservation(trajectory: dict) -> float:'"
        )


class TestIllustrativeNote:
    """AC #2: illustrative note that any physical domain works with the same pattern."""

    def test_multi_domain_note_exists(self) -> None:
        text = _guide_text()
        has_cfd = "CFD" in text
        has_energy = "energy conservation" in text
        has_momentum = "momentum conservation" in text
        assert has_cfd or has_energy or has_momentum, (
            "Illustrative note about multiple physical domains not found\n"
            "  Fix: add note that any domain works (CFD: energy conservation, "
            "robotics: momentum conservation, climate: mass conservation)"
        )

    def test_multi_domain_note_all_three_domains(self) -> None:
        """All three canonical domains from AC #2 must be explicitly mentioned."""
        text = _guide_text()
        assert "CFD" in text, (
            "'CFD' not mentioned in illustrative note\n"
            "  Fix: note must list 'CFD: energy conservation' as one of the example domains"
        )
        assert "energy conservation" in text, (
            "'energy conservation' not mentioned in illustrative note\n"
            "  Fix: note must list 'CFD: energy conservation' as one of the example domains"
        )
        assert "momentum conservation" in text, (
            "'momentum conservation' not mentioned in illustrative note\n"
            "  Fix: note must list 'robotics: momentum conservation' as one of the example domains"
        )


class TestColabCTA:
    """AC #3: CTA link must point to Domain Scientist Colab notebook."""

    def test_colab_notebook_link_present(self) -> None:
        text = _guide_text()
        assert "notebooks/domain-scientist-colab.ipynb" in text, (
            "CTA link to 'notebooks/domain-scientist-colab.ipynb' not found\n"
            "  Fix: add a prominent CTA link pointing to notebooks/domain-scientist-colab.ipynb"
        )

    def test_colab_url_format(self) -> None:
        """CTA must use a proper Google Colab URL, not just a local path reference."""
        text = _guide_text()
        assert "colab.research.google.com" in text, (
            "Google Colab URL not found — link must use 'colab.research.google.com'\n"
            "  Fix: use the Colab URL pattern: "
            "https://colab.research.google.com/github/YOUR-ORG/physlink/blob/main/"
            "notebooks/domain-scientist-colab.ipynb"
        )
