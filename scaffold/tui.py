import os
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm

from pyratatui import (
    Block, Color, Constraint, Direction, Layout, Paragraph, Style, Table, Row,
    Terminal, Tabs, List, ListItem, ListState, TableState
)

from scaffold.registry import list_servers, add_server, remove_server, sync
from scaffold.health import check_all
from scaffold.installer import run_installs
from scaffold.models import get_models_for_agent, MODELS
from scaffold.sessions import load_sessions, get_resume_command, delete_session
from scaffold.skeleton import setup_project
from scaffold.launcher import launch_agent, check_agent_available, build_launch_command

console = Console()

def run_tui(start_tab="Init"):
    tab_index = 0
    if start_tab.lower() == "mcp": tab_index = 1
    elif start_tab.lower() == "sessions": tab_index = 2

    mcp_table_state = TableState()
    mcp_table_state.select(0)
    
    sess_table_state = TableState()
    sess_table_state.select(0)
    
    agent_list_state = ListState()
    agent_list_state.select(0)

    # Cache for heavy ops
    cache = {
        "mcp_results": [],
        "servers": {},
        "agents": list(MODELS.keys()) if MODELS else [],
        "sess_list": []
    }
    needs_refresh = True

    while True:
        action = None
        action_data = {}

        with Terminal() as term:
            while True:
                if needs_refresh:
                    cache["servers"] = list_servers()
                    cache["sess_list"] = load_sessions()
                    if tab_index == 1:
                        # Only check health when on MCP tab
                        cache["mcp_results"] = check_all(cache["servers"])
                    needs_refresh = False

                def ui(frame):
                    chunks = (
                        Layout()
                        .direction(Direction.Vertical)
                        .constraints([
                            Constraint.length(3),
                            Constraint.fill(1),
                            Constraint.length(3)
                        ])
                        .split(frame.area)
                    )
                    
                    # Header
                    tabs = Tabs(["1: Init Agent", "2: Manage MCPs", "3: Sessions"]) \
                        .select(tab_index) \
                        .block(Block().bordered().title("🛡  The Scaffolding")) \
                        .highlight_style(Style().fg(Color.cyan()).bold())
                    frame.render_widget(tabs, chunks[0])
                    
                    if tab_index == 0:
                        items = [ListItem(a) for a in cache["agents"]]
                        l = List(items).block(Block().bordered().title("Select Agent")) \
                            .highlight_style(Style().fg(Color.yellow()).bold()) \
                            .highlight_symbol("▶ ")
                        frame.render_stateful_list(l, chunks[1], agent_list_state)
                        footer_text = "Arrows: Navigate | Enter: Select | 1-3: Switch Tab | q: Quit"
                        
                    elif tab_index == 1:
                        header = Row.from_strings(["NAME", "TRANSPORT", "HEALTH"]).style(Style().fg(Color.cyan()).bold())
                        t_rows = []
                        if cache["mcp_results"]:
                            for r in cache["mcp_results"]:
                                entry = cache["servers"].get(r.name, {})
                                transport = entry.get("defaultTransport", list(entry.get("transports", {}).keys())[0] if entry.get("transports") else "unknown")
                                icon = "✅" if r.status == "up" else ("⚠️" if getattr(r, 'warn_only', False) else "❌")
                                t_rows.append(Row.from_strings([str(r.name), str(transport), f"{icon} {r.message}"]))
                        else:
                            for name, entry in cache["servers"].items():
                                transport = entry.get("defaultTransport", list(entry.get("transports", {}).keys())[0] if entry.get("transports") else "unknown")
                                t_rows.append(Row.from_strings([str(name), str(transport), "❓ checking..."]))

                        t = Table(t_rows).column_widths([Constraint.percentage(30), Constraint.percentage(20), Constraint.percentage(50)]).header(header) \
                            .block(Block().bordered().title("Registered MCPs")) \
                            .highlight_style(Style().fg(Color.yellow()).bold()) \
                            .highlight_symbol("▶ ")
                        frame.render_stateful_table(t, chunks[1], mcp_table_state)
                        footer_text = "Arrows: Navigate | a: Add | r: Remove | s: Sync | 1-3: Switch Tab | q: Quit"
                        
                    elif tab_index == 2:
                        header = Row.from_strings(["AGENT", "MODEL", "PROJECT", "STARTED"]).style(Style().fg(Color.cyan()).bold())
                        t_rows = []
                        for s in cache["sess_list"]:
                            model_str = s.get("model") or "default"
                            t_rows.append(Row.from_strings([str(s.get("agent", "")), str(model_str), str(s.get("project", "")), str(s.get("timestamp", ""))[:16]]))
                        
                        t = Table(t_rows).column_widths([Constraint.percentage(20), Constraint.percentage(20), Constraint.percentage(40), Constraint.percentage(20)]).header(header) \
                            .block(Block().bordered().title("Recent Sessions")) \
                            .highlight_style(Style().fg(Color.yellow()).bold()) \
                            .highlight_symbol("▶ ")
                        frame.render_stateful_table(t, chunks[1], sess_table_state)
                        footer_text = "Arrows: Navigate | Enter: Resume | d: Delete | 1-3: Switch Tab | q: Quit"
                    
                    frame.render_widget(Paragraph.from_string(footer_text).block(Block().bordered()), chunks[2])

                term.draw(ui)
                ev = term.poll_event(100)
                if not ev: continue
                
                if ev.code == "1" and tab_index != 0: 
                    tab_index = 0
                    needs_refresh = True
                elif ev.code == "2" and tab_index != 1: 
                    tab_index = 1
                    needs_refresh = True
                elif ev.code == "3" and tab_index != 2: 
                    tab_index = 2
                    needs_refresh = True
                elif ev.code == "q" or (ev.code == "c" and ev.ctrl): 
                    action = "quit"
                    break
                elif ev.code == "Down" or ev.code == "j":
                    if tab_index == 0:
                        idx = agent_list_state.selected or 0
                        agent_list_state.select(min(idx + 1, len(cache["agents"]) - 1))
                    elif tab_index == 1:
                        idx = mcp_table_state.selected or 0
                        max_idx = max(0, len(cache["mcp_results"] if cache["mcp_results"] else cache["servers"]) - 1)
                        mcp_table_state.select(min(idx + 1, max_idx))
                    elif tab_index == 2:
                        idx = sess_table_state.selected or 0
                        sess_table_state.select(min(idx + 1, max(0, len(cache["sess_list"]) - 1)))
                elif ev.code == "Up" or ev.code == "k":
                    if tab_index == 0:
                        idx = agent_list_state.selected or 0
                        agent_list_state.select(max(idx - 1, 0))
                    elif tab_index == 1:
                        idx = mcp_table_state.selected or 0
                        mcp_table_state.select(max(idx - 1, 0))
                    elif tab_index == 2:
                        idx = sess_table_state.selected or 0
                        sess_table_state.select(max(idx - 1, 0))
                elif ev.code == "Enter":
                    if tab_index == 0:
                        idx = agent_list_state.selected or 0
                        if idx < len(cache["agents"]):
                            action = "init"
                            action_data["agent"] = cache["agents"][idx]
                            break
                    elif tab_index == 2:
                        idx = sess_table_state.selected or 0
                        if idx < len(cache["sess_list"]):
                            action = "resume"
                            action_data["session"] = cache["sess_list"][idx]
                            break
                elif tab_index == 1:
                    if ev.code == "a":
                        action = "add_mcp"
                        break
                    elif ev.code == "r":
                        idx = mcp_table_state.selected or 0
                        servers_list = cache["mcp_results"] if cache["mcp_results"] else list(cache["servers"].keys())
                        if idx < len(servers_list):
                            action = "remove_mcp"
                            item = servers_list[idx]
                            action_data["name"] = item.name if hasattr(item, 'name') else str(item)
                            break
                    elif ev.code == "s":
                        action = "sync_mcp"
                        break
                elif tab_index == 2:
                    if ev.code == "d":
                        idx = sess_table_state.selected or 0
                        if idx < len(cache["sess_list"]):
                            sid = cache["sess_list"][idx]["id"]
                            delete_session(sid)
                            needs_refresh = True
                            sess_table_state.select(max(idx - 1, 0))

        # Outside the terminal for prompt flows
        if action == "quit":
            break
            
        elif action == "init":
            console.clear()
            agent = action_data["agent"]
            console.print(f"[bold cyan]Agent selected: {agent}[/]")
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
            
            project = Prompt.ask("Project Directory", default="./my-ctf")
            model_args = ["--model", model_id] if model_id else []
            cmd_preview = build_launch_command(agent, model_args)
            if cmd_preview:
                console.print(f"Launch preview: [dim]{' '.join(cmd_preview)}[/dim]")
            ok, detail = check_agent_available(agent)
            if not ok:
                console.print(f"[red]Pre-flight failed:[/red] {detail}")
                Prompt.ask("Press Enter to return")
                needs_refresh = True
                continue
            launch = Confirm.ask(f"Init {agent} in {project}?", default=True)
            if launch:
                setup_project(project)
                console.print("[green]Running pre-flight checks![/]")
                run_installs(list_servers())
                launch_agent(agent, project, model_id)
                Prompt.ask("Press Enter to return")
            needs_refresh = True

        elif action == "add_mcp":
            console.clear()
            console.print("[bold cyan]Add new MCP[/]")
            name = Prompt.ask("Name")
            if not name: continue
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
            
            try:
                add_server(name, entry)
                console.print("[green]Added and synced![/green]")
            except Exception as exc:
                console.print(f"[red]Add MCP failed:[/red] {exc}")
            Prompt.ask("Press Enter to continue")
            needs_refresh = True

        elif action == "remove_mcp":
            console.clear()
            name = action_data["name"]
            if Confirm.ask(f"Remove {name}?", default=False):
                try:
                    remove_server(name)
                    console.print(f"[green]Removed {name} and synced![/green]")
                except Exception as exc:
                    console.print(f"[red]Remove MCP failed:[/red] {exc}")
                Prompt.ask("Press Enter to continue")
            needs_refresh = True
            
        elif action == "sync_mcp":
            console.clear()
            try:
                sync()
                console.print("[green]Synced to all agents![/green]")
            except Exception as exc:
                console.print(f"[red]Sync failed:[/red] {exc}")
            Prompt.ask("Press Enter to continue")
            needs_refresh = True

        elif action == "resume":
            console.clear()
            s_to_resume = action_data["session"]
            cmd = get_resume_command(s_to_resume["agent"], s_to_resume)
            if not cmd:
                console.print(f"[yellow]{s_to_resume['agent']} doesn't support resuming. Launching normally in dir.[/yellow]")
                launch_agent(s_to_resume["agent"], s_to_resume["project"], s_to_resume.get("model"))
            else:
                os.chdir(s_to_resume["project"])
                console.print(f"Executing: {' '.join(cmd)}")
                subprocess.run(cmd, shell=(os.name == 'nt'))
            Prompt.ask("Press Enter to continue")
            needs_refresh = True
