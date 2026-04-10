# Notes for human
## Agent Runtime Matrix
- Gemini CLI: `AGENTS.md` is auto-loaded via `.gemini/settings.json`; all skills load from `.agents/skills/*`.
- Cursor: Added `.cursor/skills/bug-hunt-framework/SKILL.md` for quick routing; existing `.agents/skills/*` remain the canonical skill content.
- Copilot CLI: Added `.github/agents/bug-hunt-framework.agent.md`; also supports project instructions from `AGENTS.md` and `.github/copilot-instructions.md` style files if present.
- Codex CLI: Reads root `AGENTS.md` directly by default with inheritance rules.
- OpenCode: Reads `AGENTS.md` via instructions and optional `.opencode/opencode.json`; added `.opencode/agents/bug-hunt-framework.md` and `.opencode/opencode.json`.

## Launch Commands
- Gemini CLI: `gemini`
- Cursor: Open Agent chat and use `@bug-hunt-framework` or `/bug-hunt-framework`
- Copilot CLI: `copilot --agent bug-hunt-framework`
- Codex: `codex`
- OpenCode: `opencode`
