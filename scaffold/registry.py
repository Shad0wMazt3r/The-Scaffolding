import json
import logging
from pathlib import Path
from scaffold.env import load_env, resolve_dict
# We import sync_to_all_agents locally to avoid circular dependencies if needed

logger = logging.getLogger(__name__)

def get_registry_path() -> Path:
    return Path(__file__).parent.parent / 'mcps.json'

def load_registry(resolve: bool = False) -> dict:
    """Loads mcps.json. If resolve=True, resolves env vars."""
    path = get_registry_path()
    if not path.exists():
        return {"version": 1, "servers": {}}
    
    with path.open('r') as f:
        data = json.load(f)
        
    if resolve:
        load_env()
        data = resolve_dict(data)
        
    return data

def save_registry(data: dict):
    with get_registry_path().open('w') as f:
        json.dump(data, f, indent=2)

def list_servers() -> dict:
    data = load_registry(resolve=True)
    return data.get("servers", {})

def add_server(name: str, entry: dict):
    from scaffold.config import sync_to_all_agents
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
    sync_to_all_agents(data.get("servers", {}), specific_agent=agent)
