#!/usr/bin/env python3
"""Run multi-run vuln-finding experiment and aggregate control vs skills results."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

DEFAULT_MODEL = "composer-2"
DEFAULT_PROFILES = ["control", "skills-only"]
AGG_METRICS = [
    "precision",
    "recall",
    "f1",
    "tp_per_task",
    "fp_per_task",
    "strict_task_accuracy",
    "cwe_recall",
    "file_recall",
    "line_recall",
    "evidence_recall",
    "overreport_rate",
    "empty_output_task_rate",
    "skill_anchor_presence_rate",
    "skill_route_phase_accuracy",
    "skill_route_first_file_accuracy",
    "skill_route_strict_accuracy",
    "chain_coverage_rate",
    "chain_linked_rate",
    "chain_success_rate",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mean_std(values: list[float]) -> dict:
    if not values:
        return {"mean": None, "stddev": None, "min": None, "max": None}
    if len(values) == 1:
        v = float(values[0])
        return {"mean": v, "stddev": 0.0, "min": v, "max": v}
    return {
        "mean": round(float(statistics.mean(values)), 4),
        "stddev": round(float(statistics.pstdev(values)), 4),
        "min": round(float(min(values)), 4),
        "max": round(float(max(values)), 4),
    }


def run_once(
    repo_root: Path,
    profile: str,
    run_index: int,
    tasks: str,
    max_tasks: int,
    timeout_sec: int,
    model: str,
    agent_cmd: str,
    out_dir: Path,
    store_raw_output: bool,
) -> Path:
    out_path = out_dir / f"cursor-vuln-{profile}-run{run_index}.json"
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "benchmarks" / "run_cursor_vuln_benchmark.py"),
        "--repo-root",
        str(repo_root),
        "--profile",
        profile,
        "--tasks",
        tasks,
        "--max-tasks",
        str(max_tasks),
        "--timeout-sec",
        str(timeout_sec),
        "--model",
        model,
        "--agent-cmd",
        agent_cmd,
        "--output",
        str(out_path),
    ]
    if store_raw_output:
        cmd.append("--store-raw-output")

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Run failed (profile={profile}, run={run_index}, rc={proc.returncode}).\n"
            f"stdout:\n{proc.stdout[-1200:]}\n\nstderr:\n{proc.stderr[-1200:]}"
        )
    return out_path


def aggregate_profile(reports: list[dict]) -> dict:
    if not reports:
        return {}

    summaries = [r.get("summary", {}) for r in reports]
    total_attempted = sum(int(s.get("attempted", 0)) for s in summaries)
    total_completed = sum(int(s.get("completed", 0)) for s in summaries)
    total_timeouts = sum(int(s.get("timeouts", 0)) for s in summaries)
    total_expected = sum(int(s.get("expected_findings_total", 0)) for s in summaries)
    total_predicted = sum(int(s.get("predicted_findings_total", 0)) for s in summaries)
    total_tp = sum(int(s.get("valid_tp_total", 0)) for s in summaries)
    total_fp = sum(int(s.get("fp_total", 0)) for s in summaries)
    total_fn = sum(int(s.get("fn_total", 0)) for s in summaries)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    metric_stats = {}
    for metric in AGG_METRICS:
        vals = [s.get(metric) for s in summaries if s.get(metric) is not None]
        metric_stats[metric] = mean_std([float(v) for v in vals]) if vals else mean_std([])

    return {
        "runs": len(reports),
        "totals": {
            "attempted": total_attempted,
            "completed": total_completed,
            "timeouts": total_timeouts,
            "expected_findings_total": total_expected,
            "predicted_findings_total": total_predicted,
            "valid_tp_total": total_tp,
            "fp_total": total_fp,
            "fn_total": total_fn,
            "precision_from_totals": round(precision, 4),
            "recall_from_totals": round(recall, 4),
            "f1_from_totals": round(f1, 4),
        },
        "metric_stats": metric_stats,
    }


def profile_delta(control_agg: dict, skills_agg: dict) -> dict:
    deltas = {}
    control_metrics = control_agg.get("metric_stats", {})
    skills_metrics = skills_agg.get("metric_stats", {})
    for metric in AGG_METRICS:
        cm = control_metrics.get(metric, {}).get("mean")
        sm = skills_metrics.get(metric, {}).get("mean")
        if cm is None or sm is None:
            continue
        deltas[metric] = round(float(sm) - float(cm), 4)
    return deltas


def collect_task_stability(reports: list[dict]) -> dict:
    task_rows: dict[str, list[dict]] = {}
    for report in reports:
        for row in report.get("results", []):
            task_rows.setdefault(row["id"], []).append(row)

    out = {}
    for task_id, rows in sorted(task_rows.items()):
        strict_values = [bool(r.get("strict_pass", False)) for r in rows]
        out[task_id] = {
            "runs": len(rows),
            "strict_pass_rate": round(sum(1 for v in strict_values if v) / len(strict_values), 4),
            "tp_mean": round(statistics.mean(float(r.get("valid_tp", 0)) for r in rows), 4),
            "fp_mean": round(statistics.mean(float(r.get("fp_count", 0)) for r in rows), 4),
            "fn_mean": round(statistics.mean(float(r.get("fn_count", 0)) for r in rows), 4),
        }
    return out


def collect_route_failures(reports: list[dict]) -> list[dict]:
    failures: list[dict] = []
    for report in reports:
        profile = report.get("config", {}).get("profile", "unknown")
        for row in report.get("results", []):
            if row.get("route_required") and not row.get("route_strict_ok"):
                failures.append(
                    {
                        "profile": profile,
                        "task_id": row.get("id"),
                        "expected_phase": row.get("expected_phase", ""),
                        "predicted_phase": row.get("predicted_phase", ""),
                        "expected_first_file": row.get("expected_first_file", ""),
                        "predicted_first_file": row.get("predicted_first_file", ""),
                    }
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]), help="Repository root path")
    parser.add_argument("--tasks", default="tools/benchmarks/cursor_vuln_tasks.json", help="Task file path")
    parser.add_argument("--profiles", nargs="+", default=DEFAULT_PROFILES, help="Profiles to run")
    parser.add_argument("--runs", type=int, default=2, help="Runs per profile")
    parser.add_argument("--max-tasks", type=int, default=20, help="Maximum tasks per run (hard limit 20)")
    parser.add_argument("--timeout-sec", type=int, default=120, help="Timeout per task in seconds")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    parser.add_argument(
        "--agent-cmd",
        default=str(Path.home() / "AppData" / "Local" / "cursor-agent" / "agent.cmd"),
        help="Path to Cursor agent command",
    )
    parser.add_argument("--out-dir", default="reports/benchmarks/experiment-runs", help="Per-run output directory")
    parser.add_argument(
        "--output",
        default="reports/benchmarks/cursor-vuln-experiment-runs2.json",
        help="Aggregated experiment output report",
    )
    parser.add_argument(
        "--store-raw-output",
        action="store_true",
        help="Store full model outputs in per-run reports for manual grading",
    )
    args = parser.parse_args()

    if args.max_tasks > 20:
        raise SystemExit("--max-tasks cannot exceed 20")
    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")

    repo_root = Path(args.repo_root).resolve()
    tasks = str(Path(args.tasks) if Path(args.tasks).is_absolute() else repo_root / args.tasks)
    out_dir = Path(args.out_dir) if Path(args.out_dir).is_absolute() else repo_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if Path(args.output).is_absolute() else repo_root / args.output

    run_records: list[dict] = []
    reports_by_profile: dict[str, list[dict]] = {p: [] for p in args.profiles}

    for profile in args.profiles:
        for run_index in range(1, args.runs + 1):
            out_path = run_once(
                repo_root=repo_root,
                profile=profile,
                run_index=run_index,
                tasks=tasks,
                max_tasks=args.max_tasks,
                timeout_sec=args.timeout_sec,
                model=args.model,
                agent_cmd=args.agent_cmd,
                out_dir=out_dir,
                store_raw_output=args.store_raw_output,
            )
            report = read_json(out_path)
            reports_by_profile[profile].append(report)
            run_records.append(
                {
                    "profile": profile,
                    "run_index": run_index,
                    "report_path": str(out_path),
                    "summary": report.get("summary", {}),
                }
            )

    aggregates = {profile: aggregate_profile(reports) for profile, reports in reports_by_profile.items()}
    deltas = (
        profile_delta(aggregates.get("control", {}), aggregates.get("skills-only", {}))
        if "control" in aggregates and "skills-only" in aggregates
        else {}
    )

    stability = {
        profile: collect_task_stability(reports)
        for profile, reports in reports_by_profile.items()
    }
    route_failures = collect_route_failures(reports_by_profile.get("skills-only", []))

    output = {
        "config": {
            "repo_root": str(repo_root),
            "tasks": tasks,
            "profiles": args.profiles,
            "runs": args.runs,
            "max_tasks": args.max_tasks,
            "timeout_sec": args.timeout_sec,
            "model": args.model,
            "store_raw_output": bool(args.store_raw_output),
        },
        "run_records": run_records,
        "aggregates": aggregates,
        "control_vs_skills_delta_mean": deltas,
        "task_stability": stability,
        "skills_route_failures": route_failures,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote vuln experiment report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
