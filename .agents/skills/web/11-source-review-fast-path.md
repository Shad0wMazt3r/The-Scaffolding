## Source Code Review Fast Path

### Goal

- Produce a high-confidence vulnerability map quickly without loading long-form material unless needed.

### Preconditions

- You already loaded `01` through `10` in this skill.
- You have a target repo, service, or API surface.

### Primary Probe

- Build a minimal review loop in this order:
  1. **Map trust boundaries**: unauth -> auth, user -> admin, tenant A -> tenant B, internet -> internal.
  2. **Trace user-controlled input** to sinks (query builders, template renderers, file/network/process calls).
  3. **Verify control points**: authz checks, tenant filters, signature/token validation, rate/transaction guards.
  4. **Chain low-impact findings** using `10-cross-class-data-chaining-map.md`.

### Dead End Pivots

- If no direct sink is obvious, pivot to framework glue code (middleware, interceptors, decorators, serializers).
- If authz logic looks centralized, pivot to exception paths and helper functions that bypass shared guards.
- If codebase is too large, prioritize crown-jewel paths first: account recovery, role assignment, payment, storage, admin APIs.

### Data Chaining

- Convert each primitive into a chain candidate:
  - **Read primitive** -> secrets/config -> impersonation/escalation
  - **Write primitive** -> stored payload -> privileged execution context
  - **Request primitive** -> internal reachability -> metadata/services -> credential pivot

### Exit Criteria

- You can explain at least one validated exploit path from attacker input to business impact in <= 3 sentences.
- If not, load one deep module from `optional_deep_files` that matches the blocker.

### Deep-Load Routing

- Load `12-source-review-deep-architecture-and-trust.md` for system mapping and trust-signal analysis.
- Load `13-source-review-deep-chain-playbooks.md` for cross-class chain construction templates.
- Load `14-source-review-deep-exploitability-and-interactions.md` for exploitability verification and inter-system patterns.
- Load `15-source-review-deep-severity-and-reporting.md` for impact scoring and report narrative quality.

This fast path aligns with established threat-model-first AppSec workflows and keeps review loops short before escalating to deep analysis. [owasp](https://owasp.org/www-community/Threat_Modeling)
