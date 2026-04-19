#!/usr/bin/env python3
"""Generate consolidated leaderboard artifacts from model-sweep runs3 reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_mean(agg: dict, metric: str) -> float | None:
    return agg.get("metric_stats", {}).get(metric, {}).get("mean")


def fmt(v: float | None, places: int = 4) -> str:
    if v is None:
        return "n/a"
    return f"{v:.{places}f}"


def build_rows(root: Path) -> list[dict]:
    rows: list[dict] = []
    for model_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        exp_path = model_dir / "experiment-runs3.json"
        grade_path = model_dir / "manual-grade-runs3.json"
        if not exp_path.exists() or not grade_path.exists():
            continue

        exp = read_json(exp_path)
        grade = read_json(grade_path)
        aggregates = exp.get("aggregates", {})
        control = aggregates.get("control", {})
        skills = aggregates.get("skills-only", {})

        c_f1 = safe_mean(control, "f1")
        s_f1 = safe_mean(skills, "f1")
        c_fp = safe_mean(control, "fp_per_task")
        s_fp = safe_mean(skills, "fp_per_task")
        c_strict = safe_mean(control, "strict_task_accuracy")
        s_strict = safe_mean(skills, "strict_task_accuracy")
        c_empty = safe_mean(control, "empty_output_task_rate")
        s_empty = safe_mean(skills, "empty_output_task_rate")
        c_chain = safe_mean(control, "chain_success_rate")
        s_chain = safe_mean(skills, "chain_success_rate")
        c_subj = grade.get("profile_summary", {}).get("control", {}).get("avg_subjective_score")
        s_subj = grade.get("profile_summary", {}).get("skills-only", {}).get("avg_subjective_score")

        rows.append(
            {
                "model": model_dir.name,
                "control_f1": c_f1,
                "skills_f1": s_f1,
                "delta_f1": (s_f1 - c_f1) if c_f1 is not None and s_f1 is not None else None,
                "control_fp_per_task": c_fp,
                "skills_fp_per_task": s_fp,
                "delta_fp_per_task": (s_fp - c_fp) if c_fp is not None and s_fp is not None else None,
                "control_strict": c_strict,
                "skills_strict": s_strict,
                "delta_strict": (s_strict - c_strict) if c_strict is not None and s_strict is not None else None,
                "control_empty_rate": c_empty,
                "skills_empty_rate": s_empty,
                "delta_empty_rate": (s_empty - c_empty) if c_empty is not None and s_empty is not None else None,
                "control_chain_success": c_chain,
                "skills_chain_success": s_chain,
                "delta_chain_success": (s_chain - c_chain) if c_chain is not None and s_chain is not None else None,
                "control_subjective": c_subj,
                "skills_subjective": s_subj,
                "delta_subjective": (s_subj - c_subj) if c_subj is not None and s_subj is not None else None,
            }
        )
    return rows


def to_markdown(rows: list[dict]) -> str:
    lines = [
        "# Vulnerability Benchmark Leaderboard (runs3)",
        "",
        "| Model | Control F1 | Skills F1 | ΔF1 | ΔFP/task | ΔStrict | ΔChain Success | ΔSubjective |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda x: (x["delta_f1"] is None, -(x["delta_f1"] or -9999))):
        lines.append(
            "| {model} | {c_f1} | {s_f1} | {d_f1} | {d_fp} | {d_strict} | {d_chain} | {d_subj} |".format(
                model=row["model"],
                c_f1=fmt(row["control_f1"]),
                s_f1=fmt(row["skills_f1"]),
                d_f1=fmt(row["delta_f1"]),
                d_fp=fmt(row["delta_fp_per_task"]),
                d_strict=fmt(row["delta_strict"], places=2),
                d_chain=fmt(row["delta_chain_success"], places=2),
                d_subj=fmt(row["delta_subjective"], places=4),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        default="reports/benchmarks/model-sweep",
        help="Directory containing per-model run outputs",
    )
    parser.add_argument(
        "--output-json",
        default="reports/benchmarks/model-sweep-leaderboard.json",
        help="Path to write machine-readable leaderboard",
    )
    parser.add_argument(
        "--output-md",
        default="reports/benchmarks/model-sweep-leaderboard.md",
        help="Path to write markdown leaderboard",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    input_root = Path(args.input_root) if Path(args.input_root).is_absolute() else repo_root / args.input_root
    output_json = Path(args.output_json) if Path(args.output_json).is_absolute() else repo_root / args.output_json
    output_md = Path(args.output_md) if Path(args.output_md).is_absolute() else repo_root / args.output_md

    rows = build_rows(input_root)
    payload = {"rows": rows, "models": len(rows)}
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(to_markdown(rows), encoding="utf-8")

    print(f"Wrote leaderboard JSON to {output_json}")
    print(f"Wrote leaderboard markdown to {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

