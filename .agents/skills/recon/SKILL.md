---
name: recon
description: Use recursive bug-bounty recon to discover, verify, and pivot domains, hosts, IPs, cloud assets, and JS signals into the next testing phase.
dependencies: [agent-setup]
files:
  - 01-setup-and-contract.md
  - 02-root-domains.md
  - 03-subdomains.md
  - 04-ip-addresses.md
  - 05-cloud-assets.md
  - 06-js-files.md
  - 07-state-transition-and-orchestration.md
---

Load files sequentially on activation: see files list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.


