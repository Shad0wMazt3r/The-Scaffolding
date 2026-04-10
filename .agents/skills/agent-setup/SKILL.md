---
name: agent-setup
description: Provide baseline activation guardrails for tool readiness and dependency checks before any phase starts.
dependencies: []
files:
  - 01-agent-bootstrap.md
---

Load files sequentially on activation: see `files` list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.
