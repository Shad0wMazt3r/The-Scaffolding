import json
import uuid
from datetime import datetime
from pathlib import Path

def get_sessions_path() -> Path:
    return Path(__file__).parent.parent / 'sessions.json'

def load_sessions() -> list:
    p = get_sessions_path()
    if not p.exists():
        return []
    try:
        with p.open('r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_sessions(sessions: list):
    p = get_sessions_path()
    with p.open('w') as f:
        json.dump(sessions, f, indent=2)

def record_session(agent: str, project_dir: str, model: str, native_id: str = None):
    sessions = load_sessions()
    sess = {
        "id": str(uuid.uuid4()),
        "agent": agent,
        "project": project_dir,
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "native_id": native_id
    }
    sessions.insert(0, sess)
    save_sessions(sessions)
    return sess['id']

def delete_session(session_id: str):
    sessions = load_sessions()
    sessions = [s for s in sessions if s["id"] != session_id]
    save_sessions(sessions)

def get_resume_command(agent: str, session: dict) -> list:
    native_id = session.get("native_id") or session.get("id")
    if agent == "opencode":
        return ["opencode", "--session", native_id]
    elif agent == "claude":
        return ["claude", "--resume", native_id]
    elif agent == "codex":
        return ["codex", "resume", native_id]
    elif agent == "copilot":
        return ["copilot", "--resume"]
    elif agent == "cursor":
        return ["cursor", session["project"]]
    return None
