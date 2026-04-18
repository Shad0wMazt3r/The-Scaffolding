#!/usr/bin/env python3
"""Validate skill manifests and TTP files against the machine-readable contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
FOOTNOTE_REF_RE = re.compile(r"\[\^\d+\]")
FOOTNOTE_DEF_RE = re.compile(r"(?m)^\[\^\d+\]:")
ESCAPED_HEADING_RE = re.compile(r"(?m)^\\#{1,6}\s")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def approx_tokens(chars: int) -> int:
    return round(chars / 4)


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def front_matter(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def extract_block(front: str, key: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}:\s*\n((?:^[ \t].*\n?)*)")
    match = pattern.search(front)
    return match.group(1) if match else ""


def extract_files_list(front: str) -> list[str]:
    block = extract_block(front, "files")
    return [m.group(1).strip() for m in re.finditer(r"(?m)^\s*-\s+(.+?)\s*$", block)]


def extract_optional_deep(front: str) -> list[dict[str, str]]:
    block = extract_block(front, "optional_deep_files")
    if not block.strip():
        return []
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in block.splitlines():
        line = raw.strip()
        if line.startswith("- file:"):
            if current:
                items.append(current)
            current = {"file": line.split(":", 1)[1].strip()}
        elif current and line.startswith("load_when:"):
            current["load_when"] = line.split(":", 1)[1].strip()
    if current:
        items.append(current)
    return items


def extract_dependencies(front: str) -> list[str]:
    match = re.search(r"(?m)^dependencies:\s*\[(.*?)\]\s*$", front)
    if not match:
        return []
    raw = match.group(1).strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def parse_contract(path: Path) -> dict:
    return json.loads(read_text(path))


def validate(repo_root: Path, contract: dict) -> dict:
    skill_root = repo_root / contract["scope"]["skill_root"]
    manifests = sorted(skill_root.glob("*/SKILL.md"))
    ttp_files = sorted(p for p in skill_root.glob("*/*.md") if p.name != "SKILL.md")
    manifest_skill_names = {p.parent.name for p in manifests}

    errors: list[dict] = []
    warnings: list[dict] = []

    manifest_file_map: dict[str, set[str]] = {}
    deep_file_map: dict[str, set[str]] = {}
    referenced_ttp: set[str] = set()

    required_keys = contract["manifest_contract"]["required_front_matter_keys"]
    required_filename_re = re.compile(contract["manifest_contract"]["files_list"]["filename_regex"])
    deep_filename_re = re.compile(contract["manifest_contract"]["optional_deep_files"]["filename_regex"])

    for manifest in manifests:
        text = read_text(manifest)
        front = front_matter(text)
        manifest_rel = rel(repo_root, manifest)
        skill = manifest.parent.name
        manifest_file_map[skill] = set()
        deep_file_map[skill] = set()

        if front is None:
            errors.append({"type": "manifest_missing_front_matter", "path": manifest_rel})
            continue

        for key in required_keys:
            if re.search(rf"(?m)^{re.escape(key)}:", front) is None:
                errors.append({"type": "manifest_missing_key", "path": manifest_rel, "key": key})

        desc_match = re.search(r"(?m)^description:\s*(.+?)\s*$", front)
        if desc_match:
            if len(desc_match.group(1).strip()) > contract["manifest_contract"]["description_max_chars"]:
                warnings.append({"type": "manifest_description_too_long", "path": manifest_rel})

        dependencies = extract_dependencies(front)
        for dep in dependencies:
            if dep not in manifest_skill_names:
                errors.append(
                    {
                        "type": "manifest_unknown_dependency",
                        "path": manifest_rel,
                        "dependency": dep,
                    }
                )

        files_list = extract_files_list(front)
        numbers: list[int] = []
        for item in files_list:
            if not required_filename_re.match(item):
                errors.append({"type": "manifest_invalid_file_name", "path": manifest_rel, "file": item})
                continue
            numbers.append(int(item.split("-", 1)[0]))
            file_path = manifest.parent / item
            if not file_path.exists():
                errors.append({"type": "manifest_missing_referenced_file", "path": manifest_rel, "file": item})
            else:
                file_rel = rel(repo_root, file_path)
                referenced_ttp.add(file_rel)
                manifest_file_map[skill].add(file_rel)

        if numbers:
            expected = list(range(min(numbers), max(numbers) + 1))
            if sorted(numbers) != expected:
                errors.append({"type": "manifest_non_sequential_files", "path": manifest_rel, "numbers": numbers})

        deep_items = extract_optional_deep(front)
        for item in deep_items:
            file_name = item.get("file", "")
            if not deep_filename_re.match(file_name):
                errors.append({"type": "manifest_invalid_deep_file_name", "path": manifest_rel, "file": file_name})
                continue
            if "load_when" not in item or not item["load_when"]:
                errors.append({"type": "manifest_missing_deep_load_when", "path": manifest_rel, "file": file_name})
            file_path = manifest.parent / file_name
            if not file_path.exists():
                errors.append({"type": "manifest_missing_referenced_deep_file", "path": manifest_rel, "file": file_name})
            else:
                file_rel = rel(repo_root, file_path)
                referenced_ttp.add(file_rel)
                deep_file_map[skill].add(file_rel)

    exception_map = {e["file"]: e for e in contract.get("temporary_exceptions", [])}

    min_links = contract["ttp_contract"]["citations"]["minimum_external_links_per_file"]
    primary_markers = tuple(contract["ttp_contract"]["required_markers_any"])
    rec_markers = contract["ttp_contract"]["recommended_markers_all"]
    html_entities = contract["ttp_contract"]["formatting"]["forbid_html_entities"]

    fast_budget = contract["ttp_contract"]["budgets"]["fast_path"]
    deep_budget = contract["ttp_contract"]["budgets"]["deep_path"]

    for ttp in ttp_files:
        path_rel = rel(repo_root, ttp)
        text = read_text(ttp)
        chars = len(text)
        lines = line_count(text)
        token_est = approx_tokens(chars)
        links = len(LINK_RE.findall(text))
        foot_refs = len(FOOTNOTE_REF_RE.findall(text))
        foot_defs = len(FOOTNOTE_DEF_RE.findall(text))

        if path_rel not in referenced_ttp:
            warnings.append({"type": "unreferenced_ttp_file", "path": path_rel})

        for ent in html_entities:
            if ent in text:
                errors.append({"type": "forbidden_html_entity", "path": path_rel, "entity": ent})
        if ESCAPED_HEADING_RE.search(text):
            errors.append({"type": "escaped_heading_prefix", "path": path_rel})
        if foot_refs > foot_defs:
            errors.append(
                {
                    "type": "unresolved_footnotes",
                    "path": path_rel,
                    "refs": foot_refs,
                    "defs": foot_defs,
                }
            )
        if links < min_links:
            warnings.append({"type": "missing_external_link", "path": path_rel, "links": links})
        if not any(marker in text for marker in primary_markers):
            warnings.append({"type": "missing_primary_marker", "path": path_rel})
        for marker in rec_markers:
            if marker not in text:
                warnings.append({"type": "missing_recommended_marker", "path": path_rel, "marker": marker})

        budget = fast_budget
        is_deep = any(path_rel in deep_file_map.get(skill, set()) for skill in deep_file_map)
        if is_deep:
            budget = deep_budget
        if path_rel in exception_map:
            budget = {
                "max_lines": exception_map[path_rel]["max_lines"],
                "max_approx_tokens": exception_map[path_rel]["max_approx_tokens"],
            }
        if lines > budget["max_lines"] or token_est > budget["max_approx_tokens"]:
            errors.append(
                {
                    "type": "budget_exceeded",
                    "path": path_rel,
                    "lines": lines,
                    "approx_tokens": token_est,
                    "budget": budget,
                }
            )

    report = {
        "scope": {
            "manifest_count": len(manifests),
            "ttp_count": len(ttp_files),
        },
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    parser.add_argument(
        "--contract",
        default=".agents/standards/skill-contract.json",
        help="Path to machine-readable contract",
    )
    parser.add_argument(
        "--report",
        default="reports/skill-validation.json",
        help="Output report path",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    contract_path = Path(args.contract)
    if not contract_path.is_absolute():
        contract_path = root / contract_path
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = root / report_path

    contract = parse_contract(contract_path)
    report = validate(root, contract)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Validation complete: errors={report['summary']['errors']} "
        f"warnings={report['summary']['warnings']} report={report_path}"
    )
    if report["summary"]["errors"] > 0:
        return 1
    if args.strict and report["summary"]["warnings"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
