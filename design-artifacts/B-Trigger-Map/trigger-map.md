# Trigger Map: PhysLink (TBD)

## Strategic Narrative
The success of PhysLink depends on a causal chain of adoption starting with **Hugo** (the PhD student) passing his "Friday Afternoon Test," followed by **Petra** (the Post-doc) standardizing her lab's comparability, and finally **Samuel** (the Domain Scientist) trusting the tool for real-world physics. Our design focus is to prove immediate speed without sacrificing long-term scientific rigour or institutional trust.

---

## Business Goals (SMART)

1.  **Co-ownership**: At least 1 unsolicited technical Pull Request from an external lab before M12.
2.  **Authority**: Publication of a position paper on arXiv concurrently with the public launch.
3.  **Material Accessibility**: 100% of demonstration notebooks must run on the free Colab T4 tier.
4.  **Temporal Accessibility**: Foundational use cases must yield results in < 90 min on Colab T4 (v0.1 onwards).
5.  **Generality**: Active usage in at least 3 distinct physical domains (e.g., Robotics + 2 others) by M18.

---

## Target Groups & Personas

| Persona | Role | Primary Driver (WANT) | Primary Barrier (FEAR) |
| :--- | :--- | :--- | :--- |
| **Hugo** | PhD Student | **Social Legitimacy**: Using a recognized peer standard. | **Loss of Control**: Fear of opaque "black box" abstractions. |
| **Petra** | Post-doc | **Legacy Building**: Standardizing lab reproducibility. | **Political Risk**: Fear of recommending a short-lived tool. |
| **Samuel** | Domain Scientist | **Hypothesis Acceleration**: Days to minutes cycles. | **Physical Inconsistency**: Fear of scientifically invalid results. |
| **Paula** | PI | **Institutional Excellence**: Rigorous, validable research. | **Reproducibility Scandal**: Risk to lab reputation. |

---

## Feature Impact Assessment (Ranked)

| Rank | Feature | Hugo (Prim.) | Petra (Sec.) | Samuel (Tert.) | **Score** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Universal Space API** | HIGH (5) | LOW (0) | HIGH (3) | **8** |
| **2** | **Trust Signals Bundle** | MED (3) | HIGH (3) | MED (1) | **7** |
| **2** | **Colab-First Demo Notebook** | HIGH (5) | MED (1) | MED (1) | **7** |
| **2** | **Domain Validation Hooks** | LOW (1) | MED (1) | HIGH (5) | **7** |
| **5** | **Standardized Trajectory Buffers** | LOW (1) | HIGH (3) | LOW (0) | **4** |
| **5** | **Time-to-Science Callout** | HIGH (5) | LOW (0) | MED (1) | **6** |
| **7** | **Architecture Adapter (DreamerV3)** | HIGH (5) | LOW (0) | LOW (0) | **5** |
| **7** | **Pipeline Debug Hooks** | HIGH (5) | LOW (0) | LOW (0) | **5** |
| **9** | **Layer 0 Trajectory Visualizer** | MED (3) | LOW (0) | MED (1) | **4** |
| **10** | **Job Serializer (YAML/JSON)** | LOW (1) | MED (1) | LOW (0) | **2** |

---

## Strategic Conclusions

1.  **The "Universal Space API" is the Priority #1**: It is the gateway for all domains. Design effort must focus here first to ensure the abstractions handle high-dimensional physical data (Samuel) as well as robotic actions (Hugo).
2.  **Bimodal MVP**: We are not just building for Hugo. The MVP must include **Domain Validation Hooks** for Samuel to ensure the tool is scientifically credible from day one.
3.  **Reputation as a Feature**: The **Trust Signals Bundle** is as critical as the code. It disarms Petra's political fear and Hugo's peer-pressure concerns.

---

**Next Phase:** UX Scenarios (Phase 3)
**Last Updated:** 2026-05-20
