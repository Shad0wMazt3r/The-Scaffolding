#!/usr/bin/env python3
"""Compare two vulnerability benchmark reports and emit deltas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

METRICS = [
    "precision",
    "recall",
    "f1",
    "tp_per_task",
    "fp_per_task",
    "chain_success_rate",
    "strict_task_accuracy",
    "avg_latency_sec",
    "time_per_valid_tp_sec",
    "avg_estimated_tokens",
]

LOWER_IS_BETTER = {"fp_per_task", "avg_latency_sec", "time_per_valid_tp_sec", "avg_estimated_tokens"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def direction(metric: str, delta: float) -> str:
    if metric in LOWER_IS_BETTER:
        if delta < 0:
            return "better"
        if delta > 0:
            return "worse"
        return "equal"
    if delta > 0:
        return "better"
    if delta < 0:
        return "worse"
    return "equal"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="Baseline benchmark JSON path")
    parser.add_argument("--candidate", required=True, help="Candidate benchmark JSON path")
    parser.add_argument(
        "--output",
        default="reports/benchmarks/cursor-vuln-comparison.json",
        help="Output comparison report path",
    )
    args = parser.parse_args()

    baseline = read_json(Path(args.baseline))
    candidate = read_json(Path(args.candidate))
    bsum = baseline.get("summary", {})
    csum = candidate.get("summary", {})

    deltas = {}
    for metric in METRICS:
        if metric not in bsum or metric not in csum:
            continue
        b = bsum[metric]
        c = csum[metric]
        if b is None or c is None:
            continue
        b_f = float(b)
        c_f = float(c)
        d = round(c_f - b_f, 4)
        deltas[metric] = {
            "baseline": b_f,
            "candidate": c_f,
            "delta": d,
            "direction": direction(metric, d),
        }

    report = {
        "baseline": {
            "path": str(Path(args.baseline)),
            "profile": baseline.get("config", {}).get("profile", "unknown"),
            "attempted": bsum.get("attempted", 0),
            "timeouts": bsum.get("timeouts", 0),
        },
        "candidate": {
            "path": str(Path(args.candidate)),
            "profile": candidate.get("config", {}).get("profile", "unknown"),
            "attempted": csum.get("attempted", 0),
            "timeouts": csum.get("timeouts", 0),
        },
        "metric_deltas": deltas,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote vuln benchmark comparison to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
