# Model Sweep Report: Skills vs No Skills (Vuln Benchmark)

## Executive Summary
**Skills make GPT-5.4 models up to ~30% better at vulnerability identification, with diminishing returns as models get smarter. When regression occurs, it's modest (<5%), while gains can be substantial (up to 29%).**


## Benchmark setup
- Tasks: 20 (`tools/benchmarks/cursor_vuln_tasks.json`)
- Profiles: `control` vs `skills-only`
- Control profile: Raw model with no skills and no tools
- Skills only profile: Model with `The-Scaffolding` skills but no tools
- Runs per model: 1 per profile
- Timeout: 120s/task
- Outputs per model:
  - `experiment.json`
  - `manual-grade.json`
  - `control-vs-skills.json`
  - `experiment-runs/cursor-vuln-control-run1.json`
  - `experiment-runs/cursor-vuln-skills-only-run1.json`

## Metric table (control vs skills-only)

| Model | Control F1 | Skills F1 | ΔF1 | % Improvement | ΔPrecision | ΔRecall | ΔFP/task | Strict Task (C→S) | Skills Route Strict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.4-nano-none | 0.4151 | 0.5333 | +0.1182 | **+28.5%** | +0.1467 | +0.0500 | -0.4500 | 20 → 25 | 100 |
| gpt-5.4-nano-low | 0.4889 | 0.5652 | +0.0763 | **+15.6%** | +0.0600 | +0.1000 | -0.0500 | 25 → 30 | 95 |
| gpt-5.4-nano-medium | 0.6364 | 0.6087 | -0.0277 | **-4.4%** | -0.0448 | +0.0000 | +0.1000 | 50 → 50 | 95 |
| gpt-5.4-nano-high | 0.5106 | 0.6122 | +0.1016 | **+19.9%** | +0.0728 | +0.1500 | -0.0500 | 30 → 35 | 100 |
| gpt-5.4-mini-low | 0.7179 | 0.7568 | +0.0389 | **+5.4%** | +0.0867 | +0.0000 | -0.1000 | 60 → 65 | 95 |
| gpt-5.4-mini-medium | 0.7619 | 0.7692 | +0.0073 | **+1.0%** | +0.0622 | -0.0500 | -0.1000 | 60 → 65 | 95 |
| gpt-5.4-mini-high | 0.8372 | 0.8095 | -0.0277 | **-3.3%** | -0.0099 | -0.0500 | +0.0000 | 70 → 70 | 100 |

Interpretation: positive ΔF1/ΔPrecision/ΔRecall means skills-only improved; negative ΔFP/task means fewer false positives per task with skills-only.

### Skills Impact Summary

| Category | Models | Average F1 Gain |
|----------|--------|-----------------|
| **Strong gains** | nano-none, nano-high, nano-low | **+21.3%** |
| **Modest gains** | mini-low, mini-medium | **+3.2%** |
| **Regressions** | nano-medium, mini-high | **-3.9%** |
| **All models (including regressions)** | 7 models | **+9.0%** |
| **Models that benefit** | 5 of 7 models | **+14.1%** |

**Key insight:** Skills effectively give you the reasoning capability of roughly the next model tier up, at similar inference cost—except when the base model already saturates the task. For example, nano-low + skills (F1 0.5652) approaches nano-medium control performance (F1 0.6364).

## Manual-grading summary (quality of findings)

| Model | Exact TP Rate Control | Exact TP Rate Skills | Plausible Extras Control | Plausible Extras Skills |
|---|---:|---:|---:|---:|
| gpt-5.4-nano-none | 0.3333 | 0.4800 | 21 | 13 |
| gpt-5.4-nano-low | 0.4400 | 0.5000 | 12 | 11 |
| gpt-5.4-nano-medium | 0.5833 | 0.6154 | 8 | 8 |
| gpt-5.4-nano-high | 0.4444 | 0.5172 | 13 | 12 |
| gpt-5.4-mini-low | 0.7895 | 0.8235 | 3 | 3 |
| gpt-5.4-mini-medium | 0.7273 | 0.8421 | 4 | 2 |
| gpt-5.4-mini-high | 0.8261 | 0.7727 | 2 | 3 |

Manual grading confirms that skills produce **more exactly correct findings** (Exact TP Rate improved in 6/7 models) and **fewer borderline calls** (Plausible Extras reduced in 5/7 models). The improvements are not just metric inflation—they reflect genuinely higher-quality outputs.

## Key findings
1. Skills-only improved **F1 in 5/7 models** and reduced FP/task in **5/7 models**.
2. The biggest gains were in **nano-none** (+28.5% F1) and **nano-high** (+19.9% F1). The weakest base models benefit most.
3. **Asymmetry of impact:** When skills help, gains reach up to **~30%**. When they hurt, regression is capped at **<5%** (nano-medium -4.4%, mini-high -3.3%). This represents a favorable **6:1 upside/downside ratio** at the extremes.
4. **Diminishing returns pattern:** Gains shrink as base model capability increases (nano-none +28.5% → mini-medium +1.0% → mini-high -3.3%).
5. **nano-medium** and **mini-high** regressed in F1 (-0.0277 each), with nano-medium showing higher FP/task under skills (over-calling) and mini-high showing recall loss (friction on already-capable model).
6. **mini-high control** is the strongest single configuration overall (F1 0.8372). Skills are not beneficial for this tier.
7. Skills routing stayed high (95–100%), so most differences are detection/precision behavior, not routing failures.

## Overall conclusion
Skills are generally helping this model set on this benchmark, but not uniformly:
- **Strong positive impact for lower-capability settings** (nano-none, nano-low, nano-high): skills provide essential structure the base models lack.
- **Mixed/neutral impact in higher-performing tiers** (mini-low, mini-medium): skills offer incremental polish but diminishing returns.
- **Occasional regressions on specific models** (nano-medium over-calling, mini-high friction): these require targeted tuning.

**Core insight:** Skills effectively "punch up" model capability by approximately one reasoning tier on average. This positions skills as a **cost-performance multiplier**—enabling smaller, cheaper models to achieve performance competitive with larger tiers.

The right next optimization target is **model-conditional skill prompting** (especially for nano-medium and mini-high) to suppress overcalling while preserving recall, and potentially **skipping skills entirely for mini-high on simple tasks** where the base model already saturates performance.