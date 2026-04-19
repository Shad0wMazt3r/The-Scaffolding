# The Scaffolding - Bug Bounty & CTF Harness


## Agent-Agnostic Offensive Orchestration

The Scaffolding is an open framework for autonomously solving CTF challenges and conducting bug bounty research. It bridges high-level security reasoning with deterministic execution by combining the Model Context Protocol (MCP) with a persistent, self-improving agent knowledge base.

**Plug it into any AI agent: Claude Code, GitHub Copilot, Codex, Gemini, OpenCode, and others, with minimal configuration.**

## What It Does

Most AI agents fail at offensive security tasks because they lack structured recon, get overwhelmed by noise, and lose context across long sessions. The Scaffolding solves this by providing:

- **Structured skill loading**: agents load only the skills relevant to the current challenge type (web, pwn, crypto, etc.), keeping context clean
- **LatticeMind integration**:  automated scanning with confidence-scored findings, so the agent reasons over signal not noise
- **Kali MCP integration**:  direct access to standard security tooling without manual setup
- **Persistent notes**: session state is externalized, preventing context rot on long solves
- **Self-improving documentation**: solve outcomes feed back into skill files, making the harness better over time

## Demo

The following is a demo of an agent using The Scaffolding to solve a hard web challenge.

https://github.com/user-attachments/assets/5774267e-0e5c-414b-99d3-1b9de2bc0444

## Architecture

<img width="865" height="873" alt="Screenshot 2026-04-11 021928" src="https://github.com/user-attachments/assets/03f7bd4d-addc-467b-abda-a074f03db30c" />

The agent sits at the center of three tool layers:

- **LatticeMind** — runs targeted scans, scores findings by confidence, surfaces candidates for the agent to reason through
- **Kali MCP** — executes standard security tools on demand
- **GitHub MCP** — searches for exploits, PoCs, and reference implementations

The bootstrap skill loads domain-specific knowledge at session start. Notes persist session state and feed back into skills after each solve.

## Get Started

**Prerequisites**
- Docker
- An AI agent with MCP support

**Setup**

1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your API keys / paths
3. Setup MCPs and launch your preferred agent using the scaffold script:
   ```bash
   pip install -r scaffold/requirements.txt
   python scaffold.py
   ```
   *The interactive TUI will let you configure MCPs, initialize projects, and launch agents (Gemini, Cursor, OpenCode, Codex, Copilot, Claude, Antigravity).*


## Project Structure

```
(root)/
├── .agents/              # Agent skill definitions
├── .cursor/              # Cursor IDE configuration
├── .gemini/              # Gemini CLI configuration
├── .github/              # GitHub integration
├── .opencode/            # OpenCode agent configuration
├── kali-mcp/             # Kali Linux MCP server integration
├── AGENTS.md             # Shared agent instructions
├── HUMAN.md              # Human-facing documentation
└── README.md
```

## Skills

Domain-specific skill files are loaded by the agent based on challenge type. Each skill encodes recon patterns, attack chains, and lessons learned from past solves.

| Skill | Coverage |
|---|---|
| `agent-setup` | Tool readiness and dependency checks |
| `agent-calibration` | Workflow optimization and feedback |
| `crypto` | Encoding, RSA, elliptic curve, hash attacks |
| `forensics` | File, memory, network, and multimedia analysis |
| `mobile` | Mobile application security testing |
| `network` | Reconnaissance and network assessment |
| `pwn` | Stack, heap, and format string exploitation |
| `recon` | Target discovery and reconnaissance |
| `reverse-engineering` | Binary analysis and RE |
| `web` | Web application security testing |

## Skill Contract and Baseline Metrics

To keep skill quality consistent across agents, this repository includes:

- Canonical contract: `.agents/standards/skill-contract.yaml`
- Machine-readable contract: `.agents/standards/skill-contract.json`
- Quality gate config: `.agents/standards/quality-gate.json`
- Router single source of truth: `.agents/standards/router-spec.json`
- Reproducible baseline generator: `tools/skills/baseline_metrics.py`
- Validator: `tools/skills/validate_skills.py`
- Normalizer: `tools/skills/normalize_skills.py`
- Router generator: `tools/skills/generate_router_wrappers.py`
- Smoke eval gate: `tools/skills/smoke_eval.py`
- Current baseline snapshot: `reports/skill-baseline.json`

Common commands:

```bash
# Generate baseline
python tools/skills/baseline_metrics.py --output reports/skill-baseline.json

# Normalize known markdown issues
python tools/skills/normalize_skills.py --write --fix-footnotes

# Check normalization drift (CI-safe)
python tools/skills/normalize_skills.py --check --fix-footnotes

# Validate against contract
python tools/skills/validate_skills.py --report reports/skill-validation.json

# Regenerate all router wrappers from one spec
python tools/skills/generate_router_wrappers.py

# Run end-to-end quality gate
python tools/skills/smoke_eval.py --output reports/skill-smoke-eval.json
```

CI enforcement lives in `.github/workflows/skills-quality.yml`.

