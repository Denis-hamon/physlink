# Design Log: Worldchain

## Backlog
- [ ] Design GitHub README (Hugo & Petra)
- [ ] Design Colab Setup & physlink doctor
- [ ] Design Universal Space API (Colab Config)
- [ ] Design Adaptation Loop & Pipeline Debug Hooks
- [ ] Design Validation & Time-to-Science Callout
- [ ] Design Lab Adoption Guide
- [ ] Design ArXiv Position Paper Landing (Referral)

## Current
- [x] All three scenarios specified (01, 02, 03) — ready for validation phase

## Design Loop Status
| Scenario | Page | Status | Updated |
|----------|------|--------|---------|
| 01 | 1.1-github-readme | building | 2026-05-20 |
| 01 | 1.2-colab-setup | building | 2026-05-20 |
| 01 | 1.3-colab-configuration | building | 2026-05-20 |
| 01 | 1.4-colab-adaptation-loop | building | 2026-05-20 |
| 01 | 1.5-colab-validation | building | 2026-05-20 |
| 02 | 2.1-github-readme | specified | 2026-05-21 |
| 02 | 2.2-changelog | specified | 2026-05-21 |
| 02 | 2.3-arxiv-paper | specified | 2026-05-21 |
| 02 | 2.4-lab-adoption-guide | specified | 2026-05-21 |
| 02 | 2.5-github-templates | specified | 2026-05-21 |
| 03 | 3.1-arxiv-paper | specified | 2026-05-21 |
| 03 | 3.2-github-readme | specified | 2026-05-21 |
| 03 | 3.3-getting-started-domain | specified | 2026-05-21 |
| 03 | 3.4-colab-validation | specified | 2026-05-21 |
| 01 | 1.1-github-readme | specified | 2026-05-20 |
| 01 | 1.2-colab-setup | specified | 2026-05-20 |
| 01 | 1.3-colab-configuration | specified | 2026-05-20 |
| 01 | 1.4-colab-adaptation-loop | specified | 2026-05-20 |
| 01 | 1.5-colab-validation | specified | 2026-05-20 |

## Log
- **2026-05-20**: Initialized Phase 4 Design Log.
- **2026-05-20**: Specified Scenario 01 page 1.1 `github-readme` with layout, objects, content, interactions, states, validation, spacing, typography, and object registry.
- **2026-05-20**: Specified Scenario 01 page 1.2 `colab-setup` with Colab setup flow, `physlink doctor` diagnostics, Go/No-Go states, validation rules, and object registry.
- **2026-05-20**: Specified Scenario 01 page 1.3 `colab-configuration` with Universal Space API cells, summary/explainability checks, validation errors, and object registry.
- **2026-05-20**: Specified Scenario 01 page 1.4 `colab-adaptation-loop` with DreamerV3 fit flow, progress monitor, debug hooks, checkpoint recovery, export validation, and object registry.
- **2026-05-20**: Specified Scenario 01 page 1.5 `colab-validation` with triptych renderer, validation metrics, time-to-science callout, artifact export, sharing, recovery states, and object registry.
- **2026-05-21**: Specified Scenario 02 page 2.1 `github-readme` — same URL as 1.1 but documented through Petra's institutional filter: scan priority table (license → arXiv → maintenance → CHANGELOG), 2 new objects (maintenance badge + lab path CTA), dual-path action bar redesign proposal, 5 open questions on shared README design tensions.
- **2026-05-21**: Specified Scenario 02 page 2.2 `changelog` — GitHub file view spec: Keep a Changelog format, release entry structure, breaking change + migration note pattern, GO/NO-GO conditions for Petra, 5 states (healthy / thin / stale / hash-dump / absent), 4 open questions on CHANGELOG governance.
- **2026-05-21**: Specified Scenario 02 page 2.3 `arxiv-paper` (MOMENT OF TRUTH) — full dual-persona spec (Petra credential audit + Samuel domain vocabulary check), cross-persona scan map, paper content requirements (abstract structure, physical invariants section, benchmark table, GitHub link placement), 5 open questions on paper strategy.
- **2026-05-21**: Updated Scenario 03 page 3.1 `arxiv-paper` — delta spec referencing 2.3 as canonical source; documents Samuel's cold-discovery scan, physics vocabulary GO/NO-GO, and GitHub-link-as-exit pattern.
- **2026-05-21**: Specified Scenario 03 page 3.2 `github-readme` — delta spec referencing 1.1 as canonical source; documents Samuel's single-goal 10-second scan for `readme-links-domain-scientists-link`; design tension on link discoverability below fold; 2 open questions on Fast Action Bar entry and "Who is this for?" grid.
- **2026-05-21**: Specified Scenario 03 page 3.3 `getting-started-domain` (SAMUEL'S MOMENT OF TRUTH) — standalone documentation page for domain scientists; philosophy section naming "physical hallucinations" explicitly; `register_invariant()` API with mass conservation worked example; compliance report and histogram; CTA to Domain Scientists Colab demo; 4 open questions on domain vocabulary and API surface.
- **2026-05-21**: Specified Scenario 03 page 3.4 `colab-validation` — 8-cell Colab notebook spec; Cell 3 is Samuel's only edit (replace example_trajectories with CFD data); Cell 5 SUCCESS moment (`violations=0/N`); Cell 6 compliance histogram; Cell 8 community return ("What's next?" with GitHub Domain Extension issue link). Scenario 03 complete. All 14 UX specification pages across all three scenarios specified.
- **2026-05-21**: Validation audit completed — 14 pages, 0 critical issues, 4 warnings (W1: 1.x navigation format inconsistency; W2: Reference Materials section position; W3: delta spec registry annotation absent; W4: Python code blocks unlabeled). 32 open design questions remain. Report: `_progress/validation-report.md`.
- **2026-05-21**: Fixed W1+W2+W3 — added Previous/Next Step nav links to 1.1–1.5; moved Reference Materials sections to after Object Registry in all 1.x specs; added delta spec Object Registry pointer annotations to 3.1 and 3.2.
- **2026-05-21**: Fixed W4 — added `> **API Design Example**` callout before all 15 Python code blocks across 6 specs (1.2×1, 1.3×4, 1.4×5, 1.5×2, 3.3×2, 3.4×1). All 4 validation warnings resolved. Specs ready for development handoff.
- **2026-05-21**: Design Delivery complete — created DD-001/DD-002/DD-003 (YAML specs), TS-001/TS-002/TS-003 (test scenarios), and 3 handoff logs. Phase 4 UX Design fully handed off. Next: BMad implementation (Phase 5+). Dependency order: DD-001 → DD-002 → DD-003. BLOCKER: 3.2 Q1 (README discoverability for Samuel) must be resolved before DD-003 dev starts.
