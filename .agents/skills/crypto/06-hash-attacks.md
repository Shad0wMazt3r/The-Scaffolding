## Hash Attacks

- Preconditions
  - [Condition: Raw hash used as MAC or commitment without domain separation] → Classify construction before testing collisions/extension
  - [Condition: Merkle-Damgård hash used as hash(secret || msg)] → Flag length-extension exposure

- Parameter fingerprinting
  - [Condition: MD5/SHA1 present] → Separate collision-relevant from preimage-relevant risk
  - [Condition: Unbounded attacker-controlled keys into hash tables/parsers] → Flag hash-flooding/DoS

- State machine
  - [Condition: Construction visible] → **Primary Probe:** composition review
  - [Condition: Construction hidden behind API] → **Pivot 1:** behavioral tests on appended data; **Pivot 2:** duplicate-prefix acceptance; **Pivot 3:** parser-side collision amplification
  - [Condition: Length-extension feasible] → Derive exact message framing, verify, pass into token/session revalidation

- Data chaining
  - [Condition: Length-extension feasible] → Verify framing requirements, use in token/session revalidation sandbox
  - [Condition: Collision acceptance exists] → Chain into identity confusion, file-substitution, or certificate-parsing

- Triage one-liners
  - Algorithm family fingerprint: `algos={16:'MD5',20:'SHA1',32:'SHA256',64:'SHA512'}.get(len(d), 'unknown')`

- Tool choice
  - [Condition: Construction review dominates] → Python
  - [Condition: Differential-path or chosen-prefix mathematics] → Specialized tooling; feasibility is challenge-specific

***
