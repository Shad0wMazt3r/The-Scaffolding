import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def deep_merge(dict1, dict2):
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1 and isinstance(dict1[key], dict):
            deep_merge(dict1[key], value)
        else:
            dict1[key] = value

def load_json(path):
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return {}
    try:
        with path.open('r', encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file: {path} ({exc})") from exc

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _contains_unresolved_env(value: Any) -> bool:
    if isinstance(value, str):
        return "${" in value and "}" in value
    if isinstance(value, dict):
        return any(_contains_unresolved_env(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_unresolved_env(v) for v in value)
    return False

def to_gemini(name: str, entry: dict) -> dict:
    transports = entry.get("transports", {})
    if "http" in transports:
        return {"serverUrl": transports["http"]["url"], "headers": entry.get("headers", {})}
    elif "stdio" in transports:
        return {"command": transports["stdio"]["command"], "args": transports["stdio"].get("args", []), "env": transports["stdio"].get("env", {})}
    elif "sse" in transports:
        return {"serverUrl": transports["sse"]["url"], "headers": entry.get("headers", {})}
    return {}

def to_cursor(name: str, entry: dict) -> dict:
    transports = entry.get("transports", {})
    if "sse" in transports:
        return {"type": "sse", "url": transports["sse"]["url"]}
    elif "stdio" in transports:
        return {"type": "command", "command": transports["stdio"]["command"], "args": transports["stdio"].get("args", []), "env": transports["stdio"].get("env", {})}
    elif "http" in transports:
        return {"type": "sse", "url": transports["http"]["url"]} # fallback
    return {}

def to_opencode(name: str, entry: dict) -> dict:
    transports = entry.get("transports", {})
    if "http" in transports or "sse" in transports:
        url = transports.get("http", {}).get("url") or transports.get("sse", {}).get("url")
        return {"type": "remote", "url": url}
    elif "stdio" in transports:
        return {"type": "local", "command": transports["stdio"]["command"], "args": transports["stdio"].get("args", []), "env": transports["stdio"].get("env", {})}
    return {}
    
def to_codex(name: str, entry: dict) -> dict:
    transports = entry.get("transports", {})
    if "stdio" in transports:
        return {"type": "stdio", "command": transports["stdio"]["command"], "args": transports["stdio"].get("args", []), "env": transports["stdio"].get("env", {})}
    elif "http" in transports or "sse" in transports:
        url = transports.get("http", {}).get("url") or transports.get("sse", {}).get("url")
        return {"type": "http", "url": url}
    return {}

def to_claude(name: str, entry: dict) -> dict:
    transports = entry.get("transports", {})
    if "stdio" in transports:
        return {"command": transports["stdio"]["command"], "args": transports["stdio"].get("args", []), "env": transports["stdio"].get("env", {})}
    return {"command": "npx", "args": ["-y", "mcp-remote", transports.get("sse", {}).get("url", "")]} if "sse" in transports else {}

def to_antigravity(name: str, entry: dict) -> dict:
    transports = entry.get("transports", {})
    if "http" in transports or "sse" in transports:
        url = transports.get("http", {}).get("url") or transports.get("sse", {}).get("url")
        return {"serverUrl": url, "headers": entry.get("headers", {})}
    elif "stdio" in transports:
        return {"command": transports["stdio"]["command"], "args": transports["stdio"].get("args", []), "env": transports["stdio"].get("env", {})}
    return {}

TRANSLATORS = {
    "gemini": to_gemini,
    "cursor": to_cursor,
    "opencode": to_opencode,
    "codex": to_codex,
    "claude": to_claude,
    "antigravity": to_antigravity
}
CONFIG_PATHS = {
    "gemini": ".gemini/settings.json",
    "cursor": ".cursor/mcp.json",
    "opencode": ".opencode/opencode.json",
    "codex": ".codex/mcp.json",
    "claude": "claude.json", 
    "antigravity": ".antigravity/mcp_config.json"
}

def sync_to_all_agents(registry_servers: dict, specific_agent: str = None):
    from scaffold.env import resolve_dict, load_env
    load_env()
    missing_env: set[str] = set()
    resolved_servers = resolve_dict(registry_servers, missing=missing_env)
    if missing_env:
        logger.warning("Missing env vars while syncing MCP config: %s", ", ".join(sorted(missing_env)))
    
    agents = [specific_agent] if specific_agent else TRANSLATORS.keys()
    base_dir = Path.cwd()
    
    for agent in agents:
        if agent not in TRANSLATORS:
            continue
        translator = TRANSLATORS[agent]
        path = base_dir / CONFIG_PATHS[agent]
        
        mcp_block = {}
        for name, entry in resolved_servers.items():
            if _contains_unresolved_env(entry):
                logger.warning("Skipping MCP '%s' due to unresolved env placeholders", name)
                continue
            translated = translator(name, entry)
            if translated:
                mcp_block[name] = translated
        
        if not mcp_block:
            continue
            
        config = load_json(path)
        if agent == "opencode":
            config["mcp"] = dict(mcp_block)
        elif agent == "codex":
            if "mcp" not in config or not isinstance(config.get("mcp"), dict):
                config["mcp"] = {}
            config["mcp"]["servers"] = dict(mcp_block)
        else:
            config["mcpServers"] = dict(mcp_block)
        
        save_json(path, config)
