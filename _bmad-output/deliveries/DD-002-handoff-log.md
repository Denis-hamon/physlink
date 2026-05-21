# Handoff Log — DD-002 Petra's Lab Standard Rollout

**Date:** 2026-05-21 | **Designer:** Denis | **Status:** ready_for_handoff

## Key Design Decisions

1. **DD-002 is content-only** — PhysLink controls text/structure, not HTML. GitHub/arXiv render everything.
2. **CHANGELOG is a governance signal, not a changelog** — Petra reads it to judge process maturity, not feature history
3. **Keep a Changelog format is mandatory** — `## [X.Y.Z] - YYYY-MM-DD` with `⚠️ **Breaking:**` + `> **Migration:**`
4. **Dual-path action bar (Hugo + Petra)** — README must serve both personas without cluttering the hero
5. **Domain Extension issue template serves both DD-002 and DD-003** — ship it before first lab outreach

## Critical Gotchas

- arXiv paper is a hard dependency — if Petra can't find the paper, the entire scenario fails
- CHANGELOG must be maintained incrementally (per PR) — batch updates at release are a NO-GO signal
- The "Evaluate for your lab →" action bar link must be in the first viewport on desktop
- PR template CHANGELOG checkbox creates a feedback loop with 2.2 — both must ship together

## Open Questions Requiring Team Decision

- Dual-path action bar final design (Q1 in 2.1) — impacts DD-001 README too
- Domain Extension template ship date (2.5 Q1) — blocks DD-003 community return
- Physical invariants PR checklist item (2.5 Q2) — low effort, high Samuel signal

## Dependencies

- DD-001 must exist before CHANGELOG has real entries
- arXiv submission is an external dependency with unknown timeline
