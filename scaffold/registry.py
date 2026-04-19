import json
import logging
from pathlib import Path
from scaffold.env import load_env, resolve_dict
# We import sync_to_all_agents locally to avoid circular dependencies if needed

logger = logging.getLogger(__name__)
ALLOWED_TRANSPORTS = {"http", "sse", "stdio"}
ALLOWED_HEALTH_TYPES = {"http", "docker-image", "bridge-path"}

def get_registry_path() -> Path:
    return Path(__file__).parent.parent / 'mcps.json'

def load_registry(resolve: bool = False) -> dict:
    """Loads mcps.json. If resolve=True, resolves env vars."""
    path = get_registry_path()
    if not path.exists():
        return {"version": 1, "servers": {}}
    
    try:
        with path.open('r', encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in MCP registry {path}: {exc}") from exc
        
    if resolve:
        load_env()
        data = resolve_dict(data)
        
    return data

def save_registry(data: dict):
    with get_registry_path().open('w', encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _validate_server_entry(name: str, entry: dict) -> None:
    if not isinstance(entry, dict):
        raise ValueError(f"MCP '{name}' entry must be an object")

    transports = entry.get("transports")
    if not isinstance(transports, dict) or not transports:
        raise ValueError(f"MCP '{name}' requires non-empty transports")
    unknown = set(transports.keys()) - ALLOWED_TRANSPORTS
    if unknown:
        raise ValueError(f"MCP '{name}' has unsupported transports: {', '.join(sorted(unknown))}")

    for transport, cfg in transports.items():
        if not isinstance(cfg, dict):
            raise ValueError(f"MCP '{name}' transport '{transport}' must be an object")
        if transport in {"http", "sse"} and not cfg.get("url"):
            raise ValueError(f"MCP '{name}' transport '{transport}' requires 'url'")
        if transport == "stdio" and not cfg.get("command"):
            raise ValueError(f"MCP '{name}' transport 'stdio' requires 'command'")

    default_transport = entry.get("defaultTransport")
    if default_transport and default_transport not in transports:
        raise ValueError(
            f"MCP '{name}' defaultTransport '{default_transport}' missing from transports"
        )

    health = entry.get("health", {})
    if health and not isinstance(health, dict):
        raise ValueError(f"MCP '{name}' health must be an object")
    health_type = health.get("type")
    if health_type and health_type not in ALLOWED_HEALTH_TYPES:
        raise ValueError(f"MCP '{name}' health.type '{health_type}' is not supported")

def list_servers() -> dict:
    data = load_registry(resolve=True)
    return data.get("servers", {})

def add_server(name: str, entry: dict):
    from scaffold.config import sync_to_all_agents
    _validate_server_entry(name, entry)
    data = load_registry(resolve=False)
    if "servers" not in data:
        data["servers"] = {}
    data["servers"][name] = entry
    save_registry(data)
    sync_to_all_agents(data["servers"])

def remove_server(name: str):
    from scaffold.config import sync_to_all_agents
    data = load_registry(resolve=False)
    if "servers" in data and name in data["servers"]:
        del data["servers"][name]
        save_registry(data)
        sync_to_all_agents(data["servers"])

def sync(agent: str = None):
    from scaffold.config import sync_to_all_agents
    data = load_registry(resolve=False)
    for name, entry in data.get("servers", {}).items():
        _validate_server_entry(name, entry)
    sync_to_all_agents(data.get("servers", {}), specific_agent=agent)
