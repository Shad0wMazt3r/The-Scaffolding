#!/usr/bin/env python3
"""Produce objective + subjective grading views from vuln benchmark run outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_cwe(value: str) -> str:
    digits = re.findall(r"\d+", value or "")
    return digits[0] if digits else ""


def line_overlap(a1: int, a2: int, b1: int, b2: int) -> bool:
    lo1, hi1 = min(a1, a2), max(a1, a2)
    lo2, hi2 = min(b1, b2), max(b1, b2)
    return max(lo1, lo2) <= min(hi1, hi2)


def classify_finding(finding: dict, expected: list[dict]) -> str:
    cwe = normalize_cwe(str(finding.get("cwe", "")))
    file = str(finding.get("file", ""))
    ls = int(finding.get("line_start", -1))
    le = int(finding.get("line_end", -1))

    for exp in expected:
        if normalize_cwe(str(exp.get("cwe", ""))) != cwe:
            continue
        if str(exp.get("file", "")) != file:
            continue
        if line_overlap(ls, le, int(exp.get("line_start", -1)), int(exp.get("line_end", -1))):
            return "exact_tp"

    # same file as expected but different CWE/line: plausible secondary finding
    if any(str(exp.get("file", "")) == file for exp in expected):
        return "plausible_extra_same_file"

    # if task expects no findings, classify as potential control-break
    if not expected:
        return "control_flag"

    return "speculative_extra"


def subjective_score(finding: dict) -> tuple[int, list[str]]:
    score = 0
    notes: list[str] = []
    claim = str(finding.get("vuln_claim", ""))
    proof = str(finding.get("proof", ""))
    repro = str(finding.get("repro_steps", ""))
    impact = str(finding.get("impact", ""))
    text = " ".join([claim, proof, repro, impact]).lower()

    if len(claim) >= 30:
        score += 1
    else:
        notes.append("short_claim")
    if len(proof) >= 40:
        score += 1
    else:
        notes.append("weak_proof")
    if len(repro) >= 30:
        score += 1
    else:
        notes.append("weak_repro")
    if any(t in text for t in ["payload", "example", "curl", "request", "response", "$ne", "../", "169.254", "unsigned"]):
        score += 1
    else:
        notes.append("no_concrete_test_signal")
    if any(t in text for t in ["precondition", "requires", "if ", "only when", "reachable", "constraint", "impact"]):
        score += 1
    else:
        notes.append("thin_exploitability_reasoning")

    return score, notes


def load_run_paths(experiment: dict | None, explicit_reports: list[Path]) -> list[Path]:
    if explicit_reports:
        return explicit_reports
    if not experiment:
        return []
    paths: list[Path] = []
    for row in experiment.get("run_records", []):
        p = Path(row.get("report_path", ""))
        if p.exists():
            paths.append(p)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", default="tools/benchmarks/cursor_vuln_tasks.json", help="Task file path")
    parser.add_argument("--experiment", default="", help="Optional experiment report path")
    parser.add_argument("--reports", nargs="*", default=[], help="Optional explicit run report paths")
    parser.add_argument(
        "--output",
        default="reports/benchmarks/cursor-vuln-manual-grade.json",
        help="Output grading report path",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    tasks_path = Path(args.tasks) if Path(args.tasks).is_absolute() else repo_root / args.tasks
    task_rows = read_json(tasks_path)
    tasks_by_id = {t["id"]: t for t in task_rows}

    experiment = None
    if args.experiment:
        exp_path = Path(args.experiment) if Path(args.experiment).is_absolute() else repo_root / args.experiment
        experiment = read_json(exp_path)

    explicit = [Path(p) if Path(p).is_absolute() else repo_root / p for p in args.reports]
    run_paths = load_run_paths(experiment, explicit)
    if not run_paths:
        raise SystemExit("No run reports provided/found.")

    entries = []
    profile_summary: dict[str, dict] = {}
    for run_path in run_paths:
        run = read_json(run_path)
        profile = run.get("config", {}).get("profile", "unknown")
        run_name = run_path.name
        profile_summary.setdefault(
            profile,
            {
                "runs": 0,
                "findings_total": 0,
                "exact_tp": 0,
                "plausible_extra_same_file": 0,
                "speculative_extra": 0,
                "control_flags": 0,
                "subjective_score_sum": 0,
            },
        )
        profile_summary[profile]["runs"] += 1

        for row in run.get("results", []):
            task = tasks_by_id.get(row.get("id"), {})
            expected = task.get("expected_findings", [])
            for finding in row.get("parsed_findings", []):
                klass = classify_finding(finding, expected)
                score, notes = subjective_score(finding)
                entry = {
                    "run": run_name,
                    "profile": profile,
                    "task_id": row.get("id"),
                    "classification": klass,
                    "subjective_score_0_to_5": score,
                    "subjective_flags": notes,
                    "finding": {
                        "cwe": finding.get("cwe", ""),
                        "file": finding.get("file", ""),
                        "line_start": finding.get("line_start", -1),
                        "line_end": finding.get("line_end", -1),
                        "vuln_claim": finding.get("vuln_claim", ""),
                    },
                }
                entries.append(entry)

                ps = profile_summary[profile]
                ps["findings_total"] += 1
                ps["subjective_score_sum"] += score
                if klass in ps:
                    ps[klass] += 1

    for profile, ps in profile_summary.items():
        total = ps["findings_total"] or 1
        ps["exact_tp_rate"] = round(ps["exact_tp"] / total, 4)
        ps["speculative_extra_rate"] = round(ps["speculative_extra"] / total, 4)
        ps["control_flag_rate"] = round(ps["control_flags"] / total, 4)
        ps["avg_subjective_score"] = round(ps["subjective_score_sum"] / total, 4)

    output = {
        "config": {
            "tasks": str(tasks_path),
            "run_reports": [str(p) for p in run_paths],
        },
        "profile_summary": profile_summary,
        "graded_findings": entries,
        "manual_review_guidance": {
            "focus_first": [
                "speculative_extra",
                "control_flag",
                "plausible_extra_same_file",
            ],
            "use_subjective_flags_to_prioritize": True,
        },
    }

    output_path = Path(args.output) if Path(args.output).is_absolute() else repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote manual grading report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
