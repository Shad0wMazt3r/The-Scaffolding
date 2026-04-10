---
name: crypto
description: Triage cryptographic artifacts from encoding and classical ciphers through RSA, EC, symmetric, hash, protocol, RNG, custom, and zero-knowledge attacks.
dependencies: [agent-setup]
files:
  - 01-workspace-baseline.md
  - 02-classical-and-encoding.md
  - 03-rsa-attacks.md
  - 04-elliptic-curve-attacks.md
  - 05-symmetric-attacks.md
  - 06-hash-attacks.md
  - 07-protocol-attacks.md
  - 08-lcg-and-prng-attacks.md
  - 09-custom-and-unknown-cipher-analysis.md
  - 10-zero-knowledge-and-commitment.md
---

Load files sequentially on activation: see files list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.


