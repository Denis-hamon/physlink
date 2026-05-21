# Scenario 01: Hugo's "Friday Afternoon Test"

## Strategic Context

- **Transaction**: Installation and first successful adaptation run on a custom domain in < 90 minutes.
- **Business Goal**: Objective 4 (Temporal Accessibility) & Objective 3 (Colab T4).
- **Persona**: Hugo (The Overwhelmed PhD).
- **Situation**: Friday afternoon at 3:30 PM at the lab, exhausted by a failing custom pipeline, seeking an alternative before the weekend.

## Driving Forces

- **Hope**: Get a coherent simulation result and a "win" before the weekend starts.
- **Worry**: Wasting 3 more hours on a "black box" that won't install or can't be debugged.

## Interaction Model

- **Device**: Desktop (Lab workstation).
- **Starting Point**: Arrives at GitHub README via research Slack/Twitter. Spends 90 seconds filtering: looks for a clear code snippet, green CI badge, and social proof (stars).

## Success Definition

- **User Success**: Sees a successful result GIF, notes the explicit time-saved callout, and **shares the notebook URL with a colleague**.
- **Business Success**: A skeptical researcher is converted into an active user and propagation vector.

## The Path (Shortest Journey)

1. **GitHub README** — Filters for trust (Code/CI/Stars) and clicks "Open in Colab".
2. **Colab Setup** — Installation and `physlink doctor` validation in 30s.
3. **Colab Configuration** — Defines robot via Universal Space API (30 lines). **MOMENT OF TRUTH**.
4. **Colab Adaptation Loop** — Runs adaptation with transparent progress (inspects via Debug Hooks if needed).
5. **Colab Validation** — Sees result GIF + Time-to-Science Callout, shares notebook URL. ✓
