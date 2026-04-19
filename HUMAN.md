# Notes for human
## Agent Runtime Matrix
- Gemini CLI: `AGENTS.md` is auto-loaded via `.gemini/settings.json`; all skills load from `.agents/skills/*`.
- Cursor: Added `.cursor/skills/bug-hunt-framework/SKILL.md` for quick routing; existing `.agents/skills/*` remain the canonical skill content. Run with `agent --approve-mcps --force`
- Copilot CLI: Added `.github/agents/bug-hunt-framework.agent.md`; also supports project instructions from `AGENTS.md` and `.github/copilot-instructions.md` style files if present.
- Codex CLI: Reads root `AGENTS.md` directly by default with inheritance rules.
- OpenCode: Reads `AGENTS.md` via instructions and optional `.opencode/opencode.json`; added `.opencode/agents/bug-hunt-framework.md` and `.opencode/opencode.json`.

## Launch & Orchestration
You should use the unified `scaffold.py` script to manage and launch agents:

```bash
# Launch interactive TUI
python scaffold.py

# CLI alternatives
python scaffold.py init --agent gemini --project ./my-target
python scaffold.py mcp sync
```

Alternatively, direct launch commands:
- Gemini CLI: `gemini`
- Cursor: `cursor <project-dir>` or `cursor-agent`
- Copilot CLI: `copilot`
- Codex: `codex`
- OpenCode: `opencode`
- Claude: `claude`
- Antigravity: Open the project folder via the VS Code fork / Antigravity app natively.
