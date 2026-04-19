# Model Sweep Report: Skills vs No Skills (Vuln Benchmark)

## Executive summary
Across 11 completed model sweeps, skills improved objective F1 on 7 models and regressed on 4.  
The strongest objective configuration remains **`gpt-5.4-mini-high` control** (F1 0.8372), while the largest skills gain is **`gpt-5.1-codex-mini-low`** (+0.1506 F1).


## Benchmark setup
- Tasks: 20 (`tools/benchmarks/cursor_vuln_tasks.json`)
- Profiles: `control` vs `skills-only`
- Runs per model: 1 per profile
- Timeout: 120s/task
- Artifacts per model:
  - `experiment.json`
  - `manual-grade.json`
  - `control-vs-skills.json`
  - `experiment-runs/cursor-vuln-control-run1.json`
  - `experiment-runs/cursor-vuln-skills-only-run1.json`

## Objective metrics (control vs skills-only)

| Model | Control F1 | Skills F1 | ΔF1 | ΔPrecision | ΔRecall | ΔFP/task |
|---|---:|---:|---:|---:|---:|---:|
| claude-4.6-sonnet-medium | 0.7273 | 0.7347 | +0.0074 | -0.0460 | +0.1000 | +0.1500 |
| gemini-3-flash | 0.7660 | 0.6818 | -0.0842 | -0.0417 | -0.1500 | +0.0000 |
| gpt-5.1-codex-mini-low | 0.5161 | 0.6667 | +0.1506 | +0.0227 | +0.2000 | +0.0500 |
| gpt-5.4-mini-high | 0.8372 | 0.8095 | -0.0277 | -0.0099 | -0.0500 | +0.0000 |
| gpt-5.4-mini-low | 0.7179 | 0.7568 | +0.0389 | +0.0867 | +0.0000 | -0.1000 |
| gpt-5.4-mini-medium | 0.7619 | 0.7692 | +0.0073 | +0.0622 | -0.0500 | -0.1000 |
| gpt-5.4-nano-high | 0.5106 | 0.6122 | +0.1016 | +0.0728 | +0.1500 | -0.0500 |
| gpt-5.4-nano-low | 0.4889 | 0.5652 | +0.0763 | +0.0600 | +0.1000 | -0.0500 |
| gpt-5.4-nano-medium | 0.6364 | 0.6087 | -0.0277 | -0.0448 | +0.0000 | +0.1000 |
| gpt-5.4-nano-none | 0.4151 | 0.5333 | +0.1182 | +0.1467 | +0.0500 | -0.4500 |
| kimi-k2.5 | 0.6977 | 0.5833 | -0.1144 | -0.1522 | -0.0500 | +0.3000 |

## Visual 1: ΔF1 (skills - control)
Scale: ~1 block = 0.01 F1

```text
gpt-5.1-codex-mini-low  +0.1506  ███████████████
gpt-5.4-nano-none       +0.1182  ████████████
gpt-5.4-nano-high       +0.1016  ██████████
gpt-5.4-nano-low        +0.0763  ████████
gpt-5.4-mini-low        +0.0389  ████
claude-4.6-sonnet-medium+0.0074  █
gpt-5.4-mini-medium     +0.0073  █
gpt-5.4-mini-high       -0.0277  ░░░
gpt-5.4-nano-medium     -0.0277  ░░░
gemini-3-flash          -0.0842  ░░░░░░░░
kimi-k2.5               -0.1144  ░░░░░░░░░░░
```

## Subjective grading summary

| Model | Control subjective | Skills subjective | ΔSubjective | Control exact TP rate | Skills exact TP rate |
|---|---:|---:|---:|---:|---:|
| claude-4.6-sonnet-medium | 3.5833 | 3.8966 | **+0.3133** | 0.7083 | 0.6207 |
| gemini-3-flash | 3.8519 | 3.8333 | -0.0186 | 0.7037 | 0.7083 |
| gpt-5.1-codex-mini-low | 3.7273 | 3.8125 | +0.0852 | 0.7273 | 0.8125 |
| gpt-5.4-mini-high | 3.8261 | 3.7273 | -0.0988 | 0.8261 | 0.7727 |
| gpt-5.4-mini-low | 3.7368 | 3.6471 | -0.0897 | 0.7895 | 0.8235 |
| gpt-5.4-mini-medium | 3.7727 | 3.6316 | -0.1411 | 0.7273 | 0.8421 |
| gpt-5.4-nano-high | 4.0370 | 4.0000 | -0.0370 | 0.4444 | 0.5172 |
| gpt-5.4-nano-low | 4.2000 | 4.1538 | -0.0462 | 0.4400 | 0.5000 |
| gpt-5.4-nano-medium | 3.8750 | 4.0000 | +0.1250 | 0.5833 | 0.6154 |
| gpt-5.4-nano-none | 4.2424 | 4.2400 | -0.0024 | 0.3333 | 0.4800 |
| kimi-k2.5 | 3.6522 | 3.6429 | -0.0093 | 0.6522 | 0.5000 |

