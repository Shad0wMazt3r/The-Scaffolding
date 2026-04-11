# Web Application Vulnerability Identification Framework & Execution Playbook

***

## Prerequisites & Environment Setup

### Directory Structure
```
/vulns/<target>/
├── burp/
│   ├── project.burp
│   ├── scan-configs/
│   └── extensions/
├── recon/
│   ├── subdomains.txt
│   ├── endpoints.txt
│   ├── js-files.txt
│   └── params.txt
├── payloads/
│   ├── sqli/
│   ├── xss/
│   ├── ssti/
│   ├── ssrf/
│   └── custom/
├── evidence/
│   ├── screenshots/
│   ├── http-logs/
│   └── poc-scripts/
└── reports/
    ├── draft.md
    └── final/
```

### Toolstack
| Category | Tools |
|---|---|
| Proxy/Interception | Burp Suite Pro, mitmproxy |
| Recon | Amass, Subfinder, httpx, gau, waybackurls, katana |
| Fuzzing | ffuf, feroxbuster, wfuzz |
| Injection | sqlmap, dalfox (XSS), tplmap (SSTI), commix (CMDi) |
| API | Postman, Arjun, kiterunner, graphql-cop |
| OOB Detection | interactsh-client, Burp Collaborator |
| Deserialization | ysoserial, PHPGGC, gadgetinspector |
| Scripting | Python 3.11+, httpx lib, requests, pwntools |
| JWT | jwt_tool, jwt-cracker |
| Smuggling | smuggler.py, h2csmuggler |
| Prototype Pollution | ppmap, dom-invader (Burp) |

### Proxy & CA Setup
```bash
# Global proxy config
export http_proxy=http://127.0.0.1:8080
export https_proxy=http://127.0.0.1:8080

# Install Burp CA system-wide (Ubuntu/Kali)
curl -sk http://127.0.0.1:8080/cert -o burp-ca.der
openssl x509 -inform DER -in burp-ca.der -out burp-ca.crt
sudo cp burp-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Firefox: about:preferences -> Certificates -> Import burp-ca.crt
# Mobile: Push via ADB and install under Settings > Security > CA Cert
```

### Session Management
- Use Burp's **Session Handling Rules** with macro-based CSRF token refresh
- Install **Token Extractor** extension to auto-rotate bearer tokens per-request
- Configure **AuthMatrix** extension for multi-role privilege mapping
- Maintain separate Burp projects per role: `admin.burp`, `user.burp`, `guest.burp`

### Local Mirror Validation (CTF-first)
- Before local exploitation runs, ensure target ports do not collide with existing tooling (MCP servers, proxies, local APIs); remap compose ports immediately if needed.
- Mark one-shot endpoints and reset conditions up front (e.g., password leak-once endpoints) and plan restart points before brute-force/long exploit chains.
- For RNG/state recovery attacks, keep request ordering deterministic and avoid background traffic that consumes extra PRNG outputs.

***

