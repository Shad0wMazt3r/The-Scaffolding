## Web Assessment Setup

### Project Layout
```
/vulns/<target>/
├── burp/project.burp
├── recon/{subdomains,endpoints,params}.txt
├── payloads/{sqli,xss,ssti,ssrf}/
├── evidence/{screenshots,logs,poc}/
└── reports/
```

### Key Tools
Proxy: Burp Suite Pro | Recon: amass, httpx, gau | Fuzzing: ffuf, feroxbuster | Injection: sqlmap, dalfox, tplmap, commix | OOB: interactsh-client | JWT: jwt_tool | Deserialization: ysoserial | Smuggling: h2csmuggler

### Session Management & Proxy
- Set up Burp CA globally, configure system proxy to 127.0.0.1:8080
- Burp Session Handling Rules: macro-based CSRF token refresh, Token Extractor extension for bearer rotation, AuthMatrix for role mapping
- Maintain separate Burp projects per role (`admin.burp`, `user.burp`, `guest.burp`)

### Local CTF Setup
- **Port collisions:** Check target ports vs. running services (MCP, proxies, local APIs) before exploitation
- **One-shot endpoints:** Identify before running and plan restart checkpoints
- **RNG attacks:** Keep request ordering deterministic, avoid background traffic consuming PRNG outputs
