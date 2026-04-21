# Model Sweep Report (3 Runs): Skills vs No Skills

## Executive summary
All requested reruns are complete: **11 models**, **3 runs/profile** (`control` vs `skills-only`), **20 tasks/run**.

Across 3-run means, skills are net positive but highly model-dependent:
- **Objective:** macro F1 **0.6591 -> 0.6695** (**+0.0104**), with **6/11** models improving.
- **Subjective:** macro score **3.8426 -> 3.8765** (**+0.0339**), with **7/11** models improving.
- **Stability:** F1 stddev improves on **7/11** models (mean **0.0426 -> 0.0383**).
- **Diminishing returns:** baseline strength strongly anti-correlates with skill uplift (**corr = -0.81**).

---

## Setup
- Tasks: `tools/benchmarks/cursor_vuln_tasks.json` (20 tasks)
- Profiles: `control`, `skills-only`
- Runs per model/profile: 3
- Timeout: 120s/task
- Primary artifacts:
  - `reports/benchmarks/model-sweep/<model>/experiment-runs3.json`
  - `reports/benchmarks/model-sweep/<model>/manual-grade-runs3.json`

---

## Objective + subjective by model (3-run means)

| Model | Control F1 | Skills F1 | ΔF1 | ΔFP/task | ΔStrict | F1 stddev (C->S) | ΔSubjective |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.1-codex-mini-low | 0.4774 | 0.5926 | **+0.1152** | +0.1667 | +20.00 | 0.0547->0.0524 | +0.0555 |
| gpt-5.4-nano-none | 0.4384 | 0.5011 | **+0.0627** | -0.2667 | +11.67 | 0.0440->0.0315 | -0.0178 |
| gpt-5.4-nano-low | 0.5137 | 0.5663 | **+0.0526** | -0.1333 | +10.00 | 0.0179->0.0452 | -0.1020 |
| gpt-5.4-nano-high | 0.5877 | 0.6197 | **+0.0320** | -0.0834 | +1.67 | 0.0545->0.0132 | +0.0488 |
| gpt-5.4-mini-low | 0.7409 | 0.7609 | **+0.0200** | -0.0500 | -1.67 | 0.0580->0.0058 | +0.0434 |
| gemini-3-flash | 0.7145 | 0.7329 | **+0.0184** | -0.0834 | +0.00 | 0.0369->0.0380 | +0.0930 |
| kimi-k2.5 | 0.6959 | 0.6803 | -0.0156 | +0.0333 | -6.67 | 0.0232->0.0737 | +0.0175 |
| claude-4.6-sonnet-medium | 0.7875 | 0.7697 | -0.0178 | +0.1334 | -10.00 | 0.0479->0.0302 | **+0.2666** |
| gpt-5.4-mini-high | 0.8384 | 0.8035 | -0.0349 | +0.0167 | -6.67 | 0.0319->0.0169 | -0.1043 |
| gpt-5.4-nano-medium | 0.6647 | 0.6088 | -0.0559 | +0.1000 | -5.00 | 0.0707->0.0694 | +0.0822 |
| gpt-5.4-mini-medium | 0.7906 | 0.7286 | -0.0620 | +0.0333 | -3.33 | 0.0284->0.0445 | -0.0100 |

---

## Deep dive: how skills helped, and where they hurt

### 1) Where skills helped
The strongest improvements are concentrated on weaker baselines:
- **Low baseline group (control F1 < 0.60):** avg **ΔF1 +0.0656**, avg **ΔFP/task -0.0792**, avg **ΔStrict +10.83**.
- This pattern appears in `gpt-5.1-codex-mini-low` and nano tiers (`none`, `low`, `high`).

Interpretation:
1. Skills improve output structure adherence and reduce omission errors.
2. Skills increase candidate coverage enough to materially lift recall/strict hit rates.
3. For weaker models, extra structure offsets under-specification and hesitation.

### 2) Where skills hindered
Regressions are concentrated on stronger baselines:
- **High baseline group (control F1 >= 0.75):** avg **ΔF1 -0.0382**, avg **ΔFP/task +0.0611**, avg **ΔStrict -6.67**.
- Regressions cluster in `gpt-5.4-mini-high`, `gpt-5.4-mini-medium`, and `claude-4.6-sonnet-medium`.

Interpretation:
1. Strong models already have robust internal reasoning; heavy scaffolding can become overhead.
2. Over-constraining output can shift effort from discrimination to format compliance.
3. Added skill text can increase verbosity and marginal claims, increasing FP pressure.

