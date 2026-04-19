import socket
import urllib.request
import subprocess
from concurrent.futures import ThreadPoolExecutor

class HealthResult:
    def __init__(self, name, status, message, warn_only, latency_ms=0):
        self.name = name
        self.status = status # 'up', 'down', 'conflict'
        self.message = message
        self.warn_only = warn_only
        self.latency_ms = latency_ms

def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0

def check_http(url, port):
    if port and check_port("127.0.0.1", int(port)):
        try:
            urllib.request.urlopen(url, timeout=2)
            return "up", "OK"
        except urllib.error.HTTPError as e:
            return "up", f"HTTP {e.code}"
        except Exception as e:
            return "conflict", f"Port {port} in use by non-MCP process"
    else:
        return "down", "Connection refused"

def check_docker(image):
    try:
        res = subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True)
        if res.returncode == 0:
            return "up", "Image exists"
        return "down", "Image not found"
    except FileNotFoundError:
        return "down", "Docker not installed"

def check_bridge(path, port):
    from pathlib import Path
    if port and check_port("127.0.0.1", int(port)):
        return "up", "Bridge running"
    
    if Path(path).exists():
        return "up", "Bridge found (inactive)"
    return "down", "Bridge script missing"

def check_server(name: str, entry: dict) -> HealthResult:
    from scaffold.env import resolve_dict
    entry = resolve_dict(entry)
    health_cfg = entry.get("health", {})
    warn_only = health_cfg.get("warnOnly", False)
    htype = health_cfg.get("type")
    
    if htype == "http":
        url = entry.get("transports", {}).get("http", {}).get("url") or entry.get("transports", {}).get("sse", {}).get("url")
        if not url: url = "http://127.0.0.1:8000"
        status, msg = check_http(url, health_cfg.get("port"))
        return HealthResult(name, status, msg, warn_only)
    elif htype == "docker-image":
        status, msg = check_docker(health_cfg.get("image"))
        return HealthResult(name, status, msg, warn_only)
    elif htype == "bridge-path":
        status, msg = check_bridge(health_cfg.get("path", ""), health_cfg.get("port"))
        return HealthResult(name, status, msg, warn_only)
    
    return HealthResult(name, "up", "No health check", warn_only)

def check_all(servers: dict) -> list:
    results = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(check_server, k, v): k for k, v in servers.items()}
        for f in futures:
            results.append(f.result())
    return results
