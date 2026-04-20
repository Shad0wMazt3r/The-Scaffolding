#!/usr/bin/env python3
"""Generate manual grading scaffolds for CTF benchmark writeups."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def count_command_signals(text: str) -> int:
    return len(re.findall(r"(?im)^\s*(?:\$|PS>|#\s*(?:curl|python|docker|nc|socat)\b)", text))


def count_evidence_signals(text: str) -> int:
    patterns = [
        r"(?i)\bflag\{[^}\n]+\}",
        r"(?i)\bhash\b",
        r"(?i)\bsha(?:1|256|512)?\b",
        r"(?i)\blog\b",
        r"(?i)\bresponse\b",
        r"(?i)\bproof\b",
    ]
    return sum(1 for p in patterns if re.search(p, text))


def section_coverage(section_presence: dict[str, bool]) -> float:
    total = len(section_presence)
    if total == 0:
        return 0.0
    present = sum(1 for ok in section_presence.values() if ok)
    return round(present / total, 4)


def render_markdown_worksheet(output: dict, rubric: dict) -> str:
    lines: list[str] = []
    lines.append("# CTF Benchmark Manual Grading Worksheet")
    lines.append("")
    lines.append(f"Run report: `{output['config']['run_report']}`")
    lines.append("")
    lines.append("## Rubric dimensions")
    lines.append("")
    for dim in rubric.get("dimensions", []):
        lines.append(
            f"- **{dim['label']}** (`{dim['key']}`): {dim['min']}..{dim['max']} — {dim.get('guidance', '')}"
        )
    lines.append("")
    lines.append("## Penalties")
    lines.append("")
    for pen in rubric.get("penalties", []):
        lines.append(f"- **{pen['label']}** (`{pen['key']}`): {pen['min']}..{pen['max']}")
    lines.append("")
    lines.append("## Challenge grading sheets")
    lines.append("")

    for row in output.get("grading_sheet", []):
        lines.append(f"### {row['challenge_id']} ({row['category']})")
        lines.append("")
        lines.append(f"- Writeup path: `{row['writeup_path']}`")
        lines.append(f"- Auto section coverage: `{row['auto']['section_coverage']}`")
        lines.append(f"- Auto command signals: `{row['auto']['command_signals']}`")
        lines.append(f"- Auto evidence signals: `{row['auto']['evidence_signals']}`")
        lines.append(f"- Auto runtime errors: `{', '.join(row['auto']['errors']) if row['auto']['errors'] else 'none'}`")
        lines.append("")
        lines.append("Manual scores:")
        for field in row.get("manual_scores", {}):
            lines.append(f"- `{field}`: ")
        lines.append("")
        lines.append("Penalty adjustments:")
        for field in row.get("manual_penalties", {}):
            lines.append(f"- `{field}`: ")
        lines.append("")
        lines.append("Reviewer notes:")
        lines.append("")
        lines.append("```")
        lines.append("")
        lines.append("```")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-report", required=True, help="Path to run-report.json from run_cursor_ctf_benchmark.py")
    parser.add_argument("--rubric", default="ctf-benchmarking/grading/rubric.json", help="Rubric JSON path")
    parser.add_argument("--output", default="", help="Output grading JSON path")
    parser.add_argument("--worksheet-md", default="", help="Optional markdown worksheet output path")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    run_report_path = Path(args.run_report)
    if not run_report_path.is_absolute():
        run_report_path = repo_root / run_report_path
    rubric_path = Path(args.rubric)
    if not rubric_path.is_absolute():
        rubric_path = repo_root / rubric_path

    run_report = read_json(run_report_path)
    rubric = read_json(rubric_path)

    results = run_report.get("results", [])
    grading_sheet: list[dict] = []
    for row in results:
        challenge_id = str(row.get("id", "unknown"))
        writeup_path = run_report_path.parent / challenge_id / "writeup.md"
        writeup_text = writeup_path.read_text(encoding="utf-8") if writeup_path.exists() else ""
        section_presence = row.get("section_presence", {})
        auto = {
            "section_coverage": section_coverage(section_presence),
            "command_signals": count_command_signals(writeup_text),
            "evidence_signals": count_evidence_signals(writeup_text),
            "errors": row.get("errors", []),
            "writeup_complete_flag": bool(row.get("writeup_complete", False)),
        }

        manual_scores = {dim["key"]: None for dim in rubric.get("dimensions", [])}
        manual_penalties = {pen["key"]: 0 for pen in rubric.get("penalties", [])}
        grading_sheet.append(
            {
                "challenge_id": challenge_id,
                "category": row.get("category"),
                "title": row.get("title"),
                "writeup_path": str(writeup_path),
                "section_presence": section_presence,
                "auto": auto,
                "manual_scores": manual_scores,
                "manual_penalties": manual_penalties,
                "reviewer_notes": "",
                "final_score": None,
            }
        )

    output = {
        "config": {
            "run_report": str(run_report_path),
            "rubric": str(rubric_path),
        },
        "rubric": rubric,
        "grading_sheet": grading_sheet,
    }

    output_path = Path(args.output) if args.output else (run_report_path.parent / "manual-grade.json")
    if not output_path.is_absolute():
        output_path = repo_root / output_path
    write_text(output_path, json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"Wrote manual grading JSON: {output_path}")

    if args.worksheet_md:
        worksheet_path = Path(args.worksheet_md)
        if not worksheet_path.is_absolute():
            worksheet_path = repo_root / worksheet_path
        write_text(worksheet_path, render_markdown_worksheet(output, rubric))
        print(f"Wrote worksheet markdown: {worksheet_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