### 3) Mixed-family behavior
- **Gemini 3 Flash:** objective improves slightly (**+0.0184 F1**) with better precision/lower FP, but chain success collapses (**66.7% -> 0%**). Skills help single-finding precision but hurt chain-oriented behavior.
- **Kimi K2.5:** objective regresses (**-0.0156 F1**, strict down, FP up), while subjective nudges up (**+0.0175**). Better narrative feel, worse exploit discrimination.
- **Sonnet 4.6:** largest subjective gain (**+0.2666**) but objective regression (**-0.0178**) and FP increase.

---

## If baseline is already strong, how skills should change

For strong baselines, use **skills-lite**, not full scaffolding:

1. **Compress instruction surface**
   - Keep only: expected output schema + hard evidence requirements.
   - Remove long rubric text and repeated phrasing.

2. **Evidence-gated claims**
   - Require at least one concrete anchor (`file+line` or endpoint+payload+observable effect) before allowing a finding.
   - For high-baseline models, this is more impactful than additional reasoning instructions.

3. **Top-K candidate cap before expansion**
   - Force initial shortlist (`K=2-3`) before detailed writeups.
   - Reduces over-calling and keeps attention on highest-confidence vulnerabilities.

4. **Optional chain mode, not mandatory**
   - Enable chain-specific fields only when model reports explicit multi-step preconditions.
   - Avoid forcing chain narrative into tasks that are single-hop by nature.

5. **Two-pass discriminator for high-baseline models**
   - Pass 1: candidate generation.
   - Pass 2: adversarial self-check ("why this may be false") + exploitability confirmation.
   - Keep pass-2 short and evidence-first.

6. **Model-conditional routing**
   - `mini-high`: default control or skills-lite.
   - `sonnet`: skills for reporting mode, control for strict triage mode.
   - `gemini`: control for chain-heavy tasks, skills-lite for precision triage.

---

## Visuals

### Visual A: ΔF1 (skills - control)
```text
+0.12 | gpt-5.1-codex-mini-low   ████████████
+0.06 | gpt-5.4-nano-none        ██████
+0.05 | gpt-5.4-nano-low         █████
+0.03 | gpt-5.4-nano-high        ███
+0.02 | gpt-5.4-mini-low         ██
+0.02 | gemini-3-flash           ██
-0.02 | kimi-k2.5                ░░
-0.02 | claude-4.6-sonnet-medium ░░
-0.03 | gpt-5.4-mini-high        ░░░
-0.06 | gpt-5.4-nano-medium      ░░░░░░
-0.06 | gpt-5.4-mini-medium      ░░░░░░
```

### Visual B: Baseline strength vs uplift
```text
Correlation(control F1, ΔF1) = -0.81
Low baseline  -> larger positive skill lift
High baseline -> flat/negative skill lift
```

### Visual C: Objective vs subjective quadrants
```text
Obj+, Subj+:  gemini-3-flash, gpt-5.1-codex-mini-low, gpt-5.4-mini-low, gpt-5.4-nano-high
Obj+, Subj-:  gpt-5.4-nano-none, gpt-5.4-nano-low
Obj-, Subj+:  claude-4.6-sonnet-medium, kimi-k2.5, gpt-5.4-nano-medium
Obj-, Subj-:  gpt-5.4-mini-high, gpt-5.4-mini-medium
```

---

## Online pricing snapshot (input/output, USD per 1M tokens)

> Note: Cursor model IDs (`gpt-5.4-mini-high`, etc.) are routing/tier aliases. Pricing is mapped to closest published provider SKUs. Thinking tiers mostly change token volume/latency, not unit token price.

| Benchmark model(s) | Pricing model used | Input $/MTok | Output $/MTok | Source |
|---|---|---:|---:|---|
| `gpt-5.4-nano-*` | `openai/gpt-5-nano` | 0.05 | 0.40 | OpenRouter models API |
| `gpt-5.4-mini-*` | `openai/gpt-5-mini` | 0.25 | 2.00 | OpenRouter models API |
| `gpt-5.1-codex-mini-low` | `openai/gpt-5.1-codex-mini` | 0.25 | 2.00 | OpenRouter models API |
| `gemini-3-flash` | Gemini Flash Standard tier | 0.25 | 1.50 | Google Gemini API pricing |
| `claude-4.6-sonnet-medium` | Sonnet 4.6 | 3.00 | 15.00 | Anthropic pricing |
| `kimi-k2.5` | `moonshotai/kimi-k2.5` | 0.3827 | 1.72 | OpenRouter models API |

