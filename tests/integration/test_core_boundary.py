"""AST guard: core/ must not import from physlink.adapters/.

Enforces architectural boundary. BOUNDARY_EXCEPTIONS list is audited on every review.
"""

from __future__ import annotations

import ast
from pathlib import Path

BOUNDARY_EXCEPTIONS: list[str] = []  # explicit empty list — reviewed each PR


def get_core_files() -> list[Path]:
    core_dir = Path(__file__).parent.parent.parent / "src" / "physlink" / "core"
    return list(core_dir.rglob("*.py"))


def test_core_does_not_import_adapters() -> None:
    violations: list[str] = []
    for filepath in get_core_files():
        tree = ast.parse(filepath.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("physlink.adapters"):
                    key = f"{filepath}:{module}"
                    if key not in BOUNDARY_EXCEPTIONS:
                        violations.append(f"{filepath}: from {module} import ...")
    assert not violations, "core/ → adapters/ boundary violated:\n" + "\n".join(violations)
