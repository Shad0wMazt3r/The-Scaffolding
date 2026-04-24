## Elliptic Curve Attacks

- Preconditions
  - [Condition: Curve name, points, signatures, or custom EC arithmetic exposed] → Verify field prime, curve equation, group order, cofactor, point validation, on-receipt checks
  - [Condition: Repeated/biased nonces in ECDSA/DSA] → Collect all signatures, message hashes, nonce side-channel observations

- Parameter fingerprinting
  - [Condition: Named curve with small subgroup-order factors] → Flag Pohlig-Hellman feasibility
  - [Condition: Abnormal embedding degree or pairing-friendly behavior] → Flag MOV-style reduction
  - [Condition: Server accepts attacker-supplied points] → Flag invalid-curve and small-subgroup validation failures

- State machine
  - [Condition: Signature corpus available] → **Primary Probe:** nonce-correlation and duplicate-r analysis
  - [Condition: No duplicate nonce signal] → **Pivot 1:** partial-bias/HNP; **Pivot 2:** subgroup/order validation; **Pivot 3:** invalid-point acceptance
  - [Condition: Standard DLP stalls] → Pivot to group-structure decomposition before generic discrete-log

- Data chaining
  - [Condition: Partial nonce leakage supported] → Feed into lattice model, validate candidates against public point, use verified key for artifact access
  - [Condition: Invalid-curve acceptance confirmed] → Enumerate subgroup orders, log residue leaks, chain into CRT-style scalar reconstruction

- Triage one-liners
  - Duplicate-r detection: `dups=[r for r in rs if rs.count(r)>1]`
  - On-curve validation: `assert (y*y - (x*x*x + a*x + b)) % p == 0`

- Tool choice
  - [Condition: Finite-field arithmetic and point validation dominate] → Python
  - [Condition: Lattices, subgroup decomposition, or pairings dominate] → SageMath

***
