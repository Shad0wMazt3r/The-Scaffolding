---
name: web
description: Execute web-application assessment from setup and recon through injection, access control, auth/session issues, API, and SSRF chains.
dependencies: [agent-setup, agent-calibration]
files:
  - 01-prerequisites-and-environment.md
  - 02-injection.md
  - 03-broken-access-control.md
  - 04-authentication-and-session-flaws.md
  - 05-business-logic-flaws.md
  - 06-client-side-attacks.md
  - 07-ssrf-and-internal-exposure.md
  - 08-insecure-deserialization.md
  - 09-api-specific-vulnerabilities.md
  - 10-cross-class-data-chaining-map.md
  - 11-source-review-fast-path.md
optional_deep_files:
  - file: 12-source-review-deep-architecture-and-trust.md
    load_when: User asks for architecture mapping, trust-boundary analysis, or broad source-review strategy.
  - file: 13-source-review-deep-chain-playbooks.md
    load_when: User asks for exploit-chain construction across multiple bug classes.
  - file: 14-source-review-deep-exploitability-and-interactions.md
    load_when: User asks for exploitability triage, sanitizer bypass, race conditions, GraphQL, OAuth, or system interaction patterns.
  - file: 15-source-review-deep-severity-and-reporting.md
    load_when: User asks for impact scoring, severity amplification, or report narrative quality.
---

Load files sequentially on activation: see files list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.
Load `optional_deep_files` only when their `load_when` trigger is present.



