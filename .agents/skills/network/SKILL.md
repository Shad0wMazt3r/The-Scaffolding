---
name: network
description: Assess network assets with non-destructive service mapping, auth posture checks, directory exposure reviews, remote access, and evidence-linked pivoting.
dependencies: []
files:
  - 01-environment.md
  - 02-services-and-authentication.md
  - 03-mitm-smb-and-directory.md
  - 04-exposure-and-remote-access.md
  - 05-pivoting-automation-and-evidence.md
---

Load files sequentially on activation: see iles list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.
