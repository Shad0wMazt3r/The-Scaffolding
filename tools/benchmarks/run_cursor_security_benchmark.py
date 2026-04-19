#!/usr/bin/env python3
"""Run low-cost Cursor security benchmark (skills-only now, MCP profile later)."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import time
from pathlib import Path

JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")
PHASES = [
    "recon",
    "web",
    "network",
    "mobile",
    "pwn",
    "crypto",
    "reverse-engineering",
    "forensics",
]

FIRST_FILE_BY_PHASE = {
    "recon": "01-setup-and-contract.md",
    "web": "01-prerequisites-and-environment.md",
    "network": "01-environment.md",
    "mobile": "01-baseline-and-setup.md",
    "pwn": "01-environment-baseline.md",
    "crypto": "01-workspace-baseline.md",
    "reverse-engineering": "01-baseline-and-initial-triage.md",
    "forensics": "01-environment-and-tooling.md",
}

WEB_DEEP_FILES = [
    "12-source-review-deep-architecture-and-trust.md",
    "13-source-review-deep-chain-playbooks.md",
    "14-source-review-deep-exploitability-and-interactions.md",
    "15-source-review-deep-severity-and-reporting.md",
]


def read_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_json(text: str) -> dict | None:
    match = JSON_BLOCK_RE.search(text.strip())
    if not match:
        return None
    candidate = match.group(0).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        fields = {}
        for key in ["phase", "first_file", "deep_file", "primary_probe", "dead_end", "data_chaining"]:
            m = re.search(rf'"{key}"\s*:\s*"([^"]*)"', candidate)
            fields[key] = m.group(1) if m else ""
        if not fields["phase"]:
            return None
        return fields


def file_match(predicted: str, expected: str) -> bool:
    if not expected:
        return True
    if not predicted:
        return False
    norm = predicted.replace("\\", "/")
    base = Path(norm).name
    if base.lower() == "skill.md":
        return True
    if predicted == expected:
        return True
    if norm.endswith("/" + expected):
        return True
    if base == expected:
        return True
    return False


def deep_file_match(predicted: str, expected: str) -> bool:
    if not expected:
        # no deep file expected; allow empty or explicit none-like values
        return predicted.strip().lower() in {"", "none", "n/a", "null"}
    return file_match(predicted, expected)


def hit_count(text: str, terms: list[str]) -> int:
    lower = text.lower()
    return sum(1 for t in terms if t.lower() in lower)


def build_prompt(task: dict, skills_only: bool) -> str:
    phases = ", ".join(PHASES)
    mode_hint = (
        "Skills-only mode: do not rely on MCP servers or external scanners."
        if skills_only
        else "MCP-enabled mode: you may reference MCP-assisted pivots if useful."
    )
    return (
        f"{mode_hint} "
        "Given the scenario, choose one phase and propose a compact security playbook. "
        f"Phase must be one of [{phases}]. "
        "Use these exact first-file mappings by phase: "
        + ", ".join(f"{k}=>{v}" for k, v in FIRST_FILE_BY_PHASE.items())
        + ". "
        "For deep_file: use empty string unless the scenario includes web source-review intent. "
        "Web source-review intent means the scenario mentions any of: source review, architecture, trust boundary, chain, exploitability, severity, or reporting. "
        f"When web source-review intent is present, deep_file is required and must be exactly one of [{', '.join(WEB_DEEP_FILES)}]. "
        "Map by intent: architecture/trust boundaries=>12-source-review-deep-architecture-and-trust.md, "
        "multi-step chains/pivot chains=>13-source-review-deep-chain-playbooks.md, exploitability/proof interactions=>14-source-review-deep-exploitability-and-interactions.md, "
        "severity/risk/reporting=>15-source-review-deep-severity-and-reporting.md. "
        'Return only minified JSON with keys exactly: '
        '{"phase":"","first_file":"","deep_file":"","primary_probe":"","dead_end":"","data_chaining":""}. '
        "Use one sentence per strategy field and keep responses concise. "
        f"Scenario: {task['scenario']}"
    )


def run_agent(agent_cmd: str, prompt: str, timeout_sec: int, model: str, approve_mcps: bool) -> tuple[str, str, int, float, str]:
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
        default="tools/benchmarks/cursor_security_tasks.json",
        help="Task file path",
    )
    parser.add_argument(
        "--output",
        default="reports/benchmarks/cursor-security-skills-only.json",
        help="Output report path",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=12,
        help="Maximum tasks to run (hard limit 15)",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=20,
        help="Timeout per task in seconds",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Optional model override (empty = default)",
    )
    parser.add_argument(
        "--profile",
        choices=["skills-only", "mcp-enabled"],
        default="skills-only",
        help="Benchmark profile",
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

    tasks = read_json(task_path)[: args.max_tasks]
    skills_only = args.profile == "skills-only"
    approve_mcps = args.profile == "mcp-enabled"

    results: list[dict] = []
    for task in tasks:
        prompt = build_prompt(task, skills_only=skills_only)
        stdout, stderr, returncode, elapsed, error = run_agent(
            agent_cmd=args.agent_cmd,
            prompt=prompt,
            timeout_sec=args.timeout_sec,
            model=args.model,
            approve_mcps=approve_mcps,
        )

        parsed = extract_json(stdout) if not error else None
        phase = parsed.get("phase", "") if isinstance(parsed, dict) else ""
        first_file = parsed.get("first_file", "") if isinstance(parsed, dict) else ""
        deep_file = parsed.get("deep_file", "") if isinstance(parsed, dict) else ""
        primary_probe = parsed.get("primary_probe", "") if isinstance(parsed, dict) else ""
        dead_end = parsed.get("dead_end", "") if isinstance(parsed, dict) else ""
        data_chaining = parsed.get("data_chaining", "") if isinstance(parsed, dict) else ""

        phase_ok = phase == task["expected_phase"]
        first_ok = file_match(first_file, task["expected_first_file"])
        deep_ok = deep_file_match(deep_file, task.get("expected_deep_file", ""))
        fields_ok = min(len(primary_probe), len(dead_end), len(data_chaining)) >= 20
        combined = f"{primary_probe}\n{dead_end}\n{data_chaining}"
        required_terms = task.get("required_terms", [])
        hits = hit_count(combined, required_terms)
        term_ratio = (hits / len(required_terms)) if required_terms else 1.0
        terms_ok = term_ratio >= 0.5

        strict_pass = (
            not error
            and returncode == 0
            and phase_ok
            and first_ok
            and deep_ok
            and fields_ok
            and terms_ok
        )

        # 0..1 per-task signal score
        signal = (0.35 if phase_ok else 0.0) + (0.2 if first_ok else 0.0) + (0.15 if deep_ok else 0.0)
        signal += (0.15 if fields_ok else 0.0) + (0.15 * min(1.0, term_ratio))

        results.append(
            {
                "id": task["id"],
                "expected_phase": task["expected_phase"],
                "expected_first_file": task["expected_first_file"],
                "expected_deep_file": task.get("expected_deep_file", ""),
                "predicted_phase": phase,
                "predicted_first_file": first_file,
                "predicted_deep_file": deep_file,
                "phase_match": phase_ok,
                "first_file_match": first_ok,
                "deep_file_match": deep_ok,
                "structured_fields_ok": fields_ok,
                "required_terms_hit_count": hits,
                "required_terms_total": len(required_terms),
                "required_terms_hit_ratio": round(term_ratio, 3),
                "security_signal_score": round(signal, 3),
                "strict_pass": strict_pass,
                "returncode": returncode,
                "elapsed_sec": round(elapsed, 3),
                "error": error,
                "stdout_preview": stdout[:300] if stdout else "",
                "stderr_preview": stderr[:300] if stderr else "",
            }
        )

    attempted = len(results)
    completed = len([r for r in results if r["error"] == ""])
    timeouts = len([r for r in results if r["error"] == "timeout"])
    phase_correct = len([r for r in results if r["phase_match"]])
    first_correct = len([r for r in results if r["first_file_match"]])
    deep_expected = [r for r in results if r["expected_deep_file"]]
    deep_correct = len([r for r in deep_expected if r["deep_file_match"]]) if deep_expected else 0
    structured_ok = len([r for r in results if r["structured_fields_ok"]])
    strict_ok = len([r for r in results if r["strict_pass"]])
    avg_latency = round(sum(r["elapsed_sec"] for r in results) / attempted, 3) if attempted else 0.0
    avg_signal = round(sum(r["security_signal_score"] for r in results) / attempted, 3) if attempted else 0.0
    avg_term_ratio = (
        round(sum(r["required_terms_hit_ratio"] for r in results) / attempted, 3) if attempted else 0.0
    )

    report = {
        "config": {
            "profile": args.profile,
            "tasks_file": str(task_path),
            "max_tasks": args.max_tasks,
            "timeout_sec": args.timeout_sec,
            "model": args.model or "default",
            "agent_cmd": args.agent_cmd,
            "auto_mode_flags": {
                "print": True,
                "trust": True,
                "force": True,
                "mode": "ask",
                "approve_mcps": approve_mcps,
            },
        },
        "summary": {
            "attempted": attempted,
            "completed": completed,
            "timeouts": timeouts,
            "phase_accuracy": round((phase_correct / attempted) * 100, 2) if attempted else 0.0,
            "first_file_accuracy": round((first_correct / attempted) * 100, 2) if attempted else 0.0,
            "deep_file_accuracy": round((deep_correct / len(deep_expected)) * 100, 2) if deep_expected else 0.0,
            "structured_fields_rate": round((structured_ok / attempted) * 100, 2) if attempted else 0.0,
            "strict_accuracy": round((strict_ok / attempted) * 100, 2) if attempted else 0.0,
            "required_term_hit_rate": round(avg_term_ratio * 100, 2),
            "avg_security_signal_score": avg_signal,
            "avg_latency_sec": avg_latency,
        },
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Wrote security benchmark report to {output_path} "
        f"(attempted={attempted}, completed={completed}, strict_accuracy={report['summary']['strict_accuracy']}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
