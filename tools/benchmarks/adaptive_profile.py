#!/usr/bin/env python3
"""Adaptive profile selection helpers for vuln benchmark runs."""

from __future__ import annotations

from typing import Iterable


def _norm(model: str) -> str:
    return (model or "").strip().lower()


def model_family(model: str) -> str:
    m = _norm(model)
    if "gemini" in m:
        return "gemini"
    if "kimi" in m:
        return "kimi"
    if "claude" in m or "sonnet" in m or "opus" in m or "haiku" in m:
        return "anthropic"
    if "gpt" in m or "codex" in m:
        return "openai"
    return "other"


def baseline_strength(model: str) -> str:
    """Heuristic strength buckets from model naming conventions."""
    m = _norm(model)
    if any(x in m for x in ["nano", "mini-low", "codex-mini-low", "flash-lite"]):
        return "low"
    if any(x in m for x in ["mini-high", "mini-medium", "sonnet", "opus", "pro"]):
        return "high"
    return "medium"


def chain_ratio(tasks: Iterable[dict]) -> float:
    rows = list(tasks)
    if not rows:
        return 0.0
    chained = sum(1 for t in rows if bool(t.get("chain_required", False)))
    return chained / len(rows)


def choose_profile(requested_profile: str, model: str, tasks: Iterable[dict]) -> tuple[str, str]:
    """Return (resolved_profile, reason)."""
    if requested_profile != "adaptive":
        return requested_profile, "explicit profile requested"

    family = model_family(model)
    strength = baseline_strength(model)
    c_ratio = chain_ratio(tasks)
    chain_heavy = c_ratio >= 0.15

    if family == "gemini":
        if chain_heavy:
            return "control", f"gemini + chain-heavy tasks ({c_ratio:.2f}) favors control"
        return "skills-lite", "gemini favors light scaffolding on non-chain-heavy tasks"
    if family == "kimi":
        return "control", "kimi defaults to control due observed FP pressure under full skills"
    if strength == "high":
        return "skills-lite", "high baseline strength prefers lighter scaffolding"
    if strength == "low":
        return "skills-only", "low baseline strength benefits from full skills structure"
    return "skills-lite", "medium baseline defaults to skills-lite"

