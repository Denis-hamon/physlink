# Target Users: PhysLink

**Step:** Step 7 - Identify Target Users
**Completed:** 2026-05-20

---

## Primary User: The "Ambitious PhD/Post-Doc"

| Dimension | Profile |
|-----------|---------|
| **Role** | 2nd or 3rd year PhD student / Post-doc in AI, Robotics, or Physics. |
| **Context** | Working at a mid-tier lab (ETH, MIT, INRIA) with limited proprietary infra. |
| **Frustrations** | Spending 90% of time on custom PyTorch plumbing; lack of reproducible standards; inability to compare results with other labs easily. |
| **Goals** | Publish high-impact papers at top conferences (NeurIPS, ICLR, ICRA); save months of engineering time; build a reputation as a leading researcher. |
| **Current Solutions** | Writing custom code from scratch, using unmaintained GitHub forks, or fighting with RL-centric frameworks. |
| **Behavior** | Value speed and friction-less onboarding. They talk to peers in hallways/Slack. They adopt tools that work "this afternoon." |

---

## Secondary Users & Stakeholders

- **The PI (Principal Investigator)**: Approves the use of the toolkit in the lab's methodology. Needs to be convinced of its scientific rigor and transparency.
- **Recruiters at DeepMind/AMI**: The "Ultimate Audience." They look for researchers who have built or influenced standards.
- **Industrial R&D Engineers**: Future users who adopt the tool once the academic standard is set.

---

## User Scenarios

1. **The "Friday Afternoon" Test**: A student hears about PhysLink, clones the repo, and successfully adapts a pre-trained World Model to their specific environment before the weekend.
2. **The "ArXiv Citation" Loop**: A researcher uses PhysLink's evaluation harness to compare their new model against a baseline, providing the metrics needed for a top-tier submission.
