#!/usr/bin/env python3
"""Run lightweight quality gates for skill docs and router consistency."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def pct_delta(new: float, old: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100.0


def extract_shared_block(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    start = "<!-- ROUTER_SHARED_RULES_START -->"
    end = "<!-- ROUTER_SHARED_RULES_END -->"
    if start not in text or end not in text:
        return ""
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    parser.add_argument(
        "--baseline",
        default="reports/skill-baseline.json",
        help="Baseline metrics file",
    )
    parser.add_argument(
        "--gate",
        default=".agents/standards/quality-gate.json",
        help="Quality gate config",
    )
    parser.add_argument(
        "--output",
        default="reports/skill-smoke-eval.json",
        help="Smoke eval output report",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    baseline_path = root / args.baseline
    gate_path = root / args.gate
    output_path = root / args.output
    validation_path = root / "reports" / "skill-validation.json"
    with tempfile.NamedTemporaryFile(suffix="-skill-current.json", delete=False) as tmp:
        current_path = Path(tmp.name)

    gate = read_json(gate_path)
    baseline = read_json(baseline_path)

    py = sys.executable
    baseline_cmd = [py, "tools/skills/baseline_metrics.py", "--output", str(current_path)]
    validate_cmd = [py, "tools/skills/validate_skills.py", "--report", str(validation_path)]

    baseline_run = run(baseline_cmd, root)
    validate_run = run(validate_cmd, root)

    current = read_json(current_path)
    validation = read_json(validation_path)

    baseline_total = baseline["totals"]["approx_tokens"]
    current_total = current["totals"]["approx_tokens"]
    baseline_largest = baseline["largest_files_top10"][0]["approx_tokens"]
    current_largest = current["largest_files_top10"][0]["approx_tokens"]

    total_delta = pct_delta(current_total, baseline_total)
    largest_delta = pct_delta(current_largest, baseline_largest)

    formatting_count = len(current["quality_findings"]["formatting_artifact_files"])
    unresolved_footnotes = len(current["quality_findings"]["unresolved_footnote_files"])
    validation_errors = validation["summary"]["errors"]

    router_paths = [
        root / ".cursor" / "skills" / "bug-hunt-framework" / "SKILL.md",
        root / ".github" / "agents" / "bug-hunt-framework.agent.md",
        root / ".opencode" / "agents" / "bug-hunt-framework.md",
    ]
    shared_blocks = [extract_shared_block(p) for p in router_paths]
    unique_blocks = {b for b in shared_blocks if b}
    router_drift = max(0, len(unique_blocks) - 1)

    checks = gate["checks"]
    regress = gate["regression_limits"]

    failed_checks: list[str] = []
    if validation_errors != checks["validation_errors_must_equal"]:
        failed_checks.append("validation_errors")
    if unresolved_footnotes > checks["max_unresolved_footnote_files"]:
        failed_checks.append("unresolved_footnotes")
    if formatting_count > checks["max_formatting_artifact_files"]:
        failed_checks.append("formatting_artifacts")
    if router_drift > checks["max_router_instruction_drift"]:
        failed_checks.append("router_instruction_drift")
    if total_delta > regress["total_approx_tokens_delta_max_percent"]:
        failed_checks.append("total_token_delta")
    if largest_delta > regress["largest_file_tokens_delta_max_percent"]:
        failed_checks.append("largest_file_token_delta")

    report = {
        "commands": {
            "baseline": {
                "cmd": baseline_cmd,
                "returncode": baseline_run.returncode,
                "stdout": baseline_run.stdout.strip(),
                "stderr": baseline_run.stderr.strip(),
            },
            "validation": {
                "cmd": validate_cmd,
                "returncode": validate_run.returncode,
                "stdout": validate_run.stdout.strip(),
                "stderr": validate_run.stderr.strip(),
            },
        },
        "metrics": {
            "validation_errors": validation_errors,
            "unresolved_footnote_files": unresolved_footnotes,
            "formatting_artifact_files": formatting_count,
            "router_instruction_drift": router_drift,
            "total_approx_tokens_delta_percent": round(total_delta, 3),
            "largest_file_tokens_delta_percent": round(largest_delta, 3),
        },
        "failed_checks": failed_checks,
        "pass": len(failed_checks) == 0,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        current_path.unlink(missing_ok=True)
    except OSError:
        pass
    print(f"Smoke eval pass={report['pass']} failed={len(failed_checks)} report={output_path}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
