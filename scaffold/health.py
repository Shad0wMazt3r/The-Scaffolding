import socket
import urllib.request
import urllib.error
from urllib.parse import urlparse
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

class HealthResult:
    def __init__(self, name, status, message, warn_only, latency_ms=0):
        self.name = name
        self.status = status # 'up', 'down', 'conflict', 'error'
        self.message = message
        self.warn_only = warn_only
        self.latency_ms = latency_ms

def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0

def _url_port(url: str) -> int | None:
    parsed = urlparse(url)
    return parsed.port


def _url_host(url: str) -> str:
    parsed = urlparse(url)
    return parsed.hostname or "127.0.0.1"


def check_http(url, port):
    start = time.perf_counter()
    host = _url_host(url)
    port_int = int(port) if str(port).isdigit() else _url_port(url)
    if port_int and not check_port(host, int(port_int)):
        return "down", "Connection refused", 0
    try:
        urllib.request.urlopen(url, timeout=2)
        latency = int((time.perf_counter() - start) * 1000)
        return "up", "OK", latency
    except urllib.error.HTTPError as e:
        latency = int((time.perf_counter() - start) * 1000)
        return "up", f"HTTP {e.code}", latency
    except urllib.error.URLError as e:
        if port_int and check_port(host, int(port_int)):
            return "conflict", f"Port {port_int} reachable but endpoint failed: {e.reason}", 0
        return "down", f"Request failed: {e.reason}", 0
    except Exception as e:
        return "error", f"HTTP health check error: {type(e).__name__}", 0

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
        status, msg, latency_ms = check_http(url, health_cfg.get("port"))
        return HealthResult(name, status, msg, warn_only, latency_ms=latency_ms)
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
            name = futures[f]
            try:
                results.append(f.result())
            except Exception as exc:
                results.append(HealthResult(name, "error", f"Unhandled health exception: {exc}", warn_only=False))
    return results
