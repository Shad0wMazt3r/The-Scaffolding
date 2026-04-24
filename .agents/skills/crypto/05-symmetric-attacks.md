## Symmetric Attacks

- Preconditions
  - [Condition: Block size, IV/nonce behavior, mode unknown] → Fingerprint by ciphertext length, repeated blocks, known headers, API behavior under modified inputs
  - [Condition: Oracle interaction exists] → Classify as decrypt, padding-validity, tag-validity, timing, or format oracle

- Parameter fingerprinting
  - [Condition: Repeated 16-byte blocks] → Flag ECB
  - [Condition: Stable IV or nonce reuse with same key] → Flag CBC/GCM/CTR misuse
  - [Condition: Malleability without integrity] → Flag bit-flip or block-splice path

- State machine
  - [Condition: Static ciphertext set available] → **Primary Probe:** block/nonce/length analysis
  - [Condition: Static analysis inconclusive] → **Pivot 1:** differential chosen-input; **Pivot 2:** error-channel classification; **Pivot 3:** metadata correlation
  - [Condition: Oracle rate-limited] → Optimize for minimal distinguishing queries; cache response classes

- Data chaining
  - [Condition: Reused nonce or keystream segment identified] → Align records, isolate overlap window, pass validated keystream relations
  - [Condition: Padding-validity signal exists] → Map response classes, confirm blockwise dependency, treat each byte as evidence until rechecked

- Triage one-liners
  - ECB repeated blocks: `from collections import Counter; reps=[b for b,c in Counter(ct[i:i+16] for i in range(0,len(ct),16)).items() if c>1]`
  - Nonce-reuse detection: `reuse = len(nonces) != len(set(nonces))`

- Tool choice
  - [Condition: Parsing, comparing blocks, driving APIs dominate] → Python
  - [Condition: Differential trail search or algebraic fault modeling] → SageMath model + Python harness

***