### Output-cost pressure (important for verbose report stages)
```text
Lower output $/MTok is better for long-form generation:
gpt-5-nano 0.40 < gemini-flash 1.50 < kimi-k2.5 1.72 < gpt-5-mini/codex-mini 2.00 << sonnet 15.00
```

---

## Cost-constrained stage routing for CTF / bug bounty / pentest

| Stage | Constraint profile | Best model/profile | Why |
|---|---|---|---|
| Recon + broad surface sweep | Lowest cost, high volume | `gpt-5.4-nano-low` + skills | Strong low-cost uplift; low unit pricing; good FP reduction vs control in nano tiers. |
| Candidate vuln triage | Balanced cost/quality | `gpt-5.4-mini-low` + skills | Positive F1 delta with lower FP/task; stable across runs. |
| High-confidence exploit triage | Max objective accuracy | `gpt-5.4-mini-high` control | Best raw objective accuracy in this benchmark; avoids high-baseline skills drag. |
| Chain-heavy exploitation paths | Preserve chain behavior | `gemini-3-flash` control (or skills-lite) | Skills improved precision but collapsed chain success; control safer for chaining tasks. |
| Evidence-heavy verification pass | Keep false claims down | `gpt-5.4-mini-high` control + verifier pass | Strong discriminator with less scaffolding overhead. |
| Final report writing / analyst handoff | Highest narrative quality | `claude-4.6-sonnet-medium` + skills | Largest subjective quality gain; best when clarity is prioritized over raw F1. |
| Budget-constrained but strong uplift needed | Max gain per dollar | `gpt-5.1-codex-mini-low` + skills | Largest F1 lift, but pair with strict verifier to counter FP increase. |

---

## What to change next in scaffolding
1. Ship **skills-lite** and auto-route high-baseline models to it.
2. Add **evidence-gating + top-K cap** before full writeups.
3. Split task modes:
   - **discovery mode** (coverage, cheap models, skills on),
   - **verification mode** (strict, high-baseline models, skills-lite/control),
   - **report mode** (subjective quality, Sonnet + skills).
4. Add chain-mode toggles by task type (do not force chain fields globally).

---

## Pricing source links used
- Google Gemini pricing: `https://ai.google.dev/gemini-api/docs/pricing`
- Anthropic pricing: `https://www.anthropic.com/pricing`
- Moonshot pricing landing page: `https://platform.moonshot.ai/pricing`
- OpenRouter models API (model-level token pricing): `https://openrouter.ai/api/v1/models`

---

## MCP-enabled benchmark update (11 models, single run each)

### Scope
- Profile: `mcp-enabled`
- Tasks: `tools/benchmarks/cursor_vuln_tasks.json` (20 tasks/model)
- Verifier pass: enabled (`--verify-findings`)
- Artifact root: `reports/benchmarks/model-sweep-mcp-enabled/`
- Run log: `reports/benchmarks/model-sweep-mcp-enabled/run-log.json`

### Environment state used for this run
- Playwright MCP disabled for Cursor (`C:\Users\er123\.cursor\mcp.json`).
- `lattice-mind` endpoint healthy on `http://localhost:8000/mcp`.
- `kali-mcp-server` endpoint healthy on `http://localhost:8137/sse`.
- `github-mcp` Docker image present and resolvable by scaffold health checks.
- `ghidra-mcp` SSE bridge healthy on `http://127.0.0.1:8081/sse` (bridge up; Ghidra HTTP backend not active on `:8080` during this run).

### Aggregate snapshot (macro over 11 model runs)
- Macro F1: **0.6098**
- Macro precision / recall: **0.6695 / 0.5818**
- Macro strict task accuracy: **46.36%**
- Macro FP per task: **0.3000**
- Skill anchor presence / strict route accuracy: **98.18% / 98.18%**
- Total wall-clock across all 11 runs: **5445.90s** (**1.51h**)

### Comparison vs no-skills and skills-only baselines

| Profile | Basis | Macro F1 | Macro strict task accuracy |
|---|---|---:|---:|
| control | 3-run mean | 0.6591 | 50.45% |
| skills-only | 3-run mean | 0.6695 | 51.36% |
| mcp-enabled | single run | 0.6098 | 46.36% |

- **MCP vs control:** ΔF1 **-0.0492**, Δstrict **-4.09** pts.
- **MCP vs skills-only:** ΔF1 **-0.0597**, Δstrict **-5.00** pts.
- Model-level wins:
  - MCP F1 > control on **3/11** models.
  - MCP F1 > skills-only on **1/11** models.
  - MCP strict > control on **2/11** models.
  - MCP strict > skills-only on **2/11** models.

