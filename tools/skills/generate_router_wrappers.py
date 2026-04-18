#!/usr/bin/env python3
"""Generate cross-agent router wrappers from a single canonical spec."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def shared_block(rules: list[str], ambiguity: str) -> str:
    lines = ["<!-- ROUTER_SHARED_RULES_START -->"]
    for rule in rules:
        lines.append(f"- {rule}")
    lines.append(f"- {ambiguity}")
    lines.append("<!-- ROUTER_SHARED_RULES_END -->")
    return "\n".join(lines)


def render_cursor(spec: dict) -> str:
    block = shared_block(spec["shared_rules"], spec["ambiguity_rule"])
    return (
        "---\n"
        f"name: {spec['name']}\n"
        f"description: {spec['description']}\n"
        "---\n"
        "<!-- GENERATED: tools/skills/generate_router_wrappers.py -->\n"
        "You are a phase-aware bug bounty and CTF guidance router.\n\n"
        f"{block}\n"
    )


def render_github(spec: dict) -> str:
    block = shared_block(spec["shared_rules"], spec["ambiguity_rule"])
    return (
        "---\n"
        f"name: {spec['name']}\n"
        f"description: {spec['description']}\n"
        "---\n"
        "<!-- GENERATED: tools/skills/generate_router_wrappers.py -->\n"
        "You are an authorization-aware bug bounty and CTF operations assistant for this repository.\n\n"
        f"{block}\n"
    )


def render_opencode(spec: dict) -> str:
    block = shared_block(spec["shared_rules"], spec["ambiguity_rule"])
    return (
        "---\n"
        f"description: {spec['description']}\n"
        "mode: all\n"
        "permission:\n"
        "  skill:\n"
        "    \"*\": \"allow\"\n"
        "  bash:\n"
        "    \"*\": \"allow\"\n"
        "---\n"
        "<!-- GENERATED: tools/skills/generate_router_wrappers.py -->\n"
        "You are the bug-hunt workflow operator.\n\n"
        f"{block}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    parser.add_argument(
        "--spec",
        default=".agents/standards/router-spec.json",
        help="Router spec path",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = root / spec_path

    spec = json.loads(read_text(spec_path))
    targets = spec["targets"]
    output_map = {
        "cursor": render_cursor(spec),
        "github": render_github(spec),
        "opencode": render_opencode(spec),
    }

    for key, content in output_map.items():
        out = root / targets[key]
        write_text(out, content.rstrip() + "\n")
        print(f"Wrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
