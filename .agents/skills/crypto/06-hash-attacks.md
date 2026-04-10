## Hash Attacks
- Preconditions
  - * -> [Condition: Raw hash is used as MAC or commitment without domain separation] -> Action: classify construction before testing collisions or extension properties.
  - * -> [Condition: Merkle-Damgård hash used as `hash(secret || msg)`] -> Action: flag length-extension exposure.
- Parameter fingerprinting
  - * -> [Condition: MD5/SHA1 present] -> Action: separate “collision-relevant” from “preimage-relevant” risk.
  - * -> [Condition: Unbounded attacker-controlled keys into hash tables or parsers] -> Action: flag hash-flooding/DoS path.
- State machine
  - * -> [Condition: Construction is visible] -> Action: start with composition review as the **Primary Probe**.
  - * -> [Condition: Construction hidden behind API] -> Action: **Dead End Pivot 1** to behavioral tests on appended data; **Dead End Pivot 2** to duplicate-prefix acceptance; **Dead End Pivot 3** to parser-side collision amplification review.
- Data chaining
  - * -> [Condition: Length-extension feasible] -> Action: derive the exact message framing requirements, then pass the verified framing into token/session revalidation in a sandbox.
  - * -> [Condition: Collision acceptance exists] -> Action: chain it into identity confusion, file-substitution, or certificate-parsing review depending on the challenge surface.
- Simple triage one-liners
  - * -> [Condition: Need algorithm family fingerprint from digest length] -> Action: `algos={16:'MD5',20:'SHA1',32:'SHA256',64:'SHA512'}.get(len(d), 'unknown')`
- Complexity and tool choice
  - * -> [Condition: Construction review dominates] -> Action: Python.
  - * -> [Condition: Differential-path or chosen-prefix mathematics dominate] -> Action: use specialized tooling and treat feasibility as challenge-specific, not generic.

