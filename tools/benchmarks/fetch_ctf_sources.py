#!/usr/bin/env python3
"""Fetch source repositories required by the CTF benchmark manifest."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cmd(cmd: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )


def clone_or_update(source_name: str, source_cfg: dict, dest: Path) -> None:
    repo_url = str(source_cfg.get("repo_url", "")).strip()
    ref = str(source_cfg.get("ref", "")).strip()
    if not repo_url:
        raise RuntimeError(f"Missing repo_url for source '{source_name}'")

    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        run_cmd(["git", "clone", "--depth", "1", repo_url, str(dest)])

    if ref:
        run_cmd(["git", "fetch", "--depth", "1", "origin", ref], cwd=dest)
        run_cmd(["git", "checkout", "--detach", ref], cwd=dest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="ctf-benchmarking/manifest.json",
        help="Path to benchmark manifest",
    )
    parser.add_argument(
        "--source-root",
        default="ctf-benchmarking/sources",
        help="Root folder where challenge sources are stored",
    )
    parser.add_argument(
        "--include-reference-only",
        action="store_true",
        help="Also fetch sources marked as reference-only/manual-clone",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    source_root = Path(args.source_root)
    if not source_root.is_absolute():
        source_root = repo_root / source_root

    manifest = read_json(manifest_path)
    sources = manifest.get("sources", {})
    if not isinstance(sources, dict) or not sources:
        raise SystemExit("Manifest has no 'sources' entries.")

    print(f"Using manifest: {manifest_path}")
    print(f"Source root: {source_root}")
    source_root.mkdir(parents=True, exist_ok=True)

    for source_name, source_cfg in sources.items():
        if not isinstance(source_cfg, dict):
            continue
        acquisition = str(source_cfg.get("acquisition", "")).strip()
        redistribution = str(source_cfg.get("redistribution", "")).strip()
        local_subdir = str(source_cfg.get("local_subdir", "")).strip()
        if not local_subdir:
            raise SystemExit(f"Source '{source_name}' is missing local_subdir.")
        dest = source_root / local_subdir

        if acquisition not in {"git-clone", "manual-clone"}:
            print(f"[skip] {source_name}: unsupported acquisition '{acquisition}'")
            continue
        if redistribution == "reference-only" and not args.include_reference_only:
            print(
                f"[skip] {source_name}: reference-only source. "
                "Use --include-reference-only after confirming policy."
            )
            continue

        print(f"[fetch] {source_name} -> {dest}")
        clone_or_update(source_name, source_cfg, dest)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

