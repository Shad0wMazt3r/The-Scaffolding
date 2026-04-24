## Protocol Attacks

- Preconditions
  - [Condition: TLS, PKCS#1 v1.5, compression, legacy CBC, or signature parsing] → Map protocol version, ciphersuite, transcript ordering, compression, certificate chain, alert behavior
  - [Condition: Network capture exists] → Preserve timing, packet boundaries, retransmits, server error classes

- Parameter fingerprinting
  - [Condition: Distinct error paths for RSA decrypt/format checks] → Flag Bleichenbacher-style oracle
  - [Condition: Compression before encryption with reflected secrets] → Flag CRIME/BREACH leakage
  - [Condition: Legacy CBC over TLS 1.0 semantics] → Flag BEAST/Lucky13-family

- State machine
  - [Condition: Handshake or API transcript available] → **Primary Probe:** transcript normalization and oracle classification
  - [Condition: No explicit oracle signal] → **Pivot 1:** timing clustering; **Pivot 2:** cross-request length correlation; **Pivot 3:** parser differential testing

- Data chaining
  - [Condition: Oracle class confirmed] → Convert each response to labeled state, feed into minimal-query validation harness
  - [Condition: Signature verification discrepancy found] → Chain into message-format confusion, certificate misuse, or token forgery

- Triage one-liners
  - Response clustering: `classes={(r.status, len(r.body), r.latency_bucket) for r in responses}`

- Tool choice
  - [Condition: Traffic analysis and harness control dominate] → Python
  - [Condition: Formal transcript/state reasoning dominates] → Python + symbolic tooling

***
