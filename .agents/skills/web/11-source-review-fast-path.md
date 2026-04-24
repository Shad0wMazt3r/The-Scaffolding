## Source Code Review Fast Path

**Goal:** High-confidence vulnerability map quickly; load deep modules only as needed.

**Primary Probe:**
1. Map trust boundaries: unauth → auth, user → admin, tenant A → tenant B, internet → internal
2. Trace user-controlled input to sinks (query builders, template renderers, file/network/process calls)
3. Verify control points: authz checks, tenant filters, signature/token validation, rate/transaction guards
4. Chain low-impact findings via cross-class chaining map

**Dead End Pivots:**
- No direct sink obvious → framework glue (middleware, interceptors, decorators, serializers)
- Authz logic centralized → exception paths and helpers bypassing shared guards
- Large codebase → prioritize crown jewels: account recovery, role assignment, payment, storage, admin APIs

**Data Chaining:**
- Read primitive → secrets/config → impersonation/escalation
- Write primitive → stored payload → privileged execution context
- Request primitive → internal reachability → metadata/services → credential pivot

**Exit Criteria:**
- Explain one validated exploit from attacker input → business impact in ≤3 sentences
- If blocked, load matching deep module

**Deep-Load Routing:**
- Load `12-...architecture-and-trust.md` for system mapping
- Load `13-...chain-playbooks.md` for exploit chain templates
- Load `14-...exploitability-and-interactions.md` for verification and inter-system patterns
- Load `15-...severity-and-reporting.md` for impact scoring

***
