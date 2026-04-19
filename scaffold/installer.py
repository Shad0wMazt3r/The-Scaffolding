import subprocess
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
        subprocess.run(["git", "clone", git_url, str(p)], check=True)
        if install_cmd:
            subprocess.run(install_cmd, shell=True, cwd=str(p), check=True)
    except subprocess.CalledProcessError as e:
        print(f"Install failed for {name}: {e}")

def run_installs(servers: dict):
    from scaffold.env import resolve_dict
    resolved = resolve_dict(servers)
    for name, entry in resolved.items():
        install_source(name, entry.get("source", {}))
