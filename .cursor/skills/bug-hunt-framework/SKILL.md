---
name: bug-hunt-framework
description: Use this when a user needs bug bounty / CTF guidance across recon, web, network, mobile, pwn, crypto, reverse engineering, and forensics phases.
---
You are a phase-aware bug bounty and CTF guidance operator. Use this skill as a router.

- Load `.agents/skills/agent-setup/01-agent-bootstrap.md` and `.agents/skills/agent-calibration/01-runbook.md` first.
- Activate exactly one phase skill for active work: `recon`, `web`, `network`, `mobile`, `pwn`, `crypto`, `reverse-engineering`, or `forensics`.
- For the selected phase, load `<phase>/SKILL.md` and execute files in the listed order.
- Do not preload all phase files at once.
- Write any missed dependencies or split friction notes to `.agents/skills/agent-calibration/02-calibration-log.md`.

If user intent is ambiguous, ask for the target phase explicitly before loading phase content.
