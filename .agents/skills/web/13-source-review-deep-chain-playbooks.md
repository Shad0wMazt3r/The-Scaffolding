## Deep Source Review: Chain Playbooks

**Primitive → Bridge → Impact Format:**

**Stored XSS → Admin session abuse**
- Primitive: attacker-controlled content renders in privileged UI
- Bridge: browser executes script in admin context
- Impact: admin actions, secret extraction, ATO

**SSRF → internal metadata/service access**
- Primitive: server-side request control
- Bridge: reach internal hosts or cloud metadata
- Impact: credential theft, lateral movement, infra compromise

**Prototype pollution → server-side gadget execution**
- Primitive: global object mutation
- Bridge: polluted object consumed by dangerous templating/merge
- Impact: unauthorized behavior or RCE

**IDOR + write → stored payload / cross-tenant impact**
- Primitive: unauthorized object mutation
- Bridge: victim/admin processes attacker data
- Impact: mass account abuse, tenant breakout, escalation

**Open redirect → OAuth token theft**
- Primitive: controlled redirect target
- Bridge: auth flow misbinds redirect URI/state
- Impact: ATO

**JWT weakness → role escalation**
- Primitive: token forgery or algorithm confusion
- Bridge: policy layer trusts forged claims
- Impact: admin/API takeover

**Path traversal + write → executable placement**
- Primitive: filesystem path control
- Bridge: write to executable/sensitive locations
- Impact: code execution or credential disclosure

**Race condition → business constraint bypass**
- Primitive: concurrent state mutation
- Bridge: no atomic guard on critical transaction
- Impact: financial abuse, quota bypass, integrity loss

**Dead End Pivots:**
- Chain stalls → search alternate bridge points (queue worker, webhook, reporting export, admin moderation)
- Impact seems low → test primitive across tenant/privilege boundaries elsewhere
- Link uncertain → replace with minimal PoC per step

**Exit:** ≥1 end-to-end chain validated with explicit proof at every link.

***
