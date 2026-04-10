## Protocol Attacks
- Preconditions
  - * -> [Condition: TLS, PKCS#1 v1.5, compressed secrets, legacy CBC, or signature parsing appear] -> Action: map protocol version, ciphersuite, transcript ordering, compression, certificate chain, and alert behavior.
  - * -> [Condition: Network capture exists] -> Action: preserve timing, packet boundaries, retransmits, and server error classes.
- Parameter fingerprinting
  - * -> [Condition: Distinct error paths for RSA decrypt/format checks] -> Action: flag Bleichenbacher-style oracle review.
  - * -> [Condition: Compression before encryption with reflected secrets] -> Action: flag CRIME/BREACH-style leakage class.
  - * -> [Condition: Legacy CBC over TLS 1.0 semantics] -> Action: flag BEAST/Lucky13-family review.
- State machine
  - * -> [Condition: Handshake or API transcript available] -> Action: begin with transcript normalization and oracle classification as the **Primary Probe**.
  - * -> [Condition: No explicit oracle signal] -> Action: **Dead End Pivot 1** to timing clustering; **Dead End Pivot 2** to cross-request length correlation; **Dead End Pivot 3** to parser differential testing.
- Data chaining
  - * -> [Condition: Oracle class confirmed] -> Action: convert each server response into a labeled state, then feed that state map into a minimal-query validation harness.
  - * -> [Condition: Signature verification discrepancy found] -> Action: chain the discrepancy into message-format confusion, certificate misuse, or token forgery review.
- Simple triage one-liners
  - * -> [Condition: Need response clustering stub] -> Action: `classes={(r.status, len(r.body), r.latency_bucket) for r in responses}`
- Complexity and tool choice
  - * -> [Condition: Traffic analysis and harness control dominate] -> Action: Python.
  - * -> [Condition: Formal transcript/state reasoning dominates] -> Action: pair Python with symbolic tooling.

