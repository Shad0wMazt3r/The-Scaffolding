---
name: agent-calibration
description: Improve future activation behavior by capturing missed dependencies, split quality regressions, and workflow friction, then codifying minimal corrections in local instructions.
dependencies: []
files:
  - 01-runbook.md
  - 02-calibration-log.md
---

Load files sequentially on activation: see files list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.
