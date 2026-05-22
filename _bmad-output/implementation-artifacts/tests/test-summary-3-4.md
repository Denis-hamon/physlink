# Test Automation Summary — Story 3.4: Safetensors Checkpoint Auto-Save and Recovery

**Date:** 2026-05-22
**Story:** 3.4 — Safetensors Checkpoint Auto-Save and Recovery
**physlink version:** 0.1.0

## Generated Tests

### CPU Tests (no GPU required)

**Pre-existing — `TestCheckpointLoadErrors`** (`tests/unit/adapters/test_dreamer_cpu.py`)

- [x] `test_load_checkpoint_raises_corrupt_on_nonexistent_file` — AC#2: corrupt error on missing file
- [x] `test_load_checkpoint_raises_corrupt_when_physlink_version_key_missing` — AC#2: corrupt error on absent metadata key
- [x] `test_load_checkpoint_raises_version_error_on_incompatible_major_minor` — AC#2: version error on major.minor mismatch
- [x] `test_checkpoint_version_error_carries_checkpoint_version` — AC#2: structured attribute `checkpoint_version`
- [x] `test_checkpoint_version_error_carries_current_version` — AC#2: structured attribute `current_version`
- [x] `test_load_checkpoint_forward_compatible_extra_keys_no_error` — AC#4: extra metadata keys silently ignored
- [x] `test_load_checkpoint_same_minor_version_compatible` — AC#4: same major.minor is compatible

**New (gap-fill) — `TestSaveCheckpointFunction`** (`tests/unit/adapters/test_dreamer_cpu.py`)

- [x] `test_save_checkpoint_creates_directory_if_not_exists` — AC#1: `os.makedirs(exist_ok=True)` creates nested dir
- [x] `test_save_checkpoint_returns_path_ending_with_step_filename` — AC#1: return type `str`, filename pattern `checkpoint_step_{N}.safetensors`
- [x] `test_save_checkpoint_prints_checkpoint_saved_message` — AC#1: `[physlink] Checkpoint saved:` printed to stdout with absolute path

**New (gap-fill) — `TestCheckCheckpointMetadata`** (`tests/unit/adapters/test_dreamer_cpu.py`)

- [x] `test_returns_metadata_dict_on_valid_checkpoint` — AC#2 happy path: returns `dict[str, str]` with `physlink_version`
- [x] `test_corrupt_error_message_contains_got_expected_fix` — architecture requirement: Got/Expected/Fix format on `CheckpointCorruptError`
- [x] `test_version_error_message_contains_got_expected_fix` — architecture requirement: Got/Expected/Fix format on `CheckpointVersionError`

### GPU Tests (`@pytest.mark.gpu`)

**Pre-existing — `TestFitCheckpoint`** (`tests/unit/adapters/test_dreamer_gpu.py`)

- [x] `test_fit_writes_checkpoint_files_at_interval` — AC#1: files exist at correct paths after fit()
- [x] `test_checkpoint_metadata_contains_all_required_keys` — AC#1: all 4 metadata keys present
- [x] `test_checkpoint_step_metadata_matches_step_number` — AC#1: `checkpoint_step` stored as string `"1"`
- [x] `test_checkpoint_adapter_class_is_dreamerv3adapter` — AC#1: `adapter_class == "DreamerV3Adapter"`
- [x] `test_load_checkpoint_restores_model_weights` — AC#3: model weights match after load
- [x] `test_fit_after_load_checkpoint_completes_without_error` — AC#3/NFR-10: full resume flow
- [x] `test_fit_checkpoint_writing_is_idempotent` — AC#3/NFR-09: two sequential fit() calls without corruption

## Coverage

| Acceptance Criterion | CPU Tests | GPU Tests | Status |
|---|---|---|---|
| AC#1 — File written, filename with step, 4 metadata keys, path printed | 3 (new gap-fill) | 4 | ✅ Full |
| AC#2 — CheckpointVersionError / CorruptError with attributes + message format | 5 + 2 (new gap-fill) | — | ✅ Full |
| AC#3 — Resume from checkpoint (NFR-10) | — | 2 | ✅ Full |
| AC#4 — Forward-compatible, version check on major.minor only | 2 | — | ✅ Full |

- CPU tests: 13 total (7 pre-existing + 6 new gap-fill)
- GPU tests: 7 total (pre-existing)
- **Total: 20 tests**

## Gap-Fill Summary

The 6 new CPU tests covered three gaps not addressed by the story's specified tasks:

1. **`_save_checkpoint()` direct function coverage** — The story only specified testing checkpoint behavior via `fit()` (GPU). Added 3 CPU tests that call `_save_checkpoint()` directly with `torch.nn.Linear` stubs, validating directory creation, return value, and print output.

2. **`_check_checkpoint_metadata()` happy path** — Only error cases were specified. Added test for the success path returning a valid `dict[str, str]`.

3. **Got/Expected/Fix error message format** — Architecture requirement (from `architecture.md#Error Message Patterns`) was untested. Added 2 tests asserting `Got:`, `Expected:`, `Fix:` keywords appear in both error types.

## Test Run Results

```
87 passed, 3 warnings in 0.75s   (CPU suite — pytest tests/unit/adapters/test_dreamer_cpu.py -m "not gpu")
ruff check src/ → All checks passed!
```

GPU tests (`@pytest.mark.gpu`) require CUDA and are excluded from the CPU CI job.

## Next Steps

- GPU tests in `TestFitCheckpoint` run automatically in the GPU CI job
- No additional edge cases identified beyond the 20 tests above
