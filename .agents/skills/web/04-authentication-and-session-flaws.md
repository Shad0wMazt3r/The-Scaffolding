## Authentication & Session Flaws

### JWT Attacks

- **[Primary Probe]** Decode JWT; inspect `alg` header; run `jwt_tool <token> -M at` for all attack modes
  - **[Signal: `alg:none` accepted]** Strip signature: `eyJ...header.eyJ...payload.` (empty sig)
  - **[Signal: RS256 → HS256 confusion]** Sign with HS256 using public key as HMAC secret: `jwt_tool <token> -X k -pk public.pem`
  - **[Dead End: Algorithm hardened]** Try JWK header injection with attacker-controlled key; also test `jku`/`x5u` with attacker-hosted JWKS
  - **[Dead End: Signature verified]** Weak secret brute-force: `hashcat -a 0 -m 16500 token.jwt rockyou.txt`
  - **[Dead End: Strong secret]** Check `kid` for path traversal: `"kid": "../../dev/null"` → HMAC with empty secret
  - **[Data Chaining]** Forged admin JWT → admin API → trigger SSRF via admin webhooks

### OAuth / SSO Flaws

- **[Primary Probe]** Capture auth code flow; test `redirect_uri` bypass: `%0a`, `//evil.com`, `..%2F`, `target.com.evil.com`
  - **[Signal: Code redirected to attacker]** Steal code → exchange for access token
  - **[Dead End: redirect_uri pinned]** Test `state` parameter CSRF: remove state, initiate, complete with victim session → ATO
  - **[Dead End: state validated]** Check Referer leakage: does auth code appear in `Referer` to third-party scripts?
  - **[Dead End: No referer leakage]** Implicit flow fragment leak: inject `<img src=x>` to leak `#access_token=` via referrer policy

### Session Management

- **[Primary Probe]** Entropy analysis: collect 100 tokens, measure uniqueness via Burp Sequencer
- **[Primary Probe]** Client-side hash: if login JS hashes password into hidden field, treat hash as credential-equivalent
  - **[Signal: Plaintext input + hidden hash field]** Replay exact hash with valid CSRF/session context
  - **[Dead End: Replay fails]** Verify CSRF/session binding, origin host, retry with fresh page
- **[Signal: Low entropy / sequential]** Brute-force sessions via Intruder with valid prefix + incremented suffix
- **[Dead End: Opaque tokens]** Test fixation: set `Cookie: session=attacker123` pre-login; if accepted post-auth → fixation
- **[Dead End: No fixation]** Test persistence after password reset/logout; check for non-httponly cookies readable via XSS

***
