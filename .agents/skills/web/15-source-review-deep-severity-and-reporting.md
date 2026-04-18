## Deep Source Review: Severity and Reporting

### Goal

- Produce consistent, high-signal findings with severity based on validated chain impact.

### Preconditions

- At least one chain is `confirmed-exploitable` or `code-review-only`.

### Primary Probe

- Score severity from **starting trust** to **ending trust**:
  - unauthenticated -> admin/system/cloud control => critical
  - tenant A -> tenant B data/control => high
  - authenticated self-only with no durable impact => low/informational

- Apply amplification factors:
  - chain length with validated links,
  - blast radius (single user vs multi-tenant/systemic),
  - exploit reliability,
  - data sensitivity and business criticality.

### Dead End Pivots

- If final impact is unclear, document two bounded scenarios: minimum credible and likely maximum.
- If exploit needs local/device compromise, re-scope as local-threat model instead of remote compromise.
- If only code-review evidence exists, keep claim bounded and identify missing runtime proof step.

### Data Chaining

- Keep finding narratives in fixed structure:
  - `Entry point`
  - `Trust boundary crossed`
  - `Exploit chain`
  - `Final impact`
  - `Reproduction steps`
  - `Remediation priority`

### Three-Sentence Standard

- Every critical/high finding should be explainable in <= 3 sentences:
  1. What attacker controls.
  2. Which trust assumption fails.
  3. What business-impact endpoint is reached.

### Exit Criteria

- Report is reproducible, impact-bounded, and consistent with the same severity model across findings.

Clear, bounded reporting and consistent severity framing improves triage quality and remediation throughput. [owasp](https://owasp.org/www-project-risk-rating-methodology/) [hackerone](https://docs.hackerone.com/en/articles/8496371-severity)
