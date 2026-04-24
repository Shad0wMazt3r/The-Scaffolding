## Cross-Class Data Chaining Map

```
JS Recon (secrets) ──────► API Auth Bypass
     │                          │
     ▼                          ▼
SSRF (IMDSv1 creds) ──────► AWS Lateral Movement
     │
     ▼
Internal hostname → New IDOR → Privilege Escalation
     │
     ▼
GraphQL Introspection → Admin mutation → RCE via upload
     │
     ▼
JWT kid traversal → Algorithm confusion → Auth bypass → Business Logic
     │
     ▼
PRNG state leak → Protocol artifact prediction → MIME confusion → XSS → Token abuse
     │
     ▼
Actuator heapdump → Credential artifacts → Admin route → Flag/secret
```

Every finding should triage through this chain — low-severity info leaks frequently unlock critical vulnerabilities when cross-class chaining is applied systematically.

***
