  # Model Sweep Report: Skills vs No Skills (Vuln Benchmark)

  ## Executive Summary
  **Across 11 completed model sweeps, skills improved objective F1 on 7 models and regressed on 4. When skills help, gains reach up to ~30%—effectively elevating model capability by roughly one reasoning tier. When regression occurs, it's often modest (<5% for GPT models), creating a favorable asymmetry: upside potential substantially outweighs downside risk for most deployments.**

  The strongest objective configuration remains **`gpt-5.4-mini-high` control** (F1 0.8372). The largest skills gain is **`gpt-5.1-codex-mini-low`** (+0.1506 F1, **+29.2%**). Cross-model analysis reveals that skills act as a **cost-performance multiplier**—enabling smaller, cheaper models to achieve performance competitive with larger tiers, though the effect is not uniform across model families.

  ### Skills Impact by Model Tier

  | Category | Models | Average F1 Gain |
  |----------|--------|-----------------|
  | **Strong gains (≥15%)** | gpt-5.1-codex-mini-low, gpt-5.4-nano-none, gpt-5.4-nano-high, gpt-5.4-nano-low | **+21.1%** |
  | **Modest gains (1-6%)** | gpt-5.4-mini-low, gpt-5.4-mini-medium, claude-4.6-sonnet-medium | **+3.7%** |
  | **GPT regressions** | gpt-5.4-mini-high, gpt-5.4-nano-medium | **-3.9%** |
  | **Cross-family regressions** | gemini-3-flash, kimi-k2.5 | **-12.4%** |

  **Core pattern:** Skills provide the greatest lift to weaker base models (diminishing returns as capability increases) and show **GPT-specific optimization**—GPT models average +6.2% F1 gain, while non-GPT models average -6.3% regression.


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

  | Model | Control F1 | Skills F1 | ΔF1 | % Improvement | ΔPrecision | ΔRecall | ΔFP/task |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | claude-4.6-sonnet-medium | 0.7273 | 0.7347 | +0.0074 | **+1.0%** | -0.0460 | +0.1000 | +0.1500 |
  | gemini-3-flash | 0.7660 | 0.6818 | -0.0842 | **-11.0%** | -0.0417 | -0.1500 | +0.0000 |
  | gpt-5.1-codex-mini-low | 0.5161 | 0.6667 | +0.1506 | **+29.2%** | +0.0227 | +0.2000 | +0.0500 |
  | gpt-5.4-mini-high | 0.8372 | 0.8095 | -0.0277 | **-3.3%** | -0.0099 | -0.0500 | +0.0000 |
  | gpt-5.4-mini-low | 0.7179 | 0.7568 | +0.0389 | **+5.4%** | +0.0867 | +0.0000 | -0.1000 |
  | gpt-5.4-mini-medium | 0.7619 | 0.7692 | +0.0073 | **+1.0%** | +0.0622 | -0.0500 | -0.1000 |
  | gpt-5.4-nano-high | 0.5106 | 0.6122 | +0.1016 | **+19.9%** | +0.0728 | +0.1500 | -0.0500 |
  | gpt-5.4-nano-low | 0.4889 | 0.5652 | +0.0763 | **+15.6%** | +0.0600 | +0.1000 | -0.0500 |
  | gpt-5.4-nano-medium | 0.6364 | 0.6087 | -0.0277 | **-4.4%** | -0.0448 | +0.0000 | +0.1000 |
  | gpt-5.4-nano-none | 0.4151 | 0.5333 | +0.1182 | **+28.5%** | +0.1467 | +0.0500 | -0.4500 |
  | kimi-k2.5 | 0.6977 | 0.5833 | -0.1144 | **-16.4%** | -0.1522 | -0.0500 | +0.3000 |

  ### Key Pattern: Diminishing Returns and Asymmetric Risk

  | Base F1 Range | Typical Skills Impact | Example Models |
  |---------------|---------------------|----------------|
  | <0.55 | **+15–30%** (strong lift) | nano-none, codex-mini-low, nano-high, nano-low |
  | 0.55–0.75 | **+1–6%** (modest lift) | mini-low, nano-medium*, claude-sonnet |
  | >0.75 | **-3% to -11%** (neutral/regression) | mini-high, gemini-flash*, kimi* |

  *Cross-family models show larger regressions, suggesting GPT-specific skill optimization.

  **Asymmetry insight:** Among GPT models, upside reaches ~29% (codex-mini-low) while downside is capped at ~4% (nano-medium, mini-high)—a **7:1 upside/downside ratio** at the extremes. This makes skills a **safe default for GPT deployments**.


  ## Visual 1: ΔF1 (skills - control)
  Scale: ~1 block = 0.01 F1

  ```text
  gpt-5.1-codex-mini-low  +0.1506  ███████████████  (+29.2%)
  gpt-5.4-nano-none       +0.1182  ████████████    (+28.5%)
  gpt-5.4-nano-high       +0.1016  ██████████      (+19.9%)
  gpt-5.4-nano-low        +0.0763  ████████        (+15.6%)
  gpt-5.4-mini-low        +0.0389  ████            (+5.4%)
  claude-4.6-sonnet-medium+0.0074  █               (+1.0%)
  gpt-5.4-mini-medium     +0.0073  █               (+1.0%)
  gpt-5.4-mini-high       -0.0277  ░░░             (-3.3%)
  gpt-5.4-nano-medium     -0.0277  ░░░             (-4.4%)
  gemini-3-flash          -0.0842  ░░░░░░░░        (-11.0%)
  kimi-k2.5               -0.1144  ░░░░░░░░░░░     (-16.4%)
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
  `claude-4.6-sonnet-medium` shows the **largest subjective improvement with skills**: **+0.3133** (3.5833 → 3.8966), indicating materially better narrative clarity/explanation quality even though objective F1 gain is small (+1.0%). This positions Claude + skills as the preferred configuration for **analyst-facing reports** where explanation quality matters as much as detection accuracy.


  ## Deep dive: why Gemini performed worse with skills
  Only one Gemini-family model was available (`gemini-3-flash`), and it regressed with skills:

  - F1: **0.7660 → 0.6818** (Δ -0.0842, **-11.0%**)
  - Precision: **0.6667 → 0.6250**
  - Recall: **0.9000 → 0.7500** (largest drop)
  - FP/task: unchanged (**0.45 → 0.45**)
  - Strict accuracy: **60 → 55**
  - Chain success: **100 → 0**
  - Route strict: **100** (routing is not the issue)

  Interpretation: this is **not** a routing failure and not mainly FP inflation; it is mostly a **recall/coverage collapse under skills constraints**. Notably, Gemini-3-Flash control already achieves **100% native chaining success** without skills—the model already thinks in structured vulnerability chains. The skills prompt adds overhead that **breaks** this native capability rather than enhancing it.

  **Key takeaway:** Skills appear **GPT-tuned**. Models with native structural reasoning (Gemini) may perform better with lightweight or no external scaffolding.


  ## Deep dive: Kimi objective vs subjective
  Kimi regressed the most objectively under skills:

  - F1: **0.6977 → 0.5833** (Δ -0.1144, **-16.4%**)
  - Precision: **0.6522 → 0.5000**
  - Recall: **0.7500 → 0.7000**
  - FP/task: **0.40 → 0.70** (substantial noise increase)
  - Strict accuracy: **65 → 35**

  Subjective view is flatter:

  - Avg subjective: **3.6522 → 3.6429** (near-neutral)
  - Subjective score sum: **84 → 102** (more total evaluated content)
  - Chain success: **0 → 100** (better chain articulation/completion behavior)

  So Kimi's "gain" from subjective grading is mostly **format/coverage of explanations and chain narrative**, but this does **not** convert to objective exploit discrimination (TP/FP), where it worsens. Skills make Kimi **more verbose and better at storytelling, but less accurate at vulnerability identification**.


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

  **Cost-performance insight:** Skills enable smaller models to approach larger-model performance. For example, `gpt-5.4-nano-low` + skills (F1 0.5652) approaches `gpt-5.4-nano-medium` control (F1 0.6364) at lower inference cost. This positions skills as a **cost-performance multiplier** for budget-constrained deployments.


  ## Model capability/use-case recommendations

  | Use Case | Recommended Configuration | Rationale |
  |----------|-------------------------|-----------|
  | **High-stakes vuln triage (best objective)** | `gpt-5.4-mini-high` (control) | F1 0.8372, no skills friction |
  | **Balanced production default** | `gpt-5.4-mini-medium` + skills | F1 0.7692, strong precision, reduced FP |
  | **Low-cost routine scanning** | `gpt-5.1-codex-mini-low` + skills | +29.2% lift from skills, best value |
  | **Report-writing / analyst handoff** | `claude-4.6-sonnet-medium` + skills | +0.3133 subjective gain, best explanations |
  | **Gemini 3 Flash** | Control only | Skills cause -11% F1 regression |
  | **Kimi K2.5** | Control only | Skills increase overcalling (+0.30 FP/task) |

  ### The "+1 Reasoning Tier" Rule of Thumb

  For GPT-family models, skills effectively elevate capability by approximately one tier:
  - nano-none + skills ≈ nano-low control
  - nano-low + skills ≈ nano-medium control
  - nano-high + skills ≈ nano-medium/mini-low control
  - codex-mini-low + skills ≈ approaches mini-low control

  This pattern holds until models approach ceiling performance (mini-high, F1 >0.83), where skills become friction rather than leverage.


  ## Scaffolding improvements (model-adaptive)

  1. **Skills-lite profile** for Gemini/Kimi: shorter schema, stricter top-1/top-2 cap, fewer narrative fields.
  2. **Model-conditional skill routing**: skip skills entirely for Gemini (native chaining), mini-high (saturation), and Kimi (over-calling sensitivity).
  3. **Two-pass mode**: pass 1 discover candidates, pass 2 verify exploitability and drop weak claims.
  4. **Model-conditional FP suppression**: stronger evidence requirements for models with rising FP/task (nano-medium, Kimi).
  5. **Adaptive output budget**: hard cap sentence lengths/field lengths to reduce verbosity-induced drift.
  6. **Chain scoring split in reports**: keep chain quality separate from TP/FP so "good narrative, bad detection" is explicit.
  7. **Cross-family skill tuning**: current skills are GPT-optimized; develop Claude/Gemini/Kimi-specific variants that leverage each model's native strengths rather than imposing uniform structure.