### Sonnet 4.6 requested note
`claude-4.6-sonnet-medium` shows the **largest subjective improvement with skills**: **+0.3133** (3.5833 -> 3.8966), indicating materially better narrative clarity/explanation quality even though objective F1 gain is small (+0.0074).

## Deep dive: why Gemini performed worse with skills
Only one Gemini-family model was available (`gemini-3-flash`), and it regressed with skills:

- F1: **0.7660 -> 0.6818** (Δ -0.0842)
- Precision: **0.6667 -> 0.6250**
- Recall: **0.9000 -> 0.7500** (largest drop)
- FP/task: unchanged (**0.45 -> 0.45**)
- Strict accuracy: **60 -> 55**
- Chain success: **100 -> 0**
- Route strict: **100** (routing is not the issue)

Interpretation: this is **not** a routing failure and not mainly FP inflation; it is mostly a **recall/coverage collapse under skills constraints**. The skills prompt appears to add structure overhead that reduces finding completeness on this model.

## Deep dive: Kimi objective vs subjective
Kimi regressed the most objectively under skills:

- F1: **0.6977 -> 0.5833** (Δ -0.1144)
- Precision: **0.6522 -> 0.5000**
- Recall: **0.7500 -> 0.7000**
- FP/task: **0.40 -> 0.70**
- Strict accuracy: **65 -> 35**

Subjective view is flatter:

- Avg subjective: **3.6522 -> 3.6429** (near-neutral)
- Subjective score sum: **84 -> 102** (more total evaluated content)
- Chain success: **0 -> 100** (better chain articulation/completion behavior)

So Kimi’s “gain” from subjective grading is mostly **format/coverage of explanations and chain narrative**, but this does **not** convert to objective exploit discrimination (TP/FP), where it worsens.

## Cost-benefit analysis (skills profile)

| Model | Skills F1 | Skills avg tokens | Skills avg latency (s) | F1 per 1k tokens |
|---|---:|---:|---:|---:|
| gpt-5.4-mini-high | 0.8095 | 625.2 | 18.649 | 1.2948 |
| gpt-5.4-mini-medium | 0.7692 | 607.3 | 17.273 | 1.2666 |
| gpt-5.4-mini-low | 0.7568 | 600.8 | 14.051 | 1.2597 |
| claude-4.6-sonnet-medium | 0.7347 | 704.8 | 19.496 | 1.0424 |
| gpt-5.1-codex-mini-low | 0.6667 | 596.7 | 11.620 | 1.1173 |
| gemini-3-flash | 0.6818 | 636.4 | 27.728 | 1.0713 |
| kimi-k2.5 | 0.5833 | 689.0 | 28.449 | 0.8466 |

Takeaway: best quality-per-token among high performers is currently the GPT-5.4 mini family. Sonnet adds strong subjective quality but at higher token/latency cost.

## Model capability/use-case recommendations
1. **High-stakes vuln triage (best objective):** `gpt-5.4-mini-high` (control or lightly constrained skills).
2. **Balanced production default:** `gpt-5.4-mini-medium` with skills.
3. **Low-cost routine scanning:** `gpt-5.1-codex-mini-low` with skills (big uplift from skills).
4. **Report-writing / analyst handoff quality:** `claude-4.6-sonnet-medium` with skills (largest subjective gain).
5. **Gemini 3 Flash:** prefer control or a reduced “skills-lite” prompt until recall drop is fixed.
6. **Kimi K2.5:** prefer control for now; skills currently increase overcalling.

## Scaffolding improvements (model-adaptive)
1. **Skills-lite profile** for Gemini/Kimi: shorter schema, stricter top-1/top-2 cap, fewer narrative fields.
2. **Two-pass mode**: pass 1 discover candidates, pass 2 verify exploitability and drop weak claims.
3. **Model-conditional FP suppression**: stronger evidence requirements for models with rising FP/task.
4. **Adaptive output budget**: hard cap sentence lengths/field lengths to reduce verbosity-induced drift.
5. **Chain scoring split in reports**: keep chain quality separate from TP/FP so “good narrative, bad detection” is explicit.
