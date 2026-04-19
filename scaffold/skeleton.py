import shutil
from pathlib import Path

def setup_project(project_dir: str):
    p = Path(project_dir)
    p.mkdir(parents=True, exist_ok=True)
    
    # Copy from repo root to project dir
    repo_root = Path(__file__).parent.parent
    agents_dir = repo_root / '.agents'
    dest_agents = p / '.agents'
    
    if agents_dir.exists() and not dest_agents.exists():
        shutil.copytree(agents_dir, dest_agents)
        
    for f in ["HUMAN.md", "AGENTS.md"]:
        src = repo_root / f
        dest = p / f
        if src.exists() and not dest.exists():
            shutil.copy2(src, dest)
