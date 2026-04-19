import subprocess
import os
import shutil
from pathlib import Path
from .models import build_model_arg
from .sessions import record_session

AGENT_COMMANDS = {
    "gemini": "gemini",
    "cursor": "cursor",
    "cursor agent": "cursor-agent",
    "opencode": "opencode",
    "codex": "codex",
    "claude": "claude",
    "copilot": "copilot",
}


def check_agent_available(agent: str) -> tuple[bool, str]:
    cmd = AGENT_COMMANDS.get(agent)
    if not cmd:
        if agent == "antigravity":
            return True, "IDE-based launch"
        return False, f"Unknown agent: {agent}"
    if shutil.which(cmd):
        return True, cmd
    return False, f"Required command not found in PATH: {cmd}"


def build_launch_command(agent: str, model_args: list[str]) -> list[str] | None:
    if agent == "gemini":
        return ["gemini"] + model_args
    if agent == "cursor":
        return ["cursor", "."] + model_args
    if agent == "cursor agent":
        return ["cursor-agent"] + model_args
    if agent == "opencode":
        return ["opencode", "."] + model_args
    if agent == "codex":
        return ["codex", "--cd", "."] + model_args
    if agent == "claude":
        return ["claude"] + model_args
    if agent == "copilot":
        return ["copilot"] + model_args
    return None


def launch_agent(agent: str, project_dir: str, model: str = None):
    # Change working directory
    p = Path(project_dir).absolute()
    os.chdir(p)
    
    model_args = build_model_arg(agent, model)
    ok, detail = check_agent_available(agent)
    if not ok:
        print(f"Error: {detail}")
        return False
     
    if agent == "antigravity":
        print(f"\n[Antigravity] Please open this folder directly in the IDE:")
        print(f"Path: {p}")
        record_session(agent, str(p), model)
        return True

    cmd = build_launch_command(agent, model_args)
    if not cmd:
        print(f"Unknown agent: {agent}")
        return False

    record_session(agent, str(p), model)
         
    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, shell=(os.name == 'nt'))
        return True
    except FileNotFoundError:
        print(f"Error: Command '{cmd[0]}' not found. Is {agent} installed?")
        return False
