import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from scaffold.tui import run_tui
from scaffold.registry import add_server, remove_server, sync, list_servers
from scaffold.launcher import launch_agent
from scaffold.skeleton import setup_project
from scaffold.health import check_all
from scaffold.sessions import get_resume_command, load_sessions
from scaffold.installer import run_installs

def main():
    parser = argparse.ArgumentParser(description="The Scaffolding - MCP Agent Orchestration")
    subparsers = parser.add_subparsers(dest="command")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize and launch an agent")
    init_parser.add_argument("--agent", help="Name of the agent")
    init_parser.add_argument("--project", help="Project directory")
    init_parser.add_argument("--model", help="Model to use")
    init_parser.add_argument("--dry-run", action="store_true")

    # mcp
    mcp_parser = subparsers.add_parser("mcp", help="Manage MCP registry")
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command")
    
    mcp_sub.add_parser("list", help="List registered MCPs")
    
    add_parser = mcp_sub.add_parser("add", help="Add an MCP")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--transport", choices=["http", "sse", "stdio"], required=True)
    add_parser.add_argument("--url")
    add_parser.add_argument("--description")
    add_parser.add_argument("--git-url")
    add_parser.add_argument("--install-cmd")
    add_parser.add_argument("--dry-run", action="store_true")

    rm_parser = mcp_sub.add_parser("remove", help="Remove an MCP")
    rm_parser.add_argument("name")

    sync_parser = mcp_sub.add_parser("sync", help="Sync MCPs to agent configs")
    sync_parser.add_argument("--agent", help="Sync to specific agent only")
    sync_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    # Disable imports outputting to console during import if possible
    # We already handle clear screen in TUI

    if not args.command:
        run_tui()
        return

    if args.command == "init":
        if not args.agent or not args.project:
            run_tui("init")
            return
        
        if args.dry_run:
            print(f"[DRY-RUN] Would init {args.agent} in {args.project} with model {args.model}")
            return
            
        print(f"Initializing {args.agent} in {args.project}...")
        setup_project(args.project)
        servers = list_servers()
        run_installs(servers)
        launch_agent(args.agent, args.project, args.model)

    elif args.command == "mcp":
        if args.mcp_command == "list":
            servers = list_servers()
            results = check_all(servers)
            for r in results:
                print(f"{r.name}: {'[UP]' if r.status=='up' else '[DOWN/ERROR]'} - {r.message}")
                
        elif args.mcp_command == "add":
            if args.dry_run:
                print(f"[DRY-RUN] Would add {args.name}")
                return
            entry = {
                "description": args.description or "",
                "transports": {},
                "health": {"warnOnly": False}
            }
            if args.transport in ["http", "sse"]:
                entry["transports"][args.transport] = {"url": args.url}
                entry["health"]["type"] = "http"
            else:
                entry["transports"]["stdio"] = {"command": args.url or "", "args": []}
            
            if args.git_url:
                entry["source"] = {
                    "git": args.git_url,
                    "install": args.install_cmd,
                    "localPath": f"./tools/{args.name}"
                }
            add_server(args.name, entry)
            print(f"Added {args.name} and synced to agents.")
            
        elif args.mcp_command == "remove":
            remove_server(args.name)
            print(f"Removed {args.name} and synced.")
            
        elif args.mcp_command == "sync":
            if args.dry_run:
                print(f"[DRY-RUN] Would sync to {args.agent or 'all agents'}")
                return
            sync(args.agent)
            print("Sync complete.")

if __name__ == "__main__":
    main()
