#!/usr/bin/env python3
"""Normalize known markdown issues in skill files."""

from __future__ import annotations

import argparse
from pathlib import Path

FOOTNOTE_MAP = {
    "[^1]": " [projectdiscovery](https://docs.projectdiscovery.io/tools/subfinder/overview)",
    "[^2]": " [projectdiscovery](https://docs.projectdiscovery.io/tools/katana/overview)",
    "[^3]": " [projectdiscovery](https://docs.projectdiscovery.io/tools/httpx/overview)",
    "[^5]": " [projectdiscovery](https://docs.projectdiscovery.io/tools/subfinder/usage)",
    "[^6]": " [projectdiscovery](https://docs.projectdiscovery.io/tools/katana/usage)",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_text(text: str, fix_footnotes: bool) -> str:
    updated = text.replace("&#x20;", " ")
    updated = updated.replace(r"\*\*\*", "***")
    updated = "\n".join(line.rstrip() for line in updated.splitlines()) + ("\n" if updated.endswith("\n") else "")
    if fix_footnotes:
        for token, replacement in FOOTNOTE_MAP.items():
            updated = updated.replace(token, replacement)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write changes to disk",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if normalization would change any file",
    )
    parser.add_argument(
        "--fix-footnotes",
        action="store_true",
        help="Replace unresolved [^N] references with inline links",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    files = sorted((root / ".agents" / "skills").glob("*/*.md"))

    changed: list[str] = []
    for path in files:
        original = read(path)
        normalized = normalize_text(original, fix_footnotes=args.fix_footnotes)
        if normalized != original:
            changed.append(path.relative_to(root).as_posix())
            if args.write:
                path.write_text(normalized, encoding="utf-8")

    mode = "write" if args.write else "dry-run"
    print(f"Normalization ({mode}) changed_files={len(changed)}")
    for item in changed:
        print(f" - {item}")
    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
