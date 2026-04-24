## Zero-Knowledge & Commitment Scheme Weaknesses

- Preconditions
  - [Condition: Sigma protocol, Fiat-Shamir transform, Pedersen commitment, or SNARK/STARK verification appears] → Record statement language, transcript structure, challenge derivation, randomness source, subgroup checks
  - [Condition: Custom transcript hashing or manual challenge assembly] → Flag domain-separation and replay risk

- Parameter fingerprinting
  - [Condition: Commitment base points not independently generated or subgroup checks missing] → Flag binding/hiding ambiguity
  - [Condition: Fiat-Shamir challenge omits public inputs or context] → Flag transcript malleability and replay

- State machine
  - [Condition: Verifier code available] → **Primary Probe:** relation completeness and transcript-binding review
  - [Condition: Primary review clean] → **Pivot 1:** randomness reuse checks; **Pivot 2:** subgroup/cofactor validation; **Pivot 3:** challenge-domain collision

- Data chaining
  - [Condition: Commitment randomness reused] → Correlate transcripts, test if witness relations become linearly exposed, pass validated algebraic relations
  - [Condition: Transcript binding incomplete] → Map omitted fields, verify if altered transcripts still satisfy verifier

- Triage one-liners
  - Transcript-field completeness: `missing=[f for f in required_fields if f not in transcript_hash_inputs]`

- Tool choice
  - [Condition: Parsing transcripts and verifier logic dominate] → Python
  - [Condition: Group algebra, polynomial identities, soundness edge cases dominate] → SageMath

***
