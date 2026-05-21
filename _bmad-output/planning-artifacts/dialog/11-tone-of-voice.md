# Tone of Voice & Personality: PhysLink (TBD)

**Step:** Step 11 - Define Tone of Voice
**Completed:** 2026-05-20

---

## Brand Personality: The "System Architect / Peer Researcher"

PhysLink communicates like a senior peer in a high-end research lab. It is intellectually rigorous, technically precise, but deeply empathetic to the operational friction of research. It doesn't hype; it empowers.

---

## Tone Attributes

| Attribute | Description | Why? |
|-----------|-------------|------|
| **Technical & Precise** | Uses domain-correct terminology (Latent Spaces, Rollouts, PEFT) without over-simplification. | Establishes immediate authority with PhD-level users. |
| **Sobre & Minimalist** | Clean, functional, and free of marketing "fluff." Focuses on code and data. | Signals scientific seriousness and respect for the user's time. |
| **Transparent & Empathetic** | Error messages provide context and diagnostic hints. "Failed" states are actionable. | Realizes the project's moat: "Empathy for Friction." |
| **Agnostic & Neutral** | Balanced treatment of all architectures (JEPA, Dreamer, etc.). | Protects the "Institutional Neutrality" required for a community standard. |

---

## Microcopy Examples

| Interaction | Traditional/Failing Tone | PhysLink Tone |
|-------------|--------------------------|---------------|
| **Action Button** | "Start Training" | "Initialize Adaptation Loop" |
| **Error Message** | "ValueError: size mismatch" | "PhysLink detected a shape mismatch: expected [32, 64] but got [32, 128]. Check your Encoder output." |
| **Empty State** | "No data found." | "No trajectories detected in buffer. Ensure the environment rollout completed successfully." |
| **System Status** | "Loading..." | "Validating latent space consistency..." |

---

## Do's and Don'ts

- **DO**: Provide exact dimensions and types in errors.
- **DO**: Refer to established papers when naming abstractions.
- **DON'T**: Use exclamation marks or hype-driven adjectives (e.g., "Revolutionary!", "Amazing!").
- **DON'T**: Hide complexity behind opaque "magic" functions.
