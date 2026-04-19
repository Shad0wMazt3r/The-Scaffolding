import os
import re
from pathlib import Path

def load_env():
    """Loads .env file from the repo root into os.environ."""
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        return
    with env_path.open('r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

def resolve_template(value: str) -> str:
    """Resolves ${VAR} in a string using os.environ."""
    if not isinstance(value, str):
        return value
    return re.sub(
        r'\$\{([^}]+)\}',
        lambda m: os.environ.get(m.group(1), f'${{{m.group(1)}}}'),
        value
    )

def resolve_dict(data: dict) -> dict:
    """Recursively resolves ${VAR} in all string values."""
    if isinstance(data, dict):
        return {k: resolve_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_dict(v) for v in data]
    elif isinstance(data, str):
        return resolve_template(data)
    return data
