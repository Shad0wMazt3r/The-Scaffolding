import subprocess
import shlex
from pathlib import Path

def install_source(name: str, source_cfg: dict):
    if not source_cfg:
        return
    git_url = source_cfg.get("git")
    local_path = source_cfg.get("localPath")
    install_cmd = source_cfg.get("install")
    
    if not git_url or not local_path:
        return
        
    p = Path(local_path)
    if p.exists() and p.is_dir():
        return # Already installed
        
    p.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(["git", "clone", git_url, str(p)], check=True, timeout=300)
        if install_cmd:
            cmd_parts = shlex.split(install_cmd)
            subprocess.run(cmd_parts, cwd=str(p), check=True, timeout=600)
        print(f"Installed source for {name}: {p}")
    except subprocess.CalledProcessError as e:
        print(f"Install failed for {name}: {e}")
    except subprocess.TimeoutExpired:
        print(f"Install timed out for {name}")

def run_installs(servers: dict):
    from scaffold.env import resolve_dict
    resolved = resolve_dict(servers)
    for name, entry in resolved.items():
        install_source(name, entry.get("source", {}))
