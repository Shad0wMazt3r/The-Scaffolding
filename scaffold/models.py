MODELS = {
    "gemini":   [("Auto (default)", "auto"), ("Pro", "pro"), ("Flash", "flash"), ("Flash-Lite", "flash-lite")],
    "opencode": [("Claude Sonnet 4.5", "anthropic/claude-sonnet-4-5"), ("Claude Opus 4", "anthropic/claude-opus-4"), ("GPT-4o", "openai/gpt-4o"), ("GPT-5", "openai/gpt-5")],
    "codex":    [("GPT-4o (default)", "gpt-4o"), ("o3", "o3"), ("o4-mini", "o4-mini"), ("gpt-5.4", "gpt-5.4")],
    "claude":   [("Sonnet (default)", "sonnet"), ("Opus", "opus"), ("Haiku", "haiku")],
    "cursor":   [],
    "cursor agent": [("Claude 4.5 Sonnet", "claude-4.5-sonnet"), ("Claude Opus 4", "claude-opus-4"), ("Gemini 3 Pro", "gemini-3-pro")],
    "copilot":  [("Claude Sonnet 4.5", "claude-sonnet-4.5"), ("GPT-5", "gpt-5")],
    "antigravity": []
}

import subprocess
import shutil

import re

def get_models_for_agent(agent: str):
    cmd_name = "cursor-agent" if agent == "cursor agent" else agent
    cmd_path = shutil.which(cmd_name + ".cmd") or shutil.which(cmd_name + ".bat") or shutil.which(cmd_name)
    
    if cmd_path:
        try:
            help_res = subprocess.run([cmd_path, "--help"], capture_output=True, text=True, timeout=5)
            help_text = help_res.stdout + help_res.stderr
            
            if re.search(r'--models\b|\bmodels\b', help_text):
                # Try `models` subcommand first
                res = subprocess.run([cmd_path, "models"], capture_output=True, text=True, timeout=10)
                if res.returncode == 0 and res.stdout.strip():
                    lines = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]
                    parsed = [(line, line) for line in lines if re.match(r'^[\w\.\-/]+$', line)]
                    if parsed:
                        return parsed
                        
                # Try `--models` argument as fallback
                res2 = subprocess.run([cmd_path, "--models"], capture_output=True, text=True, timeout=10)
                if res2.returncode == 0 and res2.stdout.strip():
                    lines = [line.strip() for line in res2.stdout.strip().split("\n") if line.strip()]
                    parsed = [(line, line) for line in lines if re.match(r'^[\w\.\-/]+$', line)]
                    if parsed:
                        return parsed
        except Exception:
            pass

    return MODELS.get(agent, [])

def build_model_arg(agent: str, model_id: str):
    if not model_id:
        return []
    if agent in ["gemini", "opencode", "codex", "claude", "copilot", "cursor agent"]:
        return ["--model", model_id]
    return []
