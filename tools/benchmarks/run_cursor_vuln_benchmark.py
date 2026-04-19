#!/usr/bin/env python3
"""Run low-cost vulnerability-finding benchmark with ground-truth scoring."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import time
from pathlib import Path

JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")
FENCED_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
DEFAULT_MODEL = "composer-2"
PHASE_TO_FIRST_FILE = {
    "recon": "01-setup-and-contract.md",
    "web": "01-prerequisites-and-environment.md",
    "network": "01-environment.md",
    "mobile": "01-baseline-and-setup.md",
    "pwn": "01-environment-baseline.md",
    "crypto": "01-workspace-baseline.md",
    "reverse-engineering": "01-baseline-and-initial-triage.md",
    "forensics": "01-environment-and-tooling.md",
}


def read_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_candidates(text: str) -> list[str]:
    stripped = text.strip()
    candidates: list[str] = []
    for m in FENCED_BLOCK_RE.finditer(stripped):
        block = m.group(1).strip()
        if block:
            candidates.append(block)
    if stripped:
        candidates.append(stripped)
    return candidates


def extract_json(text: str | None) -> dict | None:
    if not text:
        return None
    decoder = json.JSONDecoder()
    findings_regex = re.compile(r'\{[^{}]*"cwe"[^{}]*\}')

    for candidate in _json_candidates(text):
        # 1) strict JSON parse of whole candidate
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # 2) decode first JSON object inside candidate (handles pre/post text)
        for idx, ch in enumerate(candidate):
            if ch != "{":
                continue
            try:
                parsed, _end = decoder.raw_decode(candidate[idx:])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        # 3) fallback extraction for partially broken JSON-like outputs
        match = JSON_BLOCK_RE.search(candidate)
        if not match:
            continue
        block_text = match.group(0).strip()
        findings = []
        for m in findings_regex.finditer(block_text):
            block = m.group(0)

            def g(key: str) -> str:
                km = re.search(rf'"{key}"\s*:\s*"([^"]*)"', block)
                return km.group(1) if km else ""

            findings.append(
                {
                    "cwe": g("cwe"),
                    "file": g("file"),
                    "line_start": g("line_start"),
                    "line_end": g("line_end"),
                    "vuln_claim": g("vuln_claim"),
                    "proof": g("proof"),
                    "repro_steps": g("repro_steps"),
                    "impact": g("impact"),
                    "confidence": g("confidence"),
                    "chain_steps": g("chain_steps"),
                }
            )
        if findings:
            return {"findings": findings}
    return None


def normalize_cwe(value: str) -> str:
    digits = re.findall(r"\d+", value or "")
    return digits[0] if digits else ""


def to_int(value: object, default: int = -1) -> int:
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return default


def file_match(predicted: str, expected: str) -> bool:
    if not expected:
        return True
    if not predicted:
        return False
    norm = predicted.replace("\\", "/")
    base = Path(norm).name
    return predicted == expected or norm.endswith("/" + expected) or base == expected


def line_match(pred_start: int, pred_end: int, exp_start: int, exp_end: int, tol: int = 2) -> bool:
    if pred_start < 0 and pred_end < 0:
        return False
    if pred_end < 0:
        pred_end = pred_start
    if pred_start < 0:
        pred_start = pred_end
    lo1, hi1 = min(pred_start, pred_end), max(pred_start, pred_end)
    lo2, hi2 = min(exp_start, exp_end) - tol, max(exp_start, exp_end) + tol
    return max(lo1, lo2) <= min(hi1, hi2)


def contains_any(text: str, terms: list[str]) -> bool:
    if not terms:
        return True
    lower = text.lower()
    return any(t.lower() in lower for t in terms)


def build_prompt(task: dict, profile: str) -> str:
    mode_hint = {
        "control": "Control mode: analyze only the provided snippet; do not rely on skill files or MCP tooling.",
        "skills-only": "Skills-only mode: use internal security skill reasoning, but do not rely on MCP tooling.",
        "mcp-enabled": "MCP-enabled mode: skills plus MCP-assisted pivots are allowed.",
    }[profile]
    max_findings = int(task.get("max_findings", 2))
    scenario_inline = re.sub(r"\s+", " ", str(task["scenario"])).strip()
    route_hint = (
        "Include skill routing anchor with exact values. "
        "Use skill_anchor.phase in [recon, web, network, mobile, pwn, crypto, reverse-engineering, forensics] and "
        "skill_anchor.first_file mapped exactly as: "
        + ", ".join(f"{k}=>{v}" for k, v in PHASE_TO_FIRST_FILE.items())
        + ". "
        if profile != "control"
        else ""
    )
    output_shape = (
        '{"skill_anchor":{"phase":"","first_file":""},"findings":[{"cwe":"CWE-...","file":"","line_start":0,"line_end":0,"vuln_claim":"","proof":"","repro_steps":"","impact":"","confidence":0.0,"chain_steps":""}]}'
        if profile != "control"
        else '{"findings":[{"cwe":"CWE-...","file":"","line_start":0,"line_end":0,"vuln_claim":"","proof":"","repro_steps":"","impact":"","confidence":0.0,"chain_steps":""}]}'
    )
    no_findings_hint = (
        'If no valid vulnerability exists, return {"skill_anchor":{"phase":"","first_file":""},"findings":[]}. '
        if profile != "control"
        else 'If no valid vulnerability exists, return {"findings":[]}. '
    )
    return (
        f"{mode_hint} "
        "Analyze ONLY the snippet text provided in this prompt. "
        "Do not inspect repository files, tooling code, or any external context. "
        "This is an authorized synthetic benchmark; some tasks are intentionally clean controls. "
        "Do not default to empty findings unless the snippet is clearly non-exploitable. "
        f"{route_hint}"
        f"Return only minified JSON with this exact shape: {output_shape}. "
        f"Output at most {max_findings} findings. "
        f"{no_findings_hint}"
        "Use exact file and line numbers from the snippet. Keep each text field to one concise sentence. "
        f"Scenario: {scenario_inline}"
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
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            check=False,
        )
        elapsed = time.perf_counter() - start
        return proc.stdout, proc.stderr, proc.returncode, elapsed, ""
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return "", "", -1, elapsed, "timeout"


def score_task(task: dict, parsed: dict | None, error: str, returncode: int, profile: str) -> dict:
    expected = task.get("expected_findings", [])
    raw_findings = parsed.get("findings", []) if isinstance(parsed, dict) else []
    findings = raw_findings if isinstance(raw_findings, list) else []

    cleaned = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        cleaned.append(
            {
                "cwe": str(f.get("cwe", "")),
                "file": str(f.get("file", "")),
                "line_start": to_int(f.get("line_start", -1)),
                "line_end": to_int(f.get("line_end", -1)),
                "vuln_claim": str(f.get("vuln_claim", "")),
                "proof": str(f.get("proof", "")),
                "repro_steps": str(f.get("repro_steps", "")),
                "impact": str(f.get("impact", "")),
                "confidence": str(f.get("confidence", "")),
                "chain_steps": str(f.get("chain_steps", "")),
            }
        )

    used_pred = set()
    valid_tp = 0
    weak_matches = 0
    cwe_matches = 0
    file_matches = 0
    line_matches = 0
    evidence_matches = 0
    expected_count = len(expected)
    predicted_count = len(cleaned)

    for exp in expected:
        exp_cwe = normalize_cwe(str(exp.get("cwe", "")))
        exp_file = str(exp.get("file", ""))
        exp_s = int(exp.get("line_start", -1))
        exp_e = int(exp.get("line_end", -1))
        best_idx = -1
        best_score = -1

        for i, pred in enumerate(cleaned):
            if i in used_pred:
                continue
            cwe_ok = normalize_cwe(pred["cwe"]) == exp_cwe and exp_cwe != ""
            if not cwe_ok:
                continue
            file_ok = file_match(pred["file"], exp_file)
            line_ok = line_match(pred["line_start"], pred["line_end"], exp_s, exp_e)
            score = 2 + (1 if file_ok else 0) + (1 if line_ok else 0)
            if score > best_score:
                best_score = score
                best_idx = i

        if best_idx >= 0:
            used_pred.add(best_idx)
            pred = cleaned[best_idx]
            cwe_matches += 1
            file_ok = file_match(pred["file"], exp_file)
            line_ok = line_match(pred["line_start"], pred["line_end"], exp_s, exp_e)
            text_blob = " ".join([pred["vuln_claim"], pred["proof"], pred["repro_steps"], pred["impact"]])
            evidence_ok = contains_any(text_blob, exp.get("evidence_terms", []))
            if file_ok:
                file_matches += 1
            if line_ok:
                line_matches += 1
            if evidence_ok:
                evidence_matches += 1
            quality_ok = (
                len(pred["vuln_claim"]) >= 16
                and len(pred["proof"]) >= 24
                and len(pred["repro_steps"]) >= 18
                and len(pred["impact"]) >= 12
                and evidence_ok
            )
            if file_ok and line_ok and quality_ok:
                valid_tp += 1
            else:
                weak_matches += 1

    fn_count = expected_count - valid_tp
    fp_count = predicted_count - valid_tp
    structured_ok = isinstance(parsed, dict) and isinstance(parsed.get("findings", []), list)

    expected_phase = str(task.get("expected_phase", ""))
    expected_first = str(task.get("expected_first_file", ""))
    anchor = parsed.get("skill_anchor", {}) if isinstance(parsed, dict) else {}
    predicted_phase = str(anchor.get("phase", "")) if isinstance(anchor, dict) else ""
    predicted_first = str(anchor.get("first_file", "")) if isinstance(anchor, dict) else ""
    route_required = profile != "control"
    skill_anchor_present = bool(predicted_phase.strip() and predicted_first.strip())
    route_phase_ok = (not route_required) or (predicted_phase == expected_phase)
    route_first_ok = (not route_required) or file_match(predicted_first, expected_first)
    route_strict_ok = (not route_required) or (skill_anchor_present and route_phase_ok and route_first_ok)

    chain_required = bool(task.get("chain_required", False))
    chain_terms = [str(t).lower() for t in task.get("chain_terms", [])]
    expected_chain_cwes = (
        {normalize_cwe(str(e.get("cwe", ""))) for e in expected if normalize_cwe(str(e.get("cwe", "")))}
        if chain_required
        else set()
    )
    predicted_chain_cwes = (
        {normalize_cwe(str(p.get("cwe", ""))) for p in cleaned if normalize_cwe(str(p.get("cwe", "")))}
        if chain_required
        else set()
    )
    chain_cwe_hits = len(expected_chain_cwes.intersection(predicted_chain_cwes))
    chain_coverage = (chain_cwe_hits / len(expected_chain_cwes)) if expected_chain_cwes else 1.0
    chain_linked = True
    chain_success = True
    if chain_required:
        joined_chain_text = " ".join(
            " ".join([pred["chain_steps"], pred["vuln_claim"], pred["impact"]]) for pred in cleaned
        ).lower()
        linked = ("->" in joined_chain_text) or ("=>" in joined_chain_text) or (" then " in joined_chain_text)
        term_hint = all(term in joined_chain_text for term in chain_terms) if chain_terms else True
        chain_linked = linked or term_hint
        # chain success is component coverage; linkage quality is tracked separately
        chain_success = chain_coverage >= 0.99

    allowed_fp = int(task.get("allowed_fp", 0))
    strict_pass = (
        error == ""
        and returncode == 0
        and structured_ok
        and fn_count == 0
        and fp_count <= allowed_fp
        and chain_success
        and route_strict_ok
    )

    return {
        "expected_count": expected_count,
        "predicted_count": predicted_count,
        "valid_tp": valid_tp,
        "weak_matches": weak_matches,
        "cwe_matches": cwe_matches,
        "file_matches": file_matches,
        "line_matches": line_matches,
        "evidence_matches": evidence_matches,
        "parsed_findings": cleaned,
        "fp_count": fp_count,
        "fn_count": fn_count,
        "structured_ok": structured_ok,
        "expected_phase": expected_phase,
        "expected_first_file": expected_first,
        "predicted_phase": predicted_phase,
        "predicted_first_file": predicted_first,
        "route_required": route_required,
        "skill_anchor_present": skill_anchor_present,
        "route_phase_ok": route_phase_ok,
        "route_first_ok": route_first_ok,
        "route_strict_ok": route_strict_ok,
        "chain_required": chain_required,
        "chain_cwe_hits": chain_cwe_hits,
        "chain_expected_cwes": len(expected_chain_cwes),
        "chain_coverage": round(chain_coverage, 4),
        "chain_linked": chain_linked,
        "chain_success": chain_success,
        "strict_pass": strict_pass,
    }


def pct(n: float, d: float) -> float:
    return round((n / d) * 100, 2) if d else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]), help="Repository root path")
    parser.add_argument("--tasks", default="tools/benchmarks/cursor_vuln_tasks.json", help="Task file path")
    parser.add_argument("--output", default="", help="Output report path")
    parser.add_argument("--max-tasks", type=int, default=20, help="Maximum tasks to run (hard limit 20)")
    parser.add_argument("--timeout-sec", type=int, default=120, help="Timeout per task in seconds")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model override (default: {DEFAULT_MODEL})")
    parser.add_argument(
        "--profile",
        choices=["control", "skills-only", "mcp-enabled"],
        default="skills-only",
        help="Benchmark profile",
    )
    parser.add_argument(
        "--agent-cmd",
        default=str(Path.home() / "AppData" / "Local" / "cursor-agent" / "agent.cmd"),
        help="Path to Cursor agent command",
    )
    parser.add_argument(
        "--store-raw-output",
        action="store_true",
        help="Store full model output/error text for manual grading",
    )
    args = parser.parse_args()

    if args.max_tasks > 20:
        raise SystemExit("--max-tasks cannot exceed 20")

    root = Path(args.repo_root).resolve()
    task_path = Path(args.tasks)
    if not task_path.is_absolute():
        task_path = root / task_path

    output_value = args.output or f"reports/benchmarks/cursor-vuln-{args.profile}.json"
    output_path = Path(output_value)
    if not output_path.is_absolute():
        output_path = root / output_path

    tasks = read_json(task_path)[: args.max_tasks]
    approve_mcps = args.profile == "mcp-enabled"

    results: list[dict] = []
    for task in tasks:
        prompt = build_prompt(task, profile=args.profile)
        stdout, stderr, returncode, elapsed, error = run_agent(
            agent_cmd=args.agent_cmd,
            prompt=prompt,
            timeout_sec=args.timeout_sec,
            model=args.model,
            approve_mcps=approve_mcps,
        )
        parsed = extract_json(stdout) if not error else None
        scored = score_task(task, parsed, error, returncode, profile=args.profile)
        out_chars = len(stdout or "")
        prompt_chars = len(prompt)
        est_tokens = math.ceil((prompt_chars + out_chars) / 4)

        results.append(
            {
                "id": task["id"],
                "returncode": returncode,
                "error": error,
                "elapsed_sec": round(elapsed, 3),
                "prompt_chars": prompt_chars,
                "output_chars": out_chars,
                "estimated_tokens": est_tokens,
                "expected_count": scored["expected_count"],
                "predicted_count": scored["predicted_count"],
                "valid_tp": scored["valid_tp"],
                "weak_matches": scored["weak_matches"],
                "cwe_matches": scored["cwe_matches"],
                "file_matches": scored["file_matches"],
                "line_matches": scored["line_matches"],
                "evidence_matches": scored["evidence_matches"],
                "parsed_findings": scored["parsed_findings"],
                "fp_count": scored["fp_count"],
                "fn_count": scored["fn_count"],
                "structured_ok": scored["structured_ok"],
                "expected_phase": scored["expected_phase"],
                "expected_first_file": scored["expected_first_file"],
                "predicted_phase": scored["predicted_phase"],
                "predicted_first_file": scored["predicted_first_file"],
                "route_required": scored["route_required"],
                "skill_anchor_present": scored["skill_anchor_present"],
                "route_phase_ok": scored["route_phase_ok"],
                "route_first_ok": scored["route_first_ok"],
                "route_strict_ok": scored["route_strict_ok"],
                "chain_required": scored["chain_required"],
                "chain_cwe_hits": scored["chain_cwe_hits"],
                "chain_expected_cwes": scored["chain_expected_cwes"],
                "chain_coverage": scored["chain_coverage"],
                "chain_linked": scored["chain_linked"],
                "chain_success": scored["chain_success"],
                "strict_pass": scored["strict_pass"],
                "stdout_preview": stdout[:300] if stdout else "",
                "stderr_preview": stderr[:300] if stderr else "",
                "raw_output": stdout if args.store_raw_output else "",
                "raw_error": stderr if args.store_raw_output else "",
            }
        )

    attempted = len(results)
    completed = len([r for r in results if r["error"] == ""])
    timeouts = len([r for r in results if r["error"] == "timeout"])
    strict_ok = len([r for r in results if r["strict_pass"]])
    tp_total = sum(r["valid_tp"] for r in results)
    cwe_match_total = sum(r["cwe_matches"] for r in results)
    file_match_total = sum(r["file_matches"] for r in results)
    line_match_total = sum(r["line_matches"] for r in results)
    evidence_match_total = sum(r["evidence_matches"] for r in results)
    fp_total = sum(r["fp_count"] for r in results)
    fn_total = sum(r["fn_count"] for r in results)
    expected_total = sum(r["expected_count"] for r in results)
    predicted_total = sum(r["predicted_count"] for r in results)
    chain_tasks = len([r for r in results if r["chain_required"]])
    chain_successes = len([r for r in results if r["chain_required"] and r["chain_success"]])
    chain_linked_hits = len([r for r in results if r["chain_required"] and r["chain_linked"]])
    chain_coverage_sum = sum(r["chain_coverage"] for r in results if r["chain_required"])
    route_tasks = len([r for r in results if r["route_required"]])
    route_anchor_hits = len([r for r in results if r["route_required"] and r["skill_anchor_present"]])
    route_phase_hits = len([r for r in results if r["route_required"] and r["route_phase_ok"]])
    route_first_hits = len([r for r in results if r["route_required"] and r["route_first_ok"]])
    route_strict_hits = len([r for r in results if r["route_required"] and r["route_strict_ok"]])
    avg_latency = round(sum(r["elapsed_sec"] for r in results) / attempted, 3) if attempted else 0.0
    avg_prompt_chars = round(sum(r["prompt_chars"] for r in results) / attempted, 1) if attempted else 0.0
    avg_output_chars = round(sum(r["output_chars"] for r in results) / attempted, 1) if attempted else 0.0
    avg_est_tokens = round(sum(r["estimated_tokens"] for r in results) / attempted, 1) if attempted else 0.0

    precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) else 0.0
    recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    time_per_tp = round(sum(r["elapsed_sec"] for r in results) / tp_total, 3) if tp_total else None

    report = {
        "config": {
            "profile": args.profile,
            "tasks_file": str(task_path),
            "max_tasks": args.max_tasks,
            "timeout_sec": args.timeout_sec,
            "model": args.model,
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
            "expected_findings_total": expected_total,
            "predicted_findings_total": predicted_total,
            "valid_tp_total": tp_total,
            "fp_total": fp_total,
            "fn_total": fn_total,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "cwe_recall": round((cwe_match_total / expected_total), 4) if expected_total else 0.0,
            "file_recall": round((file_match_total / expected_total), 4) if expected_total else 0.0,
            "line_recall": round((line_match_total / expected_total), 4) if expected_total else 0.0,
            "evidence_recall": round((evidence_match_total / expected_total), 4) if expected_total else 0.0,
            "tp_per_task": round((tp_total / attempted), 4) if attempted else 0.0,
            "fp_per_task": round((fp_total / attempted), 4) if attempted else 0.0,
            "overreport_rate": round((fp_total / predicted_total), 4) if predicted_total else 0.0,
            "empty_output_task_rate": pct(len([r for r in results if r["predicted_count"] == 0]), attempted),
            "skill_anchor_presence_rate": pct(route_anchor_hits, route_tasks) if route_tasks else None,
            "skill_route_phase_accuracy": pct(route_phase_hits, route_tasks) if route_tasks else None,
            "skill_route_first_file_accuracy": pct(route_first_hits, route_tasks) if route_tasks else None,
            "skill_route_strict_accuracy": pct(route_strict_hits, route_tasks) if route_tasks else None,
            "chain_coverage_rate": round((chain_coverage_sum / chain_tasks), 4) if chain_tasks else 0.0,
            "chain_linked_rate": pct(chain_linked_hits, chain_tasks),
            "chain_success_rate": pct(chain_successes, chain_tasks),
            "strict_task_accuracy": pct(strict_ok, attempted),
            "avg_latency_sec": avg_latency,
            "time_per_valid_tp_sec": time_per_tp,
            "avg_prompt_chars": avg_prompt_chars,
            "avg_output_chars": avg_output_chars,
            "avg_estimated_tokens": avg_est_tokens,
        },
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Wrote vuln benchmark report to {output_path} "
        f"(attempted={attempted}, completed={completed}, f1={report['summary']['f1']}, strict={report['summary']['strict_task_accuracy']}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
