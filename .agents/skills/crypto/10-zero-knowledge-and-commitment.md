## Zero-Knowledge & Commitment Scheme Weaknesses
- Preconditions
  - * -> [Condition: Sigma protocol, Fiat-Shamir transform, Pedersen-style commitment, or SNARK/STARK verification code appears] -> Action: record statement language, transcript structure, challenge derivation, randomness source, and subgroup checks.
  - * -> [Condition: Custom transcript hashing or manual challenge assembly exists] -> Action: flag domain-separation and replay risk.
- Parameter fingerprinting
  - * -> [Condition: Commitment base points not independently generated or subgroup checks missing] -> Action: flag binding/hiding ambiguity.
  - * -> [Condition: Fiat-Shamir challenge omits public inputs or context] -> Action: flag transcript malleability and replay.
- State machine
  - * -> [Condition: Verifier code available] -> Action: begin with relation completeness and transcript-binding review as the **Primary Probe**.
  - * -> [Condition: Primary review is clean] -> Action: **Dead End Pivot 1** to randomness reuse checks; **Dead End Pivot 2** to subgroup/cofactor validation; **Dead End Pivot 3** to challenge-domain collision review.
- Data chaining
  - * -> [Condition: Commitment randomness is reused] -> Action: correlate transcripts, test whether witness relations become linearly exposed, and pass only validated algebraic relations into the next model.
  - * -> [Condition: Transcript binding is incomplete] -> Action: map omitted fields and verify whether altered transcripts still satisfy the verifier.
- Simple triage one-liners
  - * -> [Condition: Need transcript-field completeness check] -> Action: `missing=[f for f in required_fields if f not in transcript_hash_inputs]`
- Complexity and tool choice
  - * -> [Condition: Parsing transcripts and verifier logic dominate] -> Action: Python.
  - * -> [Condition: group algebra, polynomial identities, or soundness edge cases dominate] -> Action: SageMath.

If you want this transformed into a challenge-ready worksheet, the next most useful format is a per-artifact template with fixed fields for `fingerprint`, `oracle class`, `evidence`, `pivot chosen`, and `next-state`.
