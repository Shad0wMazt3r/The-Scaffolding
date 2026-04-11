## Cross-Class Data Chaining Map

```
JS Recon (secrets) ──────────────────────────────► API Auth Bypass
     │                                                     │
     ▼                                                     ▼
SSRF (IMDSv1 creds) ────────────────────────────► AWS Lateral Movement
     │
     ▼
Internal hostname leak ──► New IDOR surface ──► Privilege Escalation
     │
     ▼
GraphQL Introspection ──► Admin mutation ──► RCE via file upload
     │
     ▼
JWT kid traversal ──► Algorithm confusion ──► Auth bypass ──► Business Logic
     │
     ▼
PRNG state leak ──► Predict protocol artifact (boundary/nonce/id) ──► MIME confusion ──► XSS ──► Token abuse
     │
     ▼
Actuator heapdump exposure ──► Credential artifacts (user + transmitted hash) ──► Admin route access ──► Flag/secret extraction
```

Every finding should be triaged through this chain — a low-severity information leak from JS files or a headers-based hostname disclosure frequently unlocks critical-severity vulnerabilities when cross-class chaining is applied methodically. [sprocketsecurity](https://www.sprocketsecurity.com/blog/pentesting-standards-2025)
