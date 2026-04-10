## LCG & PRNG Attacks
- Preconditions
  - * -> [Condition: Session IDs, nonces, OTPs, challenge numbers, or game outputs look patterned] -> Action: collect ordered outputs with timestamps and any truncation rules.
  - * -> [Condition: Output count is small] -> Action: prioritize modulus/recurrence inference before seed guessing.
- Parameter fingerprinting
  - * -> [Condition: Linear relation under modular arithmetic appears] -> Action: flag LCG.
  - * -> [Condition: Bit-level filtration or combiner structure appears] -> Action: flag filter-generator or shrinking/clock-control family.
- State machine
  - * -> [Condition: Consecutive outputs available] -> Action: start with recurrence testing as the **Primary Probe**.
  - * -> [Condition: Probe weak because outputs are truncated or mixed] -> Action: **Dead End Pivot 1** to timestamp/seed-space pruning; **Dead End Pivot 2** to SAT/SMT modeling; **Dead End Pivot 3** to algebraic relation hunting across multiple traces.
- Data chaining
  - * -> [Condition: Internal state candidates survive consistency checks] -> Action: use them only to predict the next few lab outputs and confirm the model before trusting any broader conclusion.
  - * -> [Condition: Partial state leaks across sessions] -> Action: merge traces by clock window or process restart markers.
- Simple triage one-liners
  - * -> [Condition: Need first-difference view] -> Action: `diffs=[(outs[i+1]-outs[i]) for i in range(len(outs)-1)]`
- Complexity and tool choice
  - * -> [Condition: Small-state arithmetic dominates] -> Action: Python.
  - * -> [Condition: bit-vector constraints or filtered generators dominate] -> Action: Z3 or SageMath, depending on whether the model is Boolean-heavy or number-theoretic.

