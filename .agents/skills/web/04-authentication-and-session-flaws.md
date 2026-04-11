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
  - `->` **[Primary Probe]** If login/register JS hashes password client-side into a hidden field, treat the submitted hash as credential-equivalent; attempt controlled replay using captured request bodies, proxy history, logs, or memory artifacts
  - `->` **[Signal: Form has plaintext input + hidden `password` field populated in JS]** → replay the exact transmitted hash with valid CSRF/session context; test for direct post-auth redirects (`/admin/dashboard`, role pages)
  - `->` **[Dead End: Replay fails despite same hash]** → verify CSRF/session binding and origin host; retry with fresh login page + same hash in one cookie jar
  - `->` **[Signal: Low entropy / sequential]** → Brute-force active sessions via Intruder with valid token prefix + incremented suffix
  - `->` **[Dead End: Tokens opaque/random]** → Test fixation: set `Cookie: session=attacker123` before login; if server accepts it post-auth → fixation
  - `->` **[Dead End: No fixation]** → Test session persistence after password reset and logout; look for non-httponly cookies readable via DOM XSS

***

