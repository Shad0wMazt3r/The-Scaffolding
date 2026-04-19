import os
import re
from pathlib import Path

TEMPLATE_RE = re.compile(r"\$\{([^}]+)\}")


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
        return value[1:-1]
    return value


def load_env(path: Path | None = None, override: bool = True) -> list[str]:
    """Load .env key-values into os.environ and return loaded keys."""
    env_path = path or (Path(__file__).parent.parent / ".env")
    if not env_path.exists():
        return []

    loaded: list[str] = []
    with env_path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            val = _strip_quotes(val.strip())
            if override or key not in os.environ:
                os.environ[key] = val
            loaded.append(key)
    return loaded


def resolve_template(value: str, *, missing: set[str] | None = None, strict: bool = False) -> str:
    """Resolve ${VAR} placeholders using os.environ."""
    if not isinstance(value, str):
        return value

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        resolved = os.environ.get(key)
        if resolved is None:
            if missing is not None:
                missing.add(key)
            if strict:
                raise KeyError(f"Missing environment variable: {key}")
            return match.group(0)
        return resolved

    return TEMPLATE_RE.sub(_replace, value)


def has_unresolved_templates(value: str) -> bool:
    return bool(isinstance(value, str) and TEMPLATE_RE.search(value))


def resolve_dict(data: object, *, missing: set[str] | None = None, strict: bool = False) -> object:
    """Recursively resolve ${VAR} placeholders in nested dict/list structures."""
    if isinstance(data, dict):
        return {k: resolve_dict(v, missing=missing, strict=strict) for k, v in data.items()}
    if isinstance(data, list):
        return [resolve_dict(v, missing=missing, strict=strict) for v in data]
    if isinstance(data, str):
        return resolve_template(data, missing=missing, strict=strict)
    return data
