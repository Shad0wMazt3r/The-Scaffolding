# CTF Benchmarking Harness (5 Hard Challenges)

This package defines a reproducible CTF benchmark for agentic security workflows:

- exactly **5 hard challenges**
- one per category: `web`, `pwn`, `crypto`, `forensics`, `reverse-engineering`
- Docker-based lifecycle orchestration
- mandatory final writeup for manual grading

## Challenge set

1. `web-grandprixheaven` (Google CTF 2024 Quals)
2. `pwn-knife` (Google CTF 2024 Quals)
3. `crypto-mytls` (Google CTF 2023 Quals)
4. `rev-ilovecrackmes` (Google CTF 2024 Quals)
5. `forensics-blue-team-memory` (RootMeUp)

## Source policy

- `google/google-ctf` sources are Apache-2.0 and can be auto-fetched.
- `RootMeUp` is configured as **reference-only** in this repository policy:
  user-side download/clone is required before use.

## Setup

```powershell
python tools\benchmarks\fetch_ctf_sources.py `
  --manifest ctf-benchmarking\manifest.json `
  --source-root ctf-benchmarking\sources
```

To include reference-only sources in the fetch helper:

```powershell
python tools\benchmarks\fetch_ctf_sources.py `
  --manifest ctf-benchmarking\manifest.json `
  --source-root ctf-benchmarking\sources `
  --include-reference-only
```

## Run benchmark

```powershell
python tools\benchmarks\run_cursor_ctf_benchmark.py `
  --manifest ctf-benchmarking\manifest.json `
  --source-root ctf-benchmarking\sources `
  --model gpt-5.3-codex `
  --output-dir reports\benchmarks\ctf-run-01
```

## Grade writeups (manual-first scaffold)

```powershell
python tools\benchmarks\grade_cursor_ctf_writeups.py `
  --run-report reports\benchmarks\ctf-run-01\run-report.json `
  --rubric ctf-benchmarking\grading\rubric.json `
  --output reports\benchmarks\ctf-run-01\manual-grade.json `
  --worksheet-md reports\benchmarks\ctf-run-01\manual-grade.md
```

