"""Notebook execution tests for domain-scientist-colab.ipynb — P-15.

Executes the notebook in headless CPU mode with a steps=10 override.
Run separately from the main suite:

    pytest -m notebook_execution tests/integration/test_notebook_execution.py

Requires nbconvert + nbformat (included in the [notebook] extra):

    pip install "physlink[notebook]"

Why separate from the main suite:
- Execution takes ~5-10 s (full kernel boot + 10 adaptation steps)
- Complements the 58 structural tests in test_domain_scientist_notebook.py
  by validating *runtime* behaviour, not just JSON content
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
NOTEBOOK = PROJECT_ROOT / "notebooks" / "domain-scientist-colab.ipynb"

pytestmark = pytest.mark.notebook_execution


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nbconvert_imports() -> tuple:
    """Import nbconvert/nbformat, skip test if not installed."""
    try:
        import nbformat
        from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor

        return nbformat, ExecutePreprocessor, CellExecutionError
    except ImportError:
        pytest.skip(
            "nbconvert/nbformat not installed — run: pip install nbconvert nbformat"
        )


def _patched_notebook() -> dict:
    """Return notebook JSON with CI patches applied (no-op pip install, steps=10, Agg backend)."""
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]

    # Cell 0 (index 0): skip pip install — physlink is already installed as editable in CI
    cells[0]["source"] = [
        "pass  # pip install skipped in CI (physlink installed as editable dev dependency)\n"
    ]

    # Cell 4 (index 4): reduce steps for CPU speed  (100→10, checkpoint 50→5)
    src = "".join(cells[4]["source"])
    src = src.replace("steps=100", "steps=10").replace(
        "checkpoint_interval_steps=50", "checkpoint_interval_steps=5"
    )
    cells[4]["source"] = list(src)

    # Cell 5 (index 5): force non-interactive Agg backend before report.plot()
    src5 = "".join(cells[5]["source"])
    cells[5]["source"] = list(
        "import matplotlib\nmatplotlib.use('Agg')  # headless CI\n" + src5
    )

    return nb


# ---------------------------------------------------------------------------
# Module-scoped fixture — notebook executed once, results shared across tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def executed_nb(tmp_path_factory: pytest.TempPathFactory):
    """Execute the patched notebook once; yield the resulting nbformat NotebookNode."""
    nbformat, ExecutePreprocessor, CellExecutionError = _nbconvert_imports()

    work_dir = tmp_path_factory.mktemp("nb_execution")
    raw = _patched_notebook()
    nb_obj = nbformat.reads(json.dumps(raw), as_version=4)

    ep = ExecutePreprocessor(timeout=120, kernel_name="python3")
    try:
        ep.preprocess(nb_obj, {"metadata": {"path": str(work_dir)}})
    except CellExecutionError as exc:
        pytest.fail(f"Notebook execution raised CellExecutionError:\n{exc}")

    return nb_obj, work_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNotebookExecutes:
    """Notebook must execute end-to-end without errors."""

    def test_all_code_cells_have_no_error_output(self, executed_nb) -> None:
        nb_obj, _ = executed_nb
        for i, cell in enumerate(nb_obj.cells):
            if cell.cell_type != "code":
                continue
            for output in cell.outputs:
                assert output.output_type != "error", (
                    f"Cell {i + 1} (index {i}) produced an error output:\n"
                    f"  {output.get('ename', '')}: {output.get('evalue', '')}"
                )

    def test_all_code_cells_executed(self, executed_nb) -> None:
        nb_obj, _ = executed_nb
        for i, cell in enumerate(nb_obj.cells):
            if cell.cell_type == "code":
                assert cell.get("execution_count") is not None, (
                    f"Cell {i + 1} (index {i}) was not executed (execution_count is None)\n"
                    "  All code cells must execute in sequence"
                )


class TestCell4ComplianceOutput:
    """Cell 4 must produce a PASS compliance report at steps=10."""

    def _cell4_text(self, executed_nb) -> str:
        nb_obj, _ = executed_nb
        outputs = nb_obj.cells[4].outputs
        return "".join(
            o.get("text", "") + o.get("data", {}).get("text/plain", "")
            for o in outputs
        )

    def test_cell4_output_contains_mass_conservation(self, executed_nb) -> None:
        text = self._cell4_text(executed_nb)
        assert "mass_conservation" in text, (
            "Cell 4 output must contain 'mass_conservation'\n"
            f"  Actual output: {text[:400]!r}"
        )

    def test_cell4_output_contains_pass(self, executed_nb) -> None:
        text = self._cell4_text(executed_nb)
        assert "PASS" in text, (
            "Cell 4 output must contain 'PASS'\n"
            "  The compliance report must show mass_conservation: PASS with steps=10\n"
            f"  Actual output: {text[:400]!r}"
        )

    def test_cell4_output_shows_max_residual(self, executed_nb) -> None:
        text = self._cell4_text(executed_nb)
        assert "max_residual=" in text, (
            "Cell 4 summary must include 'max_residual=...'\n"
            f"  Actual output: {text[:400]!r}"
        )

    def test_cell4_output_shows_threshold(self, executed_nb) -> None:
        text = self._cell4_text(executed_nb)
        assert "threshold=" in text, (
            "Cell 4 summary must include 'threshold=...'\n"
            f"  Actual output: {text[:400]!r}"
        )

    def test_cell4_output_shows_violations(self, executed_nb) -> None:
        text = self._cell4_text(executed_nb)
        assert "violations=" in text, (
            "Cell 4 summary must include 'violations=X/N'\n"
            f"  Actual output: {text[:400]!r}"
        )


class TestCell2LoadsTrajectories:
    """Cell 2 must print trajectory count confirmation."""

    def test_cell2_confirms_trajectories_loaded(self, executed_nb) -> None:
        nb_obj, _ = executed_nb
        outputs = nb_obj.cells[2].outputs
        text = "".join(o.get("text", "") for o in outputs)
        assert "trajectories" in text.lower(), (
            "Cell 2 must print 'Loaded N trajectories.'\n"
            f"  Actual output: {text[:200]!r}"
        )


class TestCell6Export:
    """Cell 6 adapter.export() must create the physlink_export/ directory."""

    def test_cell6_export_directory_created(self, executed_nb) -> None:
        _, work_dir = executed_nb
        export_dir = work_dir / "physlink_export"
        assert export_dir.exists(), (
            f"physlink_export/ not found at {export_dir}\n"
            "  Cell 6 must call adapter.export(path='./physlink_export/')"
        )

    def test_cell6_export_prints_confirmation(self, executed_nb) -> None:
        nb_obj, _ = executed_nb
        outputs = nb_obj.cells[6].outputs
        text = "".join(o.get("text", "") for o in outputs)
        assert "Export complete" in text or "export" in text.lower(), (
            "Cell 6 must print export confirmation\n"
            f"  Actual output: {text[:200]!r}"
        )
