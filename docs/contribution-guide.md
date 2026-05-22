# PhysLink — Contribution Guide

## Code Quality Standards

### Linting

```bash
ruff check src/
ruff check --fix src/  # auto-fix where possible
```

Rules active: `E, F, W, I, N, UP, ANN, RUF` — includes annotations (ANN) and NumPy/Ruff-specific rules (RUF). Excludes `_bmad*`, `.venv`, `dist`, `build`.

### Type Checking

```bash
mypy --strict src/physlink/core/    # strict on core/
```

`adapters/` and `utils/` run with `ignore_missing_imports = true` and `strict = false` (PyTorch/matplotlib stubs are incomplete — tracked in ADR-002, deferred to v0.3.0).

### Docstrings

All public classes and functions must have **Google-style docstrings** with:
- One-line summary
- `Args:` section (all parameters documented)
- `Returns:` section
- `Raises:` section (all exceptions documented)
- `Example:` section with a working code snippet

### Error Messages

All `PhysLinkError` subclass messages must follow the **Got/Expected/Fix** template:
```
Got:      <what was actually received>
Expected: <what was expected>
Fix:      <actionable instruction>
```

### Import Discipline

**Core layer** (`core/`): no ML framework imports anywhere, including inside functions.  
**Adapters/utils**: torch, matplotlib, PIL, etc. must be imported **inside function bodies** only. Never at module level.

---

## Pre-commit Hooks

Install on first setup:
```bash
pre-commit install
```

Hooks configured (`.pre-commit-config.yaml`):
- `ruff` (v0.4.10, pinned) — lint with auto-fix
- `ruff-format` — formatting

---

## Pull Request Process

1. Ensure `test-cpu` CI passes locally:
   ```bash
   ruff check src/
   mypy --strict src/physlink/core/
   pytest -m "not gpu" tests/ -v
   mkdocs build --strict
   ```

2. For changes to public API: update `CHANGELOG.md` under `[Unreleased]`.

3. For breaking changes, use the standard format in `CHANGELOG.md`:
   ```markdown
   ⚠️ **Breaking:** description
   > **Migration:** migration instructions
   ```

4. For test additions: maintain coverage of `core/` boundaries. Integration tests in `tests/integration/` often verify file content (README, CHANGELOG, docs) — update them when those files change.

5. For new adapters: follow the adapter addition guide in `development-guide.md`.

---

## Commit Conventions

```
feat:     new user-facing feature
fix:      bug fix
chore:    maintenance, tooling, release
docs:     documentation only
test:     test additions or corrections
refactor: non-breaking internal restructuring
```

---

## GPU Testing

GPU tests (`@pytest.mark.gpu`) run on self-hosted T4 in CI (tag-triggered). For local GPU testing:

```bash
pytest -m "gpu" tests/ -v
```

If you change performance-sensitive code, run benchmarks against the baseline:
```bash
pytest tests/perf/ \
  --benchmark-compare=tests/perf/baselines/benchmark_baseline.json \
  --benchmark-compare-fail=min:10%
```

If a benchmark regression is intentional, regenerate the baseline on a T4 GPU and commit it (preserving `"hardware": "T4 GPU"` annotation).

---

## Versioning

PhysLink follows [Semantic Versioning](https://semver.org/):
- `MAJOR` — backward-incompatible public API changes
- `MINOR` — new backward-compatible features
- `PATCH` — backward-compatible bug fixes

The public API surface is exactly the 7 symbols in `physlink.__all__`. Any change to their signatures is a potential breaking change.

---

## RC Process (v0.2+)

Before each minor release, publish a release candidate tag (`vX.Y.0rc1`) and allow 48 hours for community testing before promoting to the final release.
