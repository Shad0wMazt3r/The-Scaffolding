---
name: web
description: Execute web-application assessment from setup and recon through injection, access control, auth/session issues, API, and SSRF chains.
dependencies: [agent-setup]
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
---

Load files sequentially on activation: see files list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.


