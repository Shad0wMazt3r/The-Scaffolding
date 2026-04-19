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

def get_models_for_agent(agent: str):
    return MODELS.get(agent, [])

def build_model_arg(agent: str, model_id: str):
    if not model_id:
        return []
    if agent in ["gemini", "opencode", "codex", "claude", "copilot", "cursor agent"]:
        return ["--model", model_id]
    return []
