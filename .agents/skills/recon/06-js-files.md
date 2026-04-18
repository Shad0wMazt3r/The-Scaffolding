## JS Files

- `J0 -> [Condition: live web hosts exist] -> Action: collect JavaScript aggressively`
    - Primary Vector: crawl live hosts with Katana using JS-aware options; Katana supports JS crawling, headless mode, XHR extraction, known-file crawling, JSONL output, and response storage. [projectdiscovery](https://docs.projectdiscovery.io/tools/katana/overview)
    - Dead End Pivot:
        - If crawling is thin, pull archive URLs from gau/Wayback and filter for `\.js`, `map`, `json`, `config`.
        - If the app is SPA-heavy, enable headless crawling and XHR extraction.
        - If the site blocks generic crawlers, replay with browser-like headers, authenticated cookies, and alternate user agents.
    - Data Chaining:
        - `katana -list hosts/httpx/live.txt -depth 5 -jc -jsl -xhr -kf all -headless -store-response -store-response-dir crawl/katana/responses -jsonl -o crawl/katana/output.jsonl`
        - Extract JS URLs into `js/urls/all.txt`.
        - Store response bodies for grep-based secret hunting and endpoint mining.

Simple JS URL extraction one-liner:

```bash
grep -RhoE 'https?://[^"'\'' )]+\.js([?#][^"'\'' )]+)?' crawl/katana/responses crawl/archives 2>/dev/null | sed 's/[?#].*$//' | sort -u > js/urls/all.txt
```

- `J1 -> [Condition: JS corpus exists] -> Action: mine endpoints, secrets, and hidden hosts`
    - Primary Vector:
        - Extract absolute URLs, relative API paths, GraphQL endpoints, WebSocket URLs, OAuth metadata, storage URLs, and environment constants.
    - Dead End Pivot:
        - If code is minified, beautify and rescan.
        - If everything is bundled, pivot through source maps and webpack chunk naming.
        - If secrets are absent, hunt for token issuers, key IDs, client IDs, and undocumented route prefixes.
    - Data Chaining:
        - Endpoints -> `crawl/params/endpoints.txt`
        - Hostnames -> `subdomains/alts/js-hosts.txt`
        - Storage URLs -> `cloud/assets.txt`
        - Params -> `crawl/params/keys.txt`
        - Loop new hostnames back into DNS resolution and httpx probing.

Simple secret-and-endpoint grep:

```bash
grep -RInaE '(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|xox[baprs]-|https?://[^"'\'' ]+|/[A-Za-z0-9._~!$&()*+,;=:@%/-]{3,})' crawl/katana/responses js/beautified 2>/dev/null > js/findings/raw-grep.txt
```

- `J2 -> [Condition: endpoints extracted] -> Action: classify and replay`
    - Primary Vector:
        - Separate paths into unauthenticated, authenticated, admin-only, upload, export, search, callback, and debug classes.
    - Dead End Pivot:
        - If endpoints return 401/403, replay with browser headers, CSRF bootstrap flow, and alternate verbs.
        - If they appear dormant, test archived parameter sets and old chunk references.
        - If only GraphQL appears, pivot into schema discovery, introspection behavior, and persisted query endpoints.
    - Data Chaining:
        - `crawl/params/endpoints.txt` -> replay queue
        - `crawl/params/keys.txt` -> param fuzzing wordlist
        - successful replays -> `hosts/httpx/api-live.txt`
        - API-live -> nuclei, custom auth-state testing, and business-logic review


### Script Definition Block: JS semantic analyzer

- Input Data:
    - `js/urls/all.txt`
    - downloaded JS bodies
    - source maps when available
- Core Processing Logic:
    - Parse AST or token stream.
    - Extract string literals, object keys, fetch/XHR calls, WebSocket constructors, route tables, and environment assignments.
    - Score interesting constants: credentials, JWT issuers, bucket names, private base URLs, feature flags, admin roles.
    - Emit normalized findings and confidence labels.
- Dependencies:
    - Python 3 or Node.js, tree-sitter or esprima, jsbeautifier
- Expected Output Format:
    - JSONL records: `type`, `value`, `source_file`, `line`, `confidence`, `pivot_target`
- `J3 -> [Condition: source maps found] -> Action: prioritize them above raw bundles`
    - Primary Vector:
        - Retrieve `.map` files, reconstruct original source tree, and search for internal comments, TODOs, hidden routes, and nonproduction API hosts.
    - Dead End Pivot:
        - If the map is missing but referenced, brute common suffixes and old hashed filenames from archives.
        - If map access is blocked, inspect JS footer comments and webpack metadata for original module names.
        - If source is vendor-only, separate first-party modules by path prefix and domain alignment.
    - Data Chaining:
        - Original-source paths -> `js/findings/source-tree.txt`
        - New routes and hosts -> `crawl/params/endpoints.txt` and `subdomains/alts/js-hosts.txt`
        - Secrets/config material -> `notes/high-signal-findings.md`

