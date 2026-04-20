#!/usr/bin/env python3
"""Run the dockerized 5-challenge CTF benchmark with mandatory writeups."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_AGENT_CMD = str(Path.home() / "AppData" / "Local" / "cursor-agent" / "agent.cmd")
DEFAULT_MODEL = "composer-2"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def split_command(command: str) -> list[str]:
    return shlex.split(command, posix=(os.name != "nt"))


def run_cmd(
    cmd: list[str],
    timeout_sec: int,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str, float, str]:
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            check=False,
        )
        elapsed = time.perf_counter() - start
        return proc.returncode, proc.stdout, proc.stderr, elapsed, ""
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return -1, "", "", elapsed, "timeout"


def run_agent(agent_cmd: str, prompt: str, timeout_sec: int, model: str) -> tuple[str, str, int, float, str]:
    cmd = [agent_cmd, "-p", "--output-format", "text", "--trust", "--force", "--mode", "ask"]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    rc, out, err, elapsed, error = run_cmd(cmd, timeout_sec=timeout_sec)
    return out, err, rc, elapsed, error


def docker_compose_up(compose_file: Path, project_name: str) -> str:
    return f'docker compose -f "{compose_file}" --project-name "{project_name}" up -d --build'


def docker_compose_down(compose_file: Path, project_name: str) -> str:
    return f'docker compose -f "{compose_file}" --project-name "{project_name}" down --remove-orphans --volumes'


def docker_compose_status(compose_file: Path, project_name: str, service_name: str) -> str:
    return (
        f'docker compose -f "{compose_file}" --project-name "{project_name}" '
        f'ps --status running --services'
    )


def healthcheck_tcp(host: str, port: int, timeout_sec: int) -> tuple[bool, str]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                return True, ""
        except OSError:
            time.sleep(2)
    return False, f"tcp healthcheck failed for {host}:{port}"


def healthcheck_container(
    compose_file: Path,
    project_name: str,
    service_name: str,
    timeout_sec: int,
    env: dict[str, str],
) -> tuple[bool, str]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        cmd = split_command(docker_compose_status(compose_file, project_name, service_name))
        rc, out, err, _elapsed, error = run_cmd(cmd, timeout_sec=30, env=env)
        if error:
            time.sleep(2)
            continue
        if rc == 0 and service_name in {line.strip() for line in out.splitlines()}:
            return True, ""
        if err.strip():
            time.sleep(2)
            continue
        time.sleep(2)
    return False, f"container healthcheck failed for service '{service_name}'"


def run_healthcheck(challenge: dict, compose_file: Path, env: dict[str, str]) -> tuple[bool, str]:
    deployment = challenge.get("deployment", {})
    healthcheck = challenge.get("healthcheck", {})
    project_name = str(deployment.get("project_name", challenge.get("id", "ctfbench")))
    service_name = str(deployment.get("service_name", "challenge"))
    h_type = str(healthcheck.get("type", "")).strip()
    timeout_sec = int(healthcheck.get("timeout_sec", 180))
    if h_type == "tcp":
        host = str(healthcheck.get("host", "127.0.0.1"))
        port = int(healthcheck.get("port", 0))
        return healthcheck_tcp(host, port, timeout_sec)
    if h_type == "container_running":
        return healthcheck_container(compose_file, project_name, service_name, timeout_sec, env)
    return False, f"unsupported healthcheck type '{h_type}'"


def section_presence(writeup: str, required_sections: list[str]) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for section in required_sections:
        escaped = re.escape(section)
        heading_re = re.compile(rf"(?im)^\s*#{1,6}\s*{escaped}\s*$")
        label_re = re.compile(rf"(?im)^\s*{escaped}\s*:")
        out[section] = bool(heading_re.search(writeup) or label_re.search(writeup))
    return out


def build_prompt(template: str, challenge: dict) -> str:
    target = challenge.get("target", {})
    target_desc = f"{target.get('type', 'unknown')}: {target.get('endpoint', 'n/a')}"
    return template.format(
        challenge_id=challenge.get("id", ""),
        title=challenge.get("title", ""),
        category=challenge.get("category", ""),
        difficulty=challenge.get("difficulty", ""),
        target=target_desc,
        challenge_brief=challenge.get("challenge_brief", ""),
    )


def load_manifest(path: Path) -> dict:
    data = read_json(path)
    if "challenges" not in data or "sources" not in data:
        raise SystemExit("Manifest must include 'sources' and 'challenges'.")
    return data


def source_path_for_challenge(challenge: dict, sources: dict, source_root: Path) -> Path:
    source = challenge.get("source", {})
    repo_key = str(source.get("repo_key", ""))
    source_cfg = sources.get(repo_key, {})
    local_subdir = str(source_cfg.get("local_subdir", "")).strip()
    expected_subpath = str(source.get("expected_subpath", "")).strip()
    if not local_subdir or not expected_subpath:
        raise SystemExit(f"Challenge '{challenge.get('id')}' has incomplete source config.")
    return source_root / local_subdir / expected_subpath


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="ctf-benchmarking/manifest.json", help="Manifest path")
    parser.add_argument("--source-root", default="ctf-benchmarking/sources", help="Root source directory")
    parser.add_argument("--output-dir", default="", help="Output run directory")
    parser.add_argument("--challenge-ids", nargs="*", default=[], help="Optional subset of challenge IDs")
    parser.add_argument("--agent-cmd", default=DEFAULT_AGENT_CMD, help="Path to agent command")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model override (default: {DEFAULT_MODEL})")
    parser.add_argument("--setup-timeout-sec", type=int, default=600, help="Docker up/down timeout")
    parser.add_argument("--agent-timeout-sec", type=int, default=1800, help="Per-challenge agent timeout")
    parser.add_argument("--skip-agent", action="store_true", help="Run lifecycle only; skip agent call")
    parser.add_argument("--keep-environment", action="store_true", help="Keep challenge containers running after each run")
    parser.add_argument("--store-raw-output", action="store_true", default=True, help="Persist raw outputs")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    source_root = Path(args.source_root)
    if not source_root.is_absolute():
        source_root = repo_root / source_root

    manifest = load_manifest(manifest_path)
    challenges = manifest.get("challenges", [])
    required_sections = [str(s) for s in manifest.get("required_writeup_sections", [])]
    if args.challenge_ids:
        wanted = set(args.challenge_ids)
        challenges = [c for c in challenges if c.get("id") in wanted]
        missing = wanted - {str(c.get("id")) for c in challenges}
        if missing:
            raise SystemExit(f"Unknown challenge IDs: {', '.join(sorted(missing))}")

    if not challenges:
        raise SystemExit("No challenges selected.")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else repo_root / "reports" / "benchmarks" / f"ctf-run-{run_id}"
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_template = read_text(repo_root / "ctf-benchmarking" / "templates" / "agent_prompt.txt")
    env = os.environ.copy()
    env["CTF_SOURCES_ROOT"] = source_root.resolve().as_posix()

    results: list[dict] = []
    for challenge in challenges:
        challenge_id = str(challenge.get("id"))
        challenge_dir = output_dir / challenge_id
        challenge_dir.mkdir(parents=True, exist_ok=True)

        compose_rel = str(challenge.get("deployment", {}).get("compose_file", "")).strip()
        if not compose_rel:
            raise SystemExit(f"Challenge '{challenge_id}' is missing deployment.compose_file.")
        compose_file = Path(compose_rel)
        if not compose_file.is_absolute():
            compose_file = repo_root / compose_file

        source_path = source_path_for_challenge(challenge, manifest["sources"], source_root)
        prompt = build_prompt(prompt_template, challenge)
        write_text(challenge_dir / "prompt.txt", prompt)

        row: dict = {
            "id": challenge_id,
            "category": challenge.get("category"),
            "title": challenge.get("title"),
            "source_path": str(source_path),
            "compose_file": str(compose_file),
            "started_at": now_iso(),
            "errors": [],
        }

        if not source_path.exists():
            row["errors"].append(
                f"missing source path: {source_path}. Run fetch_ctf_sources.py or clone manually per policy."
            )
            row["ended_at"] = now_iso()
            row["writeup_complete"] = False
            row["section_presence"] = {s: False for s in required_sections}
            results.append(row)
            continue

        up_cmd = split_command(
            docker_compose_up(
                compose_file=compose_file,
                project_name=str(challenge.get("deployment", {}).get("project_name", f"ctfbench-{challenge_id}")),
            )
        )
        up_rc, up_out, up_err, up_elapsed, up_error = run_cmd(
            up_cmd,
            timeout_sec=args.setup_timeout_sec,
            env=env,
        )
        row["deploy"] = {
            "command": " ".join(up_cmd),
            "returncode": up_rc,
            "elapsed_sec": round(up_elapsed, 3),
            "error": up_error,
        }
        if up_out.strip():
            write_text(challenge_dir / "deploy_stdout.txt", up_out)
        if up_err.strip():
            write_text(challenge_dir / "deploy_stderr.txt", up_err)
        if up_rc != 0 or up_error:
            row["errors"].append("deployment_failed")
        else:
            ok, health_error = run_healthcheck(challenge, compose_file, env)
            row["healthcheck"] = {"ok": ok, "error": health_error}
            if not ok:
                row["errors"].append("healthcheck_failed")

        agent_stdout = ""
        agent_stderr = ""
        agent_rc = 0
        agent_elapsed = 0.0
        agent_error = ""
        if not args.skip_agent and not row["errors"]:
            agent_stdout, agent_stderr, agent_rc, agent_elapsed, agent_error = run_agent(
                agent_cmd=args.agent_cmd,
                prompt=prompt,
                timeout_sec=args.agent_timeout_sec,
                model=args.model,
            )
            if args.store_raw_output:
                write_text(challenge_dir / "agent_stdout.txt", agent_stdout)
                write_text(challenge_dir / "agent_stderr.txt", agent_stderr)
            row["agent"] = {
                "returncode": agent_rc,
                "elapsed_sec": round(agent_elapsed, 3),
                "error": agent_error,
            }
            if agent_rc != 0 or agent_error:
                row["errors"].append("agent_failed")
        else:
            row["agent"] = {"skipped": True}

        writeup = agent_stdout
        write_text(challenge_dir / "writeup.md", writeup)
        presence = section_presence(writeup, required_sections)
        missing_sections = [s for s, ok in presence.items() if not ok]
        row["section_presence"] = presence
        row["missing_sections"] = missing_sections
        row["writeup_complete"] = (len(missing_sections) == 0) and (not row["errors"]) and (not args.skip_agent)

        if not args.keep_environment:
            down_cmd = split_command(
                docker_compose_down(
                    compose_file=compose_file,
                    project_name=str(challenge.get("deployment", {}).get("project_name", f"ctfbench-{challenge_id}")),
                )
            )
            down_rc, down_out, down_err, down_elapsed, down_error = run_cmd(
                down_cmd,
                timeout_sec=args.setup_timeout_sec,
                env=env,
            )
            row["teardown"] = {
                "command": " ".join(down_cmd),
                "returncode": down_rc,
                "elapsed_sec": round(down_elapsed, 3),
                "error": down_error,
            }
            if down_out.strip():
                write_text(challenge_dir / "teardown_stdout.txt", down_out)
            if down_err.strip():
                write_text(challenge_dir / "teardown_stderr.txt", down_err)

        row["ended_at"] = now_iso()
        results.append(row)

    completed = sum(1 for r in results if r.get("writeup_complete"))
    report = {
        "config": {
            "manifest": str(manifest_path),
            "source_root": str(source_root),
            "agent_cmd": args.agent_cmd,
            "model": args.model,
            "required_sections": required_sections,
            "generated_at": now_iso(),
        },
        "summary": {
            "total_challenges": len(results),
            "writeup_complete": completed,
            "writeup_incomplete": len(results) - completed,
        },
        "results": results,
    }

    report_path = output_dir / "run-report.json"
    write_text(report_path, json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote CTF benchmark report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

