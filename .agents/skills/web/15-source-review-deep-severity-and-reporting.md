## Deep Source Review: Severity and Reporting

**Severity Scoring (Starting → Ending Trust):**
- unauthenticated → admin/system/cloud control = **critical**
- tenant A → tenant B data/control = **high**
- authenticated self-only with no durable impact = **low/informational**

**Amplification Factors:**
- chain length with validated links
- blast radius (single user vs multi-tenant/systemic)
- exploit reliability
- data sensitivity and business criticality

**Dead End Pivots:**
- Impact unclear → document two scenarios: minimum credible and likely maximum
- Exploit needs local/device compromise → re-scope as local threat model
- Code-review only → keep claim bounded, identify missing runtime proof step

**Finding Narrative Structure:**
- Entry point
- Trust boundary crossed
- Exploit chain
- Final impact
- Reproduction steps
- Remediation priority

**Three-Sentence Standard:**
Every critical/high finding in ≤3 sentences:
1. What attacker controls
2. Which trust assumption fails
3. What business-impact endpoint is reached

**Exit:** Report reproducible, impact-bounded, severity consistent across findings.

***
