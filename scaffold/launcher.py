import subprocess
import os
from pathlib import Path
from .models import build_model_arg
from .sessions import record_session

def launch_agent(agent: str, project_dir: str, model: str = None):
    # Change working directory
    p = Path(project_dir).absolute()
    os.chdir(p)
    
    model_args = build_model_arg(agent, model)
    record_session(agent, str(p), model)
    
    if agent == "gemini":
        cmd = ["gemini"] + model_args
    elif agent == "cursor":
        cmd = ["cursor", "."] + model_args
    elif agent == "cursor agent":
        cmd = ["cursor-agent"] + model_args
    elif agent == "opencode":
        cmd = ["opencode", "."] + model_args
    elif agent == "codex":
        cmd = ["codex", "--cd", "."] + model_args
    elif agent == "claude":
        cmd = ["claude"] + model_args
    elif agent == "copilot":
        cmd = ["copilot"] + model_args
    elif agent == "antigravity":
        print(f"\n[Antigravity] Please open this folder directly in the IDE:")
        print(f"Path: {p}")
        return
    else:
        print(f"Unknown agent: {agent}")
        return
        
    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print(f"Error: Command '{cmd[0]}' not found. Is {agent} installed?")
