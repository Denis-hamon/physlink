# Product Brief: PhysLink (TBD)

## Strategic Summary

PhysLink is the missing infrastructure layer between World Model architectures (the brain) and physical environments (the body). By standardizing how these models are adapted to specific domains, we transform neural simulation from a complex, months-long artisanal craft into a reliable, days-long industrial commodity. 

This project is a "Trojan Horse" strategy designed to establish intellectual and technical leadership in the Embodied AI community. By providing a neutral, frictionless, and high-quality "glue layer" that researchers actually *want* to use, we aim to bridge the gap between academic innovation and industrial application, ultimately serving as a strategic career bridge into world-class AI labs like DeepMind or AMI.

---

## Vision

**The "Unified World Model Glue"**
To trigger the explosion of Embodied AI by creating the first standardized adaptation toolkit for World Models. We aim to replicate the "PEFT moment" for physical modeling, reducing domain adaptation time from 6 months of manual engineering to 2 weeks of applied science.

---

## Objectif Personnel & Carrière

**The Recruitment Signal**
This project serves as the primary artifact to demonstrate a unique "Product-Oriented Relief" for advanced AI labs. The goal is to be recognized not just as a researcher, but as the architect who built the standard rails the community uses to innovate.

---

## Positioning

| Component | Value |
|-----------|-------|
| **Target Customer** | PhD students and post-docs in AI/Robotics at mid-sized, ambitious labs (ETH, MIT CSAIL, INRIA, TU Munich). |
| **Need / Opportunity** | Breaking the "6-month engineering cycle" required to build custom infrastructure; solving the reproducibility crisis in World Model research. |
| **Category** | Standardized Adaptation & Infrastructure Toolkit for World Models (The "Glue Layer"). |
| **Key Benefit** | Drastic reduction in engineering overhead (months to days); results that are comparable, shareable, and reproducible across labs. |
| **Alternatives** | PyTorch "from scratch" (opaque), outdated/coupled GitHub forks, or RL-centric frameworks (LlamaIndex, RLlib). |
| **Differentiator** | **Institutional Neutrality**: A community-governed, architecturally agnostic standard that contrasts with the locked-in toolkits of big labs (Meta/Google). |

---

## Founding Product Concept (MVP)

**"Write Once, Adapt Anywhere"**
The core structural idea is the separation of Model, Environment, and Latent Space through a unified API.

- **Foundational Use Case**: Adapting **DreamerV3** to a **custom robotic manipulation task** (e.g., robotic arm) in under **48 hours** on a **single consumer GPU (4090)**.
- **The "Friday Afternoon Test"**: A researcher can clone the repo and have a working simulation with their own environment before the weekend ends.

---

## Business Model & Institutional Strategy

**Phase 1: Reputation-Driven Open Source (B2D/B2A)**
- **Model**: Pure Open Source (MIT/Apache 2.0). No commercial friction.
- **Currency**: Citations, GitHub Issues from top labs, Recruitment inquiries.
- **Target Labs**: 3-5 Technical/Theoretical references (ETH, MIT, FAIR) by solving their publicly stated pipeline bottlenecks.

**Phase 2: Managed IaaS (Optional)**
- **Model**: Cloud/Managed platform for high-scale latent simulation.
- **Value**: Abstracting GPU cluster complexity for institutions once the toolkit is the established standard.

---

## Success Criteria (The Roadmap)

| Milestone | Target | Success Signal |
|-----------|--------|----------------|
| **M3: Survival** | Month 3 | 5 active PhD users in issues; <10 min setup time. |
| **M6: Authority** | Month 6 | **ArXiv Position Paper** published; API stabilized (v0.1). |
| **M12: Standard** | Month 12 | **First Unsolicited External PR** from a known lab member. |
| **M18: Impact** | Month 18 | First recruitment inquiry from target labs (DeepMind/AMI). |

---

## Constraints & Design Parameters

### Technical (Inflexible)
- **Language**: Pure Python 3.10+.
- **Backend**: PyTorch-first, JAX-ready abstractions.
- **Hardware**: Must run on 1x A100/3090/4090.
- **API Stability**: Documented deprecation cycle from v0.1.

### Perception
- **Scientific Status**: Position paper must accompany the code launch.
- **Code Hygiene**: "Surgical cleanliness" (no TODOs, no redundant files).
- **Communication**: English-only for all public-facing assets.

---

## Tone of Voice

**The "System Architect / Peer Researcher"**
- **Technical & Precise**: Uses domain-correct terminology without over-simplification.
- **Sobre & Minimalist**: Free of marketing hype; focuses on data and reproducibility.
- **Transparent & Empathetic**: Error messages provide diagnostic hints (Empathy for Friction).
- **Agnostic**: Balanced treatment of all model architectures.

---

## Naming Strategy (TBD)

Current placeholders: **PhysLink**, **LatentOps**.
- **Criteria**: SEO-friendly, available on PyPI/GitHub, evokes physics/infrastructure, no confusion with LangChain/Blockchain.
- **Next Action**: Finalize name once the first model adapter (DreamerV3) is functional.

---

**Status:** Product Brief Complete (Phase 1)
**Next Phase:** Trigger Mapping (Phase 2)
**Last Updated:** 2026-05-20