### Per-model delta (MCP vs control/skills-only)

| Model | Control F1 (3-run) | Skills F1 (3-run) | MCP F1 | ΔMCP-Control | ΔMCP-Skills |
|---|---:|---:|---:|---:|---:|
| gpt-5.1-codex-mini-low | 0.4774 | 0.5926 | 0.3846 | -0.0928 | -0.2080 |
| gpt-5.4-nano-none | 0.4384 | 0.5011 | 0.4737 | +0.0353 | -0.0274 |
| gpt-5.4-nano-low | 0.5137 | 0.5663 | 0.6111 | +0.0974 | +0.0448 |
| gpt-5.4-nano-high | 0.5877 | 0.6197 | 0.4865 | -0.1012 | -0.1332 |
| gpt-5.4-mini-low | 0.7409 | 0.7609 | 0.7368 | -0.0041 | -0.0241 |
| gemini-3-flash | 0.7145 | 0.7329 | 0.7317 | +0.0172 | -0.0012 |
| kimi-k2.5 | 0.6959 | 0.6803 | 0.6500 | -0.0459 | -0.0303 |
| claude-4.6-sonnet-medium | 0.7875 | 0.7697 | 0.5854 | -0.2021 | -0.1843 |
| gpt-5.4-mini-high | 0.8384 | 0.8035 | 0.8000 | -0.0384 | -0.0035 |
| gpt-5.4-nano-medium | 0.6647 | 0.6088 | 0.5641 | -0.1006 | -0.0447 |
| gpt-5.4-mini-medium | 0.7906 | 0.7286 | 0.6842 | -0.1064 | -0.0444 |

### Per-model outcomes

| Model | F1 | Strict task accuracy | Elapsed (s) | Output |
|---|---:|---:|---:|---|
| gpt-5.4-mini-high | 0.8000 | 65.00% | 546.36 | `reports/benchmarks/model-sweep-mcp-enabled/gpt-5.4-mini-high/cursor-vuln-mcp-enabled.json` |
| gpt-5.4-mini-low | 0.7368 | 60.00% | 412.18 | `reports/benchmarks/model-sweep-mcp-enabled/gpt-5.4-mini-low/cursor-vuln-mcp-enabled.json` |
| gemini-3-flash | 0.7317 | 60.00% | 780.53 | `reports/benchmarks/model-sweep-mcp-enabled/gemini-3-flash/cursor-vuln-mcp-enabled.json` |
| gpt-5.4-mini-medium | 0.6842 | 50.00% | 447.31 | `reports/benchmarks/model-sweep-mcp-enabled/gpt-5.4-mini-medium/cursor-vuln-mcp-enabled.json` |
| kimi-k2.5 | 0.6500 | 50.00% | 611.91 | `reports/benchmarks/model-sweep-mcp-enabled/kimi-k2.5/cursor-vuln-mcp-enabled.json` |
| gpt-5.4-nano-low | 0.6111 | 55.00% | 346.30 | `reports/benchmarks/model-sweep-mcp-enabled/gpt-5.4-nano-low/cursor-vuln-mcp-enabled.json` |
| claude-4.6-sonnet-medium | 0.5854 | 30.00% | 418.14 | `reports/benchmarks/model-sweep-mcp-enabled/claude-4.6-sonnet-medium/cursor-vuln-mcp-enabled.json` |
| gpt-5.4-nano-medium | 0.5641 | 35.00% | 470.09 | `reports/benchmarks/model-sweep-mcp-enabled/gpt-5.4-nano-medium/cursor-vuln-mcp-enabled.json` |
| gpt-5.4-nano-high | 0.4865 | 35.00% | 550.02 | `reports/benchmarks/model-sweep-mcp-enabled/gpt-5.4-nano-high/cursor-vuln-mcp-enabled.json` |
| gpt-5.4-nano-none | 0.4737 | 40.00% | 320.59 | `reports/benchmarks/model-sweep-mcp-enabled/gpt-5.4-nano-none/cursor-vuln-mcp-enabled.json` |
| gpt-5.1-codex-mini-low | 0.3846 | 30.00% | 542.47 | `reports/benchmarks/model-sweep-mcp-enabled/gpt-5.1-codex-mini-low/cursor-vuln-mcp-enabled.json` |

### Notes
- This MCP-enabled slice is a **single-run** view and should not be interpreted as a stability estimate.
- For trend-level conclusions, compare against the existing 3-run `control` vs `skills-only` sections above.

