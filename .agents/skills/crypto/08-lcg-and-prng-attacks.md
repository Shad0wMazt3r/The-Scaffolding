## LCG & PRNG Attacks

- Preconditions
  - [Condition: Session IDs, nonces, OTPs, challenges, or outputs look patterned] → Collect ordered outputs with timestamps and any truncation rules
  - [Condition: Small output count] → Prioritize modulus/recurrence inference before seed guessing

- Parameter fingerprinting
  - [Condition: Linear relation under modular arithmetic appears] → Flag LCG
  - [Condition: Bit-level filtration or combiner structure appears] → Flag filter-generator or shrinking/clock-control

- State machine
  - [Condition: Consecutive outputs available] → **Primary Probe:** recurrence testing
  - [Condition: Outputs truncated or mixed] → **Pivot 1:** timestamp/seed-space pruning; **Pivot 2:** SAT/SMT modeling; **Pivot 3:** algebraic relations across traces
  - [Condition: Internal state candidates survive checks] → Use to predict next few lab outputs and confirm model

- Data chaining
  - [Condition: Partial state leaks across sessions] → Merge traces by clock window or process restart markers
  - [Condition: Recurrence confirmed] → Use for session/nonce prediction in sandbox

- Triage one-liners
  - First-difference view: `diffs=[(outs[i+1]-outs[i]) for i in range(len(outs)-1)]`

- Tool choice
  - [Condition: Small-state arithmetic dominates] → Python
  - [Condition: Bit-vector constraints or filtered generators dominate] → Z3 or SageMath

***
