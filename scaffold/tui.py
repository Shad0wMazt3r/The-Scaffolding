from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from scaffold.registry import list_servers, add_server, remove_server, sync
from scaffold.health import check_all
from scaffold.installer import run_installs
from scaffold.models import get_models_for_agent, MODELS
from scaffold.sessions import load_sessions, get_resume_command, delete_session
from scaffold.skeleton import setup_project
from scaffold.launcher import launch_agent
import os
import subprocess

console = Console()

def render_header(active_tab):
    tabs = ["Init Agent", "Manage MCPs", "Sessions"]
    tab_str = " │ ".join([f"[bold cyan]{t}[/]" if t == active_tab else t for t in tabs])
    console.print(Panel(f"🛡  The Scaffolding  │ {tab_str}", expand=False))

def tui_init():
    console.clear()
    render_header("Init Agent")
    agents = list(MODELS.keys())
    agent_str = "  ".join([f"[{i}] {a}" for i, a in enumerate(agents)])
    console.print(f"Available Agents: {agent_str}\n")
    idx = Prompt.ask("Select Agent Index", default="0")
    try:
        agent = agents[int(idx)]
    except ValueError:
        agent = agents[0]
        
    models = get_models_for_agent(agent)
    model_id = None
    if models:
        model_str = " | ".join([f"[{i}] {m[0]}" for i, m in enumerate(models)])
        console.print(f"\nModels: {model_str}")
        midx = Prompt.ask("Select Model", default="0")
        try:
            model_id = models[int(midx)][1]
        except ValueError:
            model_id = models[0][1]
    
    project = Prompt.ask("\nProject Directory", default="./my-ctf")
    launch = Confirm.ask(f"Init {agent} in {project}?", default=True)
    if launch:
        setup_project(project)
        console.print("[green]Running pre-flight checks![/]")
        servers = list_servers()
        run_installs(servers)
        launch_agent(agent, project, model_id)
        Prompt.ask("Press Enter to return")

def tui_mcps():
    while True:
        console.clear()
        render_header("Manage MCPs")
        servers = list_servers()
        results = check_all(servers)
        
        table = Table(title="Registered MCPs")
        table.add_column("NAME", style="cyan")
        table.add_column("TRANSPORT", style="magenta")
        table.add_column("HEALTH")
        
        for r in results:
            entry = servers[r.name]
            transport = entry.get("defaultTransport", list(entry.get("transports", {}).keys())[0] if entry.get("transports") else "unknown")
            icon = "✅" if r.status == "up" else ("⚠️" if r.warn_only else "❌")
            table.add_row(r.name, transport, f"{icon} {r.message}")
            
        console.print(table)
        
        action = Prompt.ask("Action", choices=["add", "remove", "sync", "back"], default="back")
        if action == "add":
            name = Prompt.ask("Name")
            desc = Prompt.ask("Description")
            trans = Prompt.ask("Transport", choices=["http", "sse", "stdio"], default="http")
            if trans in ["http", "sse"]:
                url = Prompt.ask("URL", default="http://localhost:8000")
                entry = {"description": desc, "transports": {trans: {"url": url}}, "health": {"type": "http", "warnOnly": False}}
            else:
                cmd = Prompt.ask("Command")
                entry = {"description": desc, "transports": {trans: {"command": cmd, "args": []}}, "health": {"warnOnly": False}}
            
            warn = Confirm.ask("Warn-only on health check?", default=False)
            entry["health"]["warnOnly"] = warn
            
            if Confirm.ask("Add Git source config?", default=False):
                git_url = Prompt.ask("Git URL")
                local_path = Prompt.ask("Local Path (e.g. C:\\Tools\\MyTool)")
                install_cmd = Prompt.ask("Install Command (e.g. pip install -r requirements.txt)")
                entry["source"] = {
                    "git": git_url,
                    "localPath": local_path,
                    "install": install_cmd
                }
                
            add_server(name, entry)
            console.print("[green]Added and synced![/green]")
            Prompt.ask("Press Enter to continue")
        elif action == "remove":
            name = Prompt.ask("Name to remove")
            remove_server(name)
            console.print("[green]Removed and synced![/green]")
            Prompt.ask("Press Enter to continue")
        elif action == "sync":
            sync()
            console.print("[green]Synced to all agents![/green]")
            Prompt.ask("Press Enter to continue")
        elif action == "back":
            break

def tui_sessions():
    while True:
        console.clear()
        render_header("Sessions")
        sess_list = load_sessions()
        
        table = Table(title="Recent Sessions")
        table.add_column("#", style="cyan")
        table.add_column("AGENT")
        table.add_column("MODEL")
        table.add_column("PROJECT")
        table.add_column("STARTED")
        
        for i, s in enumerate(sess_list):
            model_str = s.get("model") or "default"
            table.add_row(str(i), s.get("agent"), model_str, s.get("project"), s.get("timestamp")[:16])
            
        console.print(table)
        
        action = Prompt.ask("Action", choices=["resume", "delete", "back"], default="back")
        if action == "resume":
            idx = Prompt.ask("Session Number")
            try:
                s_to_resume = sess_list[int(idx)]
                cmd = get_resume_command(s_to_resume["agent"], s_to_resume)
                if not cmd:
                    console.print(f"[yellow]{s_to_resume['agent']} doesn't support resuming. Launching normally in dir.[/yellow]")
                    launch_agent(s_to_resume["agent"], s_to_resume["project"], s_to_resume.get("model"))
                else:
                    os.chdir(s_to_resume["project"])
                    console.print(f"Executing: {' '.join(cmd)}")
                    subprocess.run(cmd)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            Prompt.ask("Press Enter to continue")
                
        elif action == "delete":
            idx = Prompt.ask("Session Number")
            try:
                sid = sess_list[int(idx)]["id"]
                delete_session(sid)
            except Exception:
                pass
        elif action == "back":
            break

def run_tui(start_tab="Init"):
    while True:
        console.clear()
        render_header("Main")
        console.print("\n[1] Init Agent\n[2] Manage MCPs\n[3] Sessions\n[q] Quit")
        choice = Prompt.ask("Select", choices=["1", "2", "3", "q"])
        if choice == "1":
            tui_init()
        elif choice == "2":
            tui_mcps()
        elif choice == "3":
            tui_sessions()
        elif choice == "q":
            break
