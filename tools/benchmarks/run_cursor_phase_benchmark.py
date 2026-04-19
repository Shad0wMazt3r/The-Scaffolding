#!/usr/bin/env python3
"""Run a low-cost Cursor auto-mode routing benchmark (<=15 tasks)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")
DEFAULT_MODEL = "composer-2"

ALLOWED_PHASES = [
    "recon",
    "web",
    "network",
    "mobile",
    "pwn",
    "crypto",
    "reverse-engineering",
    "forensics",
]


def read_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_json_block(text: str) -> dict | None:
    match = JSON_BLOCK_RE.search(text.strip())
    if not match:
        return None
    candidate = match.group(0).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Fallback for loosely formatted or partially escaped JSON-like output.
        phase_match = re.search(r'"phase"\s*:\s*"([^"]+)"', candidate)
        file_match = re.search(r'"first_file"\s*:\s*"([^"]+)"', candidate)
        if not phase_match and not file_match:
            return None
        return {
            "phase": phase_match.group(1) if phase_match else "",
            "first_file": file_match.group(1) if file_match else "",
        }


def first_file_matches(predicted: str, expected: str) -> bool:
    if not predicted:
        return False
    normalized = predicted.replace("\\", "/")
    basename = Path(normalized).name
    # Accept phase manifest as valid phase entrypoint.
    if basename.lower() == "skill.md":
        return True
    if predicted == expected:
        return True
    if normalized.endswith("/" + expected):
        return True
    if basename == expected:
        return True
    return False


def build_prompt(scenario: str) -> str:
    phases = ", ".join(ALLOWED_PHASES)
    return (
        "You are a benchmark router. "
        f"Choose exactly one phase from [{phases}] and the first file to load for that phase. "
        'Return only minified JSON: {"phase":"...","first_file":"..."} with no extra text. '
        f"Scenario: {scenario}"
    )


def run_one(
    agent_cmd: str,
    prompt: str,
    timeout_sec: int,
    model: str | None,
    approve_mcps: bool,
) -> tuple[str, str, int, float, str]:
    cmd = [agent_cmd, "-p", "--output-format", "text", "--trust", "--force", "--mode", "ask"]
    if approve_mcps:
        cmd.append("--approve-mcps")
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)

    start = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, check=False)
        elapsed = time.perf_counter() - start
        return proc.stdout, proc.stderr, proc.returncode, elapsed, ""
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return "", "", -1, elapsed, "timeout"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    parser.add_argument(
        "--tasks",
        default="tools/benchmarks/cursor_phase_tasks.json",
        help="Task file path",
    )
    parser.add_argument(
        "--output",
        default="reports/benchmarks/cursor-auto-phase-benchmark.json",
        help="Benchmark output report path",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=10,
        help="Maximum tasks to run (hard limit 15)",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=15,
        help="Timeout per task in seconds",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Cursor model override (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--approve-mcps",
        action="store_true",
        help="Pass --approve-mcps to agent",
    )
    parser.add_argument(
        "--agent-cmd",
        default=str(Path.home() / "AppData" / "Local" / "cursor-agent" / "agent.cmd"),
        help="Path to Cursor agent command",
    )
    args = parser.parse_args()

    if args.max_tasks > 15:
        raise SystemExit("--max-tasks cannot exceed 15")

    root = Path(args.repo_root).resolve()
    task_path = Path(args.tasks)
    if not task_path.is_absolute():
        task_path = root / task_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path

    all_tasks = read_json(task_path)
    tasks = all_tasks[: args.max_tasks]

    results: list[dict] = []
    for task in tasks:
        prompt = build_prompt(task["scenario"])
        stdout, stderr, returncode, elapsed, error = run_one(
            agent_cmd=args.agent_cmd,
            prompt=prompt,
            timeout_sec=args.timeout_sec,
            model=args.model or None,
            approve_mcps=args.approve_mcps,
        )

        parsed = extract_json_block(stdout) if not error else None
        predicted_phase = parsed.get("phase") if isinstance(parsed, dict) else ""
        predicted_first = parsed.get("first_file") if isinstance(parsed, dict) else ""
        phase_match = predicted_phase == task["expected_phase"]
        first_match = first_file_matches(predicted_first, task["expected_first_file"])
        task_pass = phase_match and first_match and not error and returncode == 0

        results.append(
            {
                "id": task["id"],
                "expected_phase": task["expected_phase"],
                "expected_first_file": task["expected_first_file"],
                "predicted_phase": predicted_phase,
                "predicted_first_file": predicted_first,
                "phase_match": phase_match,
                "first_file_match": first_match,
                "pass": task_pass,
                "returncode": returncode,
                "elapsed_sec": round(elapsed, 3),
                "error": error,
                "stdout_preview": (stdout[:300] if stdout else ""),
                "stderr_preview": (stderr[:300] if stderr else ""),
            }
        )

    attempted = len(results)
    completed = len([r for r in results if r["error"] == ""])
    timeouts = len([r for r in results if r["error"] == "timeout"])
    phase_correct = len([r for r in results if r["phase_match"]])
    phase_correct_completed = len([r for r in results if r["error"] == "" and r["phase_match"]])
    strict_pass = len([r for r in results if r["pass"]])
    avg_latency = round(sum(r["elapsed_sec"] for r in results) / attempted, 3) if attempted else 0.0

    report = {
        "config": {
            "tasks_file": str(task_path),
            "max_tasks": args.max_tasks,
            "timeout_sec": args.timeout_sec,
            "model": args.model,
            "auto_mode_flags": {
                "print": True,
                "trust": True,
                "force": True,
                "mode": "ask",
                "approve_mcps": bool(args.approve_mcps),
            },
            "agent_cmd": args.agent_cmd,
        },
        "summary": {
            "attempted": attempted,
            "completed": completed,
            "timeouts": timeouts,
            "phase_accuracy": round((phase_correct / attempted) * 100, 2) if attempted else 0.0,
            "phase_accuracy_completed": round((phase_correct_completed / completed) * 100, 2) if completed else 0.0,
            "strict_accuracy": round((strict_pass / attempted) * 100, 2) if attempted else 0.0,
            "avg_latency_sec": avg_latency,
        },
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Wrote benchmark report to {output_path} "
        f"(attempted={attempted}, completed={completed}, timeouts={timeouts}, strict_accuracy={report['summary']['strict_accuracy']}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
