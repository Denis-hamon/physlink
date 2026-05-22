# PhysLink — Development Guide

## Prerequisites

| Requirement | Version | Notes |
|------------|---------|-------|
| Python | ≥ 3.10 | Tested on 3.12 in CI |
| uv | any | Recommended dependency manager |
| pip | any | Alternative to uv |
| git | any | |
| PyTorch | any (optional) | Required only for GPU training and adapter tests |

---

## Local Setup

### With uv (recommended)

```bash
git clone https://github.com/Denis-hamon/physlink.git
cd physlink
uv venv
uv pip install -e ".[dev]"
pre-commit install
```

### With pip

```bash
git clone https://github.com/Denis-hamon/physlink.git
cd physlink
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

### GPU support (optional)

```bash
pip install torch --extra-index-url https://download.pytorch.org/whl/cu121
```

---

## Environment Verification

```python
import physlink
report = physlink.doctor()
# Prints Go/No-Go diagnostic table to stdout
# Returns DiagnosticReport with verdict "GO" or "NO-GO"
```

---

## Development Commands

### Lint

```bash
ruff check src/
ruff check --fix src/   # auto-fix
```

### Type Check

```bash
mypy --strict src/physlink/core/      # strict mode on core/
mypy src/physlink/adapters/           # relaxed (PyTorch stubs incomplete)
mypy src/physlink/utils/              # relaxed (matplotlib/PIL stubs incomplete)
```

### Tests

```bash
# CPU suite (fast, no GPU required)
pytest -m "not gpu" tests/ -v

# All tests including GPU
pytest tests/ -v

# Specific test file
pytest tests/unit/core/test_spaces.py -v

# With coverage
pytest -m "not gpu" tests/ --cov=src/physlink --cov-report=term-missing
```

### Performance Benchmarks

```bash
# Run benchmarks and compare vs baseline
pytest tests/perf/ --benchmark-compare=tests/perf/baselines/benchmark_baseline.json --benchmark-compare-fail=min:10%

# Generate a new baseline (Colab T4 GPU only)
pytest tests/perf/ --benchmark-json=tests/perf/baselines/benchmark_baseline.json
```

### Documentation

```bash
# Build docs (strict — fails on warnings)
mkdocs build --strict

# Serve docs locally with live reload
mkdocs serve
# Then open http://127.0.0.1:8000
```

### Pre-commit

```bash
pre-commit run --all-files   # run ruff check + format on all files
```

---

## Project Structure for Development

```
src/physlink/
├── core/        ← add new pure-Python primitives here
├── adapters/    ← add new ML backend adapters here (subclass BaseAdapter)
└── utils/       ← add standalone utilities here
```

**Rule for adapters and utils**: All ML framework imports (`torch`, `matplotlib`, `PIL`, etc.) **must** stay inside function bodies. Never import them at module level. This ensures `import physlink` works without these dependencies installed.

**Rule for core/**: Zero ML imports. mypy strict mode enforced. Every public class/function needs a Google-style docstring with Args, Returns, Raises, and Example sections.

---

## Adding a New Adapter

1. Create `src/physlink/adapters/my_adapter.py`
2. Subclass `BaseAdapter` and implement `fit()`, `visualize()`, `export()`, `explain()`
3. Import lazily: `import torch` inside `fit()` body, not at module level
4. Add to `src/physlink/__init__.py` if promoting to public API
5. Add unit tests in `tests/unit/adapters/test_my_adapter_cpu.py`
6. GPU tests go in `tests/unit/adapters/test_my_adapter_gpu.py` with `@pytest.mark.gpu`

---

## Common Development Tasks

### Check that core/ has no torch imports

```bash
pytest tests/integration/test_core_no_torch_import.py -v
pytest tests/integration/test_core_boundary.py -v
```

### Verify docstring completeness

```bash
pytest tests/integration/test_docstring_completeness.py -v
```

### Validate CI config

```bash
pytest tests/integration/test_ci_pipeline_config.py -v
```

### Validate API stability (no regression in public symbols)

```bash
pytest tests/integration/test_api_stability.py -v
```

---

## Test Fixtures

`tests/conftest.py` provides:

```python
@pytest.fixture
def synthetic_trajectories() -> list[dict]:
    """1000 numpy-only trajectories — no GPU required."""
    rng = np.random.default_rng(42)
    return [{"obs": rng.random(7), "action": rng.random(3)} for _ in range(1000)]
```

Use `synthetic_trajectories` in any test that needs trajectory data without a GPU.

---

## mypy Configuration Notes

`pyproject.toml` has two `[[tool.mypy.overrides]]` blocks:

```toml
[[tool.mypy.overrides]]
module = "physlink.adapters.*"
ignore_missing_imports = true
strict = false   # PyTorch stubs incomplete — ADR-002 defers to v0.3.0

[[tool.mypy.overrides]]
module = "physlink.utils.*"
ignore_missing_imports = true
# matplotlib/PIL have partial stubs
```

`core/` runs under `strict = true` at the top level — no overrides.

---

## IDE Setup

No special configuration required. The `pyproject.toml` covers ruff and mypy. If your IDE uses these tools natively (VS Code with Pylance + Ruff extension, PyCharm with mypy plugin), they will pick up the config automatically.

Recommended VS Code extensions:
- `charliermarsh.ruff` — linting and formatting
- `ms-python.mypy-type-checker` — type checking
- `ms-python.python` — Python language support