### Low-cost Cursor auto benchmark (<=15 tasks)

Use the phase-routing benchmark to sanity-check real agent behavior at low cost:
All benchmark runners default to `--model composer-2` for consistent A/B comparisons.

```bash
python tools/benchmarks/run_cursor_phase_benchmark.py ^
  --tasks tools/benchmarks/cursor_phase_tasks.json ^
  --max-tasks 10 ^
  --timeout-sec 20 ^
  --output reports/benchmarks/cursor-auto-phase-benchmark.json
```

Task set file: `tools/benchmarks/cursor_phase_tasks.json` (10 tasks by default; hard max 15).

### Security benchmark (skills-only now, MCP comparison later)

Run the richer security benchmark with skills-only profile first:

```bash
python tools/benchmarks/run_cursor_security_benchmark.py ^
  --profile skills-only ^
  --tasks tools/benchmarks/cursor_security_tasks.json ^
  --max-tasks 12 ^
  --timeout-sec 20 ^
  --output reports/benchmarks/cursor-security-skills-only.json
```

Later, after enabling Kali/Lattice MCP, run:

```bash
python tools/benchmarks/run_cursor_security_benchmark.py ^
  --profile mcp-enabled ^
  --tasks tools/benchmarks/cursor_security_tasks.json ^
  --max-tasks 12 ^
  --timeout-sec 20 ^
  --output reports/benchmarks/cursor-security-mcp-enabled.json
```

Then compare:

```bash
python tools/benchmarks/compare_cursor_benchmarks.py ^
  --baseline reports/benchmarks/cursor-security-skills-only.json ^
  --candidate reports/benchmarks/cursor-security-mcp-enabled.json ^
  --output reports/benchmarks/cursor-security-comparison.json
```

### Vulnerability-finding benchmark (ground-truth quality)

Run hard-but-low-cost vuln-finding benchmark (up to 20 tasks) with strict JSON findings and TP/FP/FN scoring:

```bash
python tools/benchmarks/run_cursor_vuln_benchmark.py ^
  --profile control ^
  --model composer-2 ^
  --tasks tools/benchmarks/cursor_vuln_tasks.json ^
  --max-tasks 20 ^
  --timeout-sec 120 ^
  --store-raw-output ^
  --output reports/benchmarks/cursor-vuln-control.json

python tools/benchmarks/run_cursor_vuln_benchmark.py ^
  --profile skills-only ^
  --model composer-2 ^
  --tasks tools/benchmarks/cursor_vuln_tasks.json ^
  --max-tasks 20 ^
  --timeout-sec 120 ^
  --store-raw-output ^
  --output reports/benchmarks/cursor-vuln-skills-only.json
```

Later (after enabling MCPs):

```bash
python tools/benchmarks/run_cursor_vuln_benchmark.py ^
  --profile mcp-enabled ^
  --model composer-2 ^
  --tasks tools/benchmarks/cursor_vuln_tasks.json ^
  --max-tasks 20 ^
  --timeout-sec 120 ^
  --store-raw-output ^
  --output reports/benchmarks/cursor-vuln-mcp-enabled.json
```

Compare two vuln runs:

```bash
python tools/benchmarks/compare_cursor_vuln_benchmarks.py ^
  --baseline reports/benchmarks/cursor-vuln-control.json ^
  --candidate reports/benchmarks/cursor-vuln-skills-only.json ^
  --output reports/benchmarks/cursor-vuln-control-vs-skills.json
```

Run a 2-run experiment (control vs skills-only) and aggregate:

```bash
python tools/benchmarks/run_cursor_vuln_experiment.py ^
  --profiles control skills-only ^
  --runs 2 ^
  --model composer-2 ^
  --tasks tools/benchmarks/cursor_vuln_tasks.json ^
  --max-tasks 20 ^
  --timeout-sec 120 ^
  --store-raw-output ^
  --output reports/benchmarks/cursor-vuln-experiment-runs2.json
```

Generate objective + subjective grading from all run responses:

```bash
python tools/benchmarks/grade_cursor_vuln_responses.py ^
  --experiment reports/benchmarks/cursor-vuln-experiment-runs2.json ^
  --output reports/benchmarks/cursor-vuln-manual-grade.json
```

By default, vuln comparison focuses on efficacy metrics; add `--include-cost` only when you explicitly want latency/token deltas.

---

## Design Philosophy

The Scaffolding is token-efficient by design. Skills are loaded selectively, notes externalize state rather than consuming context, and LatticeMind's confidence scoring prevents the agent from reasoning over irrelevant findings. It runs fully locally or on cloud infrastructure depending on your setup.


## Responsible Use

This project is intended for security research and education. Only use it against systems you are authorized to test.

### Acknowledgements
- [k3nn3dy-ai](https://github.com/k3nn3dy-ai) for [Kali MCP](https://github.com/k3nn3dy-ai/kali-mcp) — 
  an essential part of this harness that provides direct access to Kali 
  Linux security tooling through the Model Context Protocol.
