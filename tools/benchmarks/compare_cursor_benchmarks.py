#!/usr/bin/env python3
"""Compare two Cursor benchmark reports and emit metric deltas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


METRICS = [
    "phase_accuracy",
    "first_file_accuracy",
    "deep_file_accuracy",
    "structured_fields_rate",
    "strict_accuracy",
    "required_term_hit_rate",
    "avg_security_signal_score",
    "avg_latency_sec",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def direction(metric: str, delta: float) -> str:
    lower_is_better = {"avg_latency_sec"}
    if metric in lower_is_better:
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
    parser.add_argument("--baseline", required=True, help="Baseline benchmark JSON")
    parser.add_argument("--candidate", required=True, help="Candidate benchmark JSON")
    parser.add_argument(
        "--output",
        default="reports/benchmarks/cursor-benchmark-comparison.json",
        help="Output comparison JSON",
    )
    args = parser.parse_args()

    baseline = read_json(Path(args.baseline))
    candidate = read_json(Path(args.candidate))

    bsum = baseline.get("summary", {})
    csum = candidate.get("summary", {})

    deltas = {}
    for metric in METRICS:
        if metric in bsum and metric in csum:
            b = float(bsum[metric])
            c = float(csum[metric])
            d = round(c - b, 3)
            deltas[metric] = {
                "baseline": b,
                "candidate": c,
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
    print(f"Wrote benchmark comparison to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
