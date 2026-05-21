# Handoff Log — DD-003 Samuel's Dignity Validation

**Date:** 2026-05-21 | **Designer:** Denis | **Status:** ready_for_handoff

## Key Design Decisions

1. **"Physical hallucinations" must be named before showing any code** — Samuel's dignity comes first
2. **register_invariant() takes a plain Python callable** — no subclasses, no decorators. Samuel writes his own fn.
3. **mode="hard" rejects, mode="soft" penalizes** — hard is the trust signal; soft is the adoption ramp
4. **PASS output format is exact**: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"` — do not change
5. **report.violations() must be human-readable** — field values + residual + "Possible cause:" — not a stack trace

## Critical Gotchas

- README discoverability (3.2 Q1) is a DESIGN BLOCKER — if `readme-links-domain-scientists-link` is below fold on 1440px, Samuel's scenario fails before reaching 3.3. Resolve before dev starts.
- The compliance histogram threshold line is the visual proof — it must be clearly labeled and rendered inline in Colab
- Cell 3 "Edit this cell" instruction must use ⚠️ and be prominent — it is the ONLY cell Samuel modifies

## Open Questions Requiring Team Decision

- README Fast Action Bar entry for Samuel (3.2 Q1) — **BLOCKER**
- Which physical domains are explicitly listed in 3.3 beyond CFD? (3.3 Q1)
- Multi-invariant example in 3.3 docs? (3.3 Q2)

## Dependencies

- DD-001 (DreamerV3Adapter) must exist before register_invariant() can be implemented
- DD-002 (readme-links-domain-scientists-link + domain_extension.md) must exist
