## Deep Source Review: Architecture and Trust

### Goal

- Build a complete attack-oriented system map before deep bug hunting.

### Preconditions

- Fast path is complete.
- You have repository access and can identify entrypoints.

### Primary Probe

- Use this architecture-first checklist:
  - Inventory components: web/API, auth, worker, cache, DB, object storage, queue, third-party APIs.
  - Draw data flows: user/client -> edge -> app -> internal services -> storage.
  - Mark trust boundaries and escalation steps explicitly.
  - Enumerate trust signals: cookies/JWT, headers, API keys, network position, mTLS assumptions.
  - Identify crown jewels: admin capability, tenant data, payment state, signing keys, cloud credentials.

### Dead End Pivots

- If boundaries are unclear, infer from middleware stacks, gateway routes, and infra config files.
- If trust signals are implicit, inspect helper libraries where request context is converted to privileged identity.
- If crown jewels are not obvious, prioritize irreversible actions and high-value data domains first.

### Data Chaining

- Create a boundary crossing map:
  - **Input boundary** (user-controlled)
  - **Validation boundary** (parsers/sanitizers)
  - **Policy boundary** (authz/tenant/business rules)
  - **Execution boundary** (DB/query/template/process/network/file sinks)
- For each crossing, note what assumptions are trusted and how they might be spoofed.

### Structured Review Prompts

- "Where can attacker input become authority?"
- "Which trust signal grants this privilege and can it be forged?"
- "What code path skips the canonical policy check?"
- "What low-severity primitive combines with this path for critical impact?"

### Exit Criteria

- You have:
  - a component and trust-boundary map,
  - a list of trusted signals with spoofability notes,
  - a prioritized set of crown-jewel paths to verify.

System-level decomposition and trust-boundary analysis are core practices in modern threat modeling and security architecture review. [owasp](https://owasp.org/www-project-threat-dragon/) [nist](https://csrc.nist.gov/publications/detail/sp/800-154/final)
