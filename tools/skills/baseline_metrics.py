#!/usr/bin/env python3
"""Generate a reproducible baseline metrics snapshot for .agents skills."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import statistics
from pathlib import Path

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
FOOTNOTE_REF_RE = re.compile(r"\[\^\d+\]")
FOOTNOTE_DEF_RE = re.compile(r"(?m)^\[\^\d+\]:")
ESCAPED_H_RE = re.compile(r"(?m)^\\#{1,6}\s")
HTML_SPACE_RE = re.compile(r"&#x20;")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def approx_tokens(chars: int) -> int:
    return round(chars / 4)


def percentile(values: list[int], p: float) -> int:
    if not values:
        return 0
    sorted_vals = sorted(values)
    idx = int(round((len(sorted_vals) - 1) * p))
    return sorted_vals[idx]


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    parser.add_argument(
        "--output",
        default="reports/skill-baseline.json",
        help="Output file path, relative to repo root unless absolute",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path

    skill_root = root / ".agents" / "skills"
    manifest_files = sorted(skill_root.glob("*/SKILL.md"))
    ttp_files = sorted(
        p for p in skill_root.glob("*/*.md") if p.name.lower() != "skill.md"
    )

    ttp_records: list[dict] = []
    for path in ttp_files:
        text = read_text(path)
        chars = len(text)
        lines = line_count(text)
        links = MARKDOWN_LINK_RE.findall(text)
        foot_refs = FOOTNOTE_REF_RE.findall(text)
        foot_defs = FOOTNOTE_DEF_RE.findall(text)
        skill = path.parent.name

        ttp_records.append(
            {
                "path": rel(root, path),
                "skill": skill,
                "lines": lines,
                "chars": chars,
                "approx_tokens": approx_tokens(chars),
                "external_links": len(links),
                "footnote_refs": len(foot_refs),
                "footnote_defs": len(foot_defs),
                "has_primary_probe": ("Primary Probe" in text)
                or ("Primary Vector" in text)
                or ("Primary validation" in text),
                "has_dead_end": ("Dead End" in text) or ("Dead-end" in text),
                "has_data_chaining": ("Data Chaining" in text)
                or ("Data chaining" in text),
                "escaped_heading_count": len(ESCAPED_H_RE.findall(text)),
                "html_space_entity_count": len(HTML_SPACE_RE.findall(text)),
                "sha256": sha256_text(text),
            }
        )

    by_skill: dict[str, dict] = {}
    for record in ttp_records:
        skill = record["skill"]
        entry = by_skill.setdefault(
            skill,
            {
                "files": 0,
                "lines": 0,
                "chars": 0,
                "approx_tokens": 0,
                "files_with_links": 0,
                "files_with_primary_probe": 0,
                "files_with_dead_end": 0,
                "files_with_data_chaining": 0,
            },
        )
        entry["files"] += 1
        entry["lines"] += record["lines"]
        entry["chars"] += record["chars"]
        entry["approx_tokens"] += record["approx_tokens"]
        if record["external_links"] > 0:
            entry["files_with_links"] += 1
        if record["has_primary_probe"]:
            entry["files_with_primary_probe"] += 1
        if record["has_dead_end"]:
            entry["files_with_dead_end"] += 1
        if record["has_data_chaining"]:
            entry["files_with_data_chaining"] += 1

    line_values = [r["lines"] for r in ttp_records]
    char_values = [r["chars"] for r in ttp_records]
    token_values = [r["approx_tokens"] for r in ttp_records]

    router_files = [
        root / ".cursor" / "skills" / "bug-hunt-framework" / "SKILL.md",
        root / ".github" / "agents" / "bug-hunt-framework.agent.md",
        root / ".opencode" / "agents" / "bug-hunt-framework.md",
    ]
    router_baseline = []
    for router in router_files:
        if router.exists():
            text = read_text(router)
            router_baseline.append(
                {
                    "path": rel(root, router),
                    "lines": line_count(text),
                    "chars": len(text),
                    "sha256": sha256_text(text),
                }
            )

    unresolved_footnote_files = [
        {
            "path": r["path"],
            "footnote_refs": r["footnote_refs"],
            "footnote_defs": r["footnote_defs"],
        }
        for r in ttp_records
        if r["footnote_refs"] > r["footnote_defs"]
    ]
    formatting_artifacts = [
        {
            "path": r["path"],
            "escaped_heading_count": r["escaped_heading_count"],
            "html_space_entity_count": r["html_space_entity_count"],
        }
        for r in ttp_records
        if r["escaped_heading_count"] > 0 or r["html_space_entity_count"] > 0
    ]

    baseline = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repo_root": str(root),
        "scope": {
            "skill_root": ".agents/skills",
            "manifest_count": len(manifest_files),
            "ttp_file_count": len(ttp_files),
            "skill_count": len({p.parent.name for p in manifest_files}),
        },
        "totals": {
            "lines": sum(line_values),
            "chars": sum(char_values),
            "approx_tokens": sum(token_values),
        },
        "distribution": {
            "lines": {
                "min": min(line_values) if line_values else 0,
                "median": statistics.median(line_values) if line_values else 0,
                "p90": percentile(line_values, 0.90),
                "p95": percentile(line_values, 0.95),
                "max": max(line_values) if line_values else 0,
            },
            "approx_tokens": {
                "min": min(token_values) if token_values else 0,
                "median": statistics.median(token_values) if token_values else 0,
                "p90": percentile(token_values, 0.90),
                "p95": percentile(token_values, 0.95),
                "max": max(token_values) if token_values else 0,
            },
        },
        "largest_files_top10": [
            {
                "path": r["path"],
                "lines": r["lines"],
                "approx_tokens": r["approx_tokens"],
            }
            for r in sorted(ttp_records, key=lambda x: x["lines"], reverse=True)[:10]
        ],
        "per_skill": {k: by_skill[k] for k in sorted(by_skill)},
        "quality_findings": {
            "files_without_external_links": [
                r["path"]
                for r in sorted(ttp_records, key=lambda x: x["path"])
                if r["external_links"] == 0
            ],
            "unresolved_footnote_files": unresolved_footnote_files,
            "formatting_artifact_files": formatting_artifacts,
        },
        "router_baseline": router_baseline,
        "input_snapshot_sha256": sha256_text(
            "\n".join(f"{r['path']}:{r['sha256']}" for r in sorted(ttp_records, key=lambda x: x["path"]))
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote baseline metrics to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
