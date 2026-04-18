## Deep Source Review: Chain Playbooks

### Goal

- Convert isolated findings into realistic, high-impact exploit chains.

### Preconditions

- You completed architecture/trust mapping or equivalent fast-path triage.

### Primary Probe

- Build chains using the primitive -> bridge -> impact format:
  - **Primitive:** what capability do you gain now?
  - **Bridge:** what trusted boundary does it cross next?
  - **Impact:** what final business/security outcome follows?

### Chain Templates

- **Stored XSS -> Admin session abuse**
  - Primitive: attacker-controlled content renders in privileged UI.
  - Bridge: browser executes script in admin context.
  - Impact: admin actions, secret extraction, account takeover.

- **SSRF -> internal metadata/service access**
  - Primitive: server-side request control.
  - Bridge: reach internal hosts or cloud metadata.
  - Impact: credential theft, lateral movement, infra compromise.

- **Prototype pollution -> server-side gadget execution**
  - Primitive: global object mutation.
  - Bridge: polluted object consumed by dangerous templating/merge path.
  - Impact: unauthorized behavior or RCE.

- **IDOR + write path -> stored payload / cross-tenant impact**
  - Primitive: unauthorized object mutation.
  - Bridge: victim/admin later processes attacker data.
  - Impact: mass account abuse, tenant breakout, privilege escalation.

- **Open redirect -> OAuth token theft**
  - Primitive: controlled redirect target.
  - Bridge: authorization flow misbinds redirect URI/state.
  - Impact: account takeover.

- **JWT verification weakness -> role escalation**
  - Primitive: token forgery or algorithm confusion.
  - Bridge: policy layer trusts forged claims.
  - Impact: admin/API takeover.

- **Path traversal + write -> executable artifact placement**
  - Primitive: file system path control.
  - Bridge: write to executable/readable sensitive locations.
  - Impact: code execution or credential disclosure.

- **Race condition -> business constraint bypass**
  - Primitive: concurrent state mutation.
  - Bridge: no atomic guard on critical transaction.
  - Impact: financial abuse, quota bypass, integrity loss.

### Dead End Pivots

- If a chain stalls, search for alternate bridge points (queue worker, webhook, reporting export, admin moderation path).
- If impact seems low, test whether the same primitive crosses tenant or privilege boundaries elsewhere.
- If a link is uncertain, replace assumptions with a minimal PoC per step.

### Data Chaining

- Persist each chain as:
  - `start_state`
  - `primitive`
  - `bridge`
  - `impact`
  - `proof_artifacts`
  - `confidence`

### Exit Criteria

- At least one chain is end-to-end validated with explicit proof at every link.

Chaining methodology is consistently associated with higher-impact outcomes in production bug bounty programs. [intigriti](https://www.intigriti.com/blog/business-insights/chaining-in-action-techniques-terminology-and-real-world-impact-on-business) [hackerone](https://www.hackerone.com/blog/how-think-hacker-inspiration-security-researchers)
