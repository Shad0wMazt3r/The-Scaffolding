## Deep Source Review: Architecture and Trust

**Architecture-First Checklist:**
- Inventory components: web/API, auth, worker, cache, DB, object storage, queue, third-party APIs
- Draw data flows: user/client → edge → app → internal services → storage
- Mark trust boundaries and escalation steps explicitly
- Enumerate trust signals: cookies/JWT, headers, API keys, network position, mTLS assumptions
- Identify crown jewels: admin capability, tenant data, payment state, signing keys, cloud credentials

**Dead End Pivots:**
- Boundaries unclear → middleware stacks, gateway routes, infra config files
- Trust signals implicit → inspect helper libraries where request context → privileged identity
- Crown jewels non-obvious → prioritize irreversible actions and high-value data domains

**Boundary Crossing Map:**
- Input boundary (user-controlled)
- Validation boundary (parsers/sanitizers)
- Policy boundary (authz/tenant/business rules)
- Execution boundary (DB/query/template/process/network/file sinks)

For each crossing, note trusted assumptions and spoofability.

**Review Prompts:**
- Where can attacker input become authority?
- Which trust signal grants this privilege and can it be forged?
- What code path skips the canonical policy check?
- What low-severity primitive combines with this path for critical impact?

**Exit:** Component/trust map, trust-signal list with spoofability notes, prioritized crown-jewel paths.

***
