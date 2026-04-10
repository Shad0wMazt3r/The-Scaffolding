# Recon - TTP

**Environment setup**

- Host OS: Linux VM, bare metal, or a Dockerized runner with Go, Python 3, Bash, GNU coreutils, jq, awk, sed, grep, GNU parallel, and sqlite3.
- Core recon binaries:
    - Passive/domain: subfinder, amass, assetfinder, dnsx, shuffledns, massdns
    - Web probing: httpx
    - Port/network: naabu, masscan, nmap
    - Crawling/archive: katana, gau, waybackurls, hakrawler
    - Content/params: unfurl, uro, qsreplace
    - Vuln triage: nuclei
    - Cloud/API: awscli, gcloud, az, s5cmd
    - Intel/pivots: whois, dig, curl, openssl, ASN/BGP lookup tooling
- Python packages: requests, aiohttp, dnspython, tldextract, pyyaml, pandas, python-Levenshtein, beautifulsoup4.
- Shell quality-of-life:
    - `export LC_ALL=C`
    - `export RECON_ROOT=$PWD/recon`
    - `mkdir -p "$RECON_ROOT"/{scope,seeds,root-domains,subdomains/{raw,brute,alts,resolved},hosts/{httpx,tech,shots},ips/{cidr,asn,ports,services},cloud/{buckets,functions,storage},crawl/{katana,archives,params,forms},js/{urls,beautified,findings},nuclei,notes,scripts,tmp}`
- Working-directory contract:
    - Every tool writes to a dedicated subfolder.
    - Every phase maintains `raw/`, `normalized`, and `verified` outputs.
    - Every “promoted” dataset has a canonical file:
        - `scope/root-domains.txt`
        - `subdomains/all.txt`
        - `subdomains/resolved/all.txt`
        - `hosts/httpx/live.txt`
        - `ips/all.txt`
        - `ips/services/live-ports.txt`
        - `cloud/assets.txt`
        - `js/urls/all.txt`
- Naming rules:
    - `*.raw.txt` = untrusted raw aggregation
    - `*.txt` = normalized/deduped plain text
    - `*.jsonl` = structured output retained for replay
    - `*.promoted.txt` = passed a validation gate and can feed the next state

```text
recon/
├── scope/
│   ├── program.txt
│   ├── out-of-scope.txt
│   └── root-domains.txt
├── seeds/
│   ├── company-names.txt
│   ├── known-urls.txt
│   └── brands.txt
├── root-domains/
│   ├── intel.raw.txt
│   ├── candidates.txt
│   └── promoted.txt
├── subdomains/
│   ├── raw/
│   ├── brute/
│   ├── alts/
│   ├── resolved/
│   └── all.txt
├── hosts/
│   ├── httpx/
│   ├── tech/
│   └── shots/
├── ips/
│   ├── cidr/
│   ├── asn/
│   ├── ports/
│   └── services/
├── cloud/
│   ├── buckets/
│   ├── functions/
│   └── storage/
├── crawl/
│   ├── katana/
│   ├── archives/
│   ├── params/
│   └── forms/
├── js/
│   ├── urls/
│   ├── beautified/
│   └── findings/
├── nuclei/
├── notes/
├── scripts/
└── tmp/
```

Simple normalization one-liner:

```bash
cat seeds/known-urls.txt 2>/dev/null | sed -E 's#^[[:space:]]+|[[:space:]]+$##g' | sed -E 's#^https?://##; s#/.*$##; s/:.*$##' | tr '[:upper:]' '[:lower:]' | sort -u > scope/root-domains.txt
```


## Root Domains

- `R0 -> [Condition: only company name, product name, or acquired brand is known]`
    - Primary Vector: build `seeds/company-names.txt`, `seeds/brands.txt`, then run org-to-domain discovery via OSINT, reverse-WHOIS sources, certificate transparency searches, and acquisition-history review.
    - Dead End Pivot:
        - Search trademarks, press releases, app-store publisher names, and CDN CNAME branding.
        - Pivot on employee email formats found in job posts or docs.
        - Pivot on TLS certificate Organization / SAN reuse across sibling brands.
    - Data Chaining:
        - Normalize all discovered candidate roots into `root-domains/intel.raw.txt`.
        - Filter with `comm -23` against `scope/out-of-scope.txt`.
        - Promote surviving roots into `root-domains/promoted.txt`, then copy to `scope/root-domains.txt`.
- `R1 -> [Condition: root domain already known] -> Action: canonicalize before enumeration`
    - Primary Vector: strip schemes, ports, paths, wildcards, and duplicate casing.
    - Dead End Pivot:
        - If the domain is a parked shell, pivot on historical snapshots and MX providers.
        - If the root has no web presence, pivot on DNS NS/MX/TXT and ASN ownership.
        - If brand mismatch exists, pivot on related domains sharing privacy-proxy leaks or favicon clusters.
    - Data Chaining:
        - `scope/root-domains.txt` becomes the only valid upstream file for subdomain tooling.
        - Preserve excluded roots in `scope/rejected-root-domains.txt` so you do not rediscover junk later.
- `R2 -> [Condition: root domain set is stable] -> Action: start passive subdomain discovery`
    - Primary Vector: `subfinder -dL scope/root-domains.txt -all -recursive -silent -o subdomains/raw/subfinder.raw.txt`; Subfinder is purpose-built for passive subdomain enumeration and supports workflow-friendly output modes and STDIN/STDOUT integration.[^5][^1]
    - Dead End Pivot:
        - Switch from passive to permutation-assisted DNS brute force on high-value labels like `api`, `admin`, `vpn`, `staging`, `dev`, `graphql`, `internal`, `sso`.
        - ASN brute-force reverse DNS for owned netblocks.
        - Mine JavaScript, archived URLs, public docs, and mobile-app configs for hidden hostnames.
    - Data Chaining:
        - `sort -u subdomains/raw/subfinder.raw.txt > subdomains/all.txt`
        - Feed `subdomains/all.txt` to DNS resolution, HTTP probing, and port discovery in parallel.
        - Keep per-root slices with `grep '\.example\.com$' subdomains/all.txt > subdomains/raw/example.com.txt`.

Simple root-to-subs branching one-liner:

```bash
subfinder -dL scope/root-domains.txt -all -recursive -silent | sed 's/\*\.//' | tr '[:upper:]' '[:lower:]' | sort -u > subdomains/all.txt
```


## Subdomains

- `S0 -> [Condition: have passive candidates] -> Action: resolve and kill wildcard noise`
    - Primary Vector: `dnsx -l subdomains/all.txt -silent -resp-only -a -aaaa -cname -retries 2 -o subdomains/resolved/dnsx.txt`
    - Dead End Pivot:
        - If most entries fail to resolve, rerun against alternate resolvers and compare deltas.
        - If wildcard DNS contaminates output, test random labels per zone and subtract matching answers.
        - If CDN fronting obscures origin, pivot on historical A records and passive DNS deltas.
    - Data Chaining:
        - Promote resolvable hosts into `subdomains/resolved/all.txt`.
        - Split CNAME-heavy hosts into `subdomains/resolved/cname.txt` for SaaS takeover review.
        - Extract direct A/AAAA answers into `ips/all.txt` for netblock correlation.
- `S1 -> [Condition: passive enumeration is thin] -> Action: branch into expansion modes`
    - Primary Vector: wordlist-driven permutations plus resolver-backed validation.
    - Dead End Pivot:
        - Header-induced vhost discovery: send alternate `Host:` values to known IPs and compare response length/title/hash.
        - Certificate SAN mining across sibling endpoints and alternate ports.
        - Public code/doc leaks: grep Swagger, Postman collections, Terraform, CI logs, and mobile APK/IPA strings.
    - Data Chaining:
        - Write candidates to `subdomains/brute/candidates.txt`.
        - Validate into `subdomains/brute/resolved.txt`.
        - Merge with `cat subdomains/resolved/all.txt subdomains/brute/resolved.txt | sort -u > subdomains/promoted.txt`.

Simple vhost brute one-liner:

```bash
while read ip; do while read host; do curl -sk --max-time 5 -H "Host: $host" https://$ip/ -o /dev/null -w "$ip $host %{http_code} %{size_download}\n"; done < subdomains/brute/candidates.txt; done < ips/all.txt | awk '$3 !~ /000|400|421|502|503/' > hosts/httpx/vhost-hits.txt
```

- `S2 -> [Condition: host resolves] -> Action: probe for live web services`
    - Primary Vector: `httpx -l subdomains/promoted.txt -silent -threads 200 -follow-host-redirects -title -tech-detect -status-code -content-length -server -ip -cname -asn -json -o hosts/httpx/httpx.jsonl`; httpx is built for high-volume HTTP probing, multiple probes, and pipeline transitions from asset identification into technology enrichment.[^3]
    - Dead End Pivot:
        - If `httpx` yields little, probe by CIDR and raw IP because httpx supports hosts, URLs, and CIDR inputs.[^3]
        - Retry with nonstandard schemes and ports: 81, 3000, 5000, 7001, 8080, 8443, 9000.
        - Reprobe using HEAD, GET, and randomized JA3/TLS fingerprints to shake loose WAF-biased behavior.
    - Data Chaining:
        - `jq -r 'select(.failed==false) | .url' hosts/httpx/httpx.jsonl | sort -u > hosts/httpx/live.txt`
        - `jq -r '[.url,.tech[]?] | @tsv' hosts/httpx/httpx.jsonl > hosts/tech/stack.tsv`
        - Feed `hosts/httpx/live.txt` into archive discovery, crawling, screenshots, and nuclei templates chosen by tech.
- `S3 -> [Condition: live host found] -> Action: classify by function`
    - Primary Vector:
        - API: paths like `/api`, `/graphql`, `/swagger`, `/openapi.json`
        - Admin: `admin`, `manage`, `console`, `backoffice`
        - Auth: `login`, `oauth`, `sso`, `idp`
        - Edge/static: CDN-only, 403/401, or single-page app shells
    - Dead End Pivot:
        - If the homepage is dead, fetch `robots.txt`, `sitemap.xml`, `/.well-known/`, and common manifest files.
        - If 403/401, pivot on path discovery, verb tampering, header-based origin hints, and archived content.
        - If SPA shell only, pivot hard into JS, source maps, and API backends.
    - Data Chaining:
        - Tag outputs into `hosts/httpx/by-type/{api,admin,auth,static}.txt`.
        - Use those files to drive specialized crawling depth, wordlists, and nuclei template subsets.


## IP Addresses

- `I0 -> [Condition: have IPs from DNS, ASN, or scope docs] -> Action: dedupe and attribute`
    - Primary Vector: consolidate into `ips/all.txt`, then map each IP to provider, ASN, and reverse DNS.
    - Dead End Pivot:
        - If IP attribution is noisy due to CDN ranges, separate edge IPs from likely origin IPs using headers, SSL SANs, and uncommon ports.
        - If only ASN is known, expand to owned CIDRs and then score by overlap with discovered domains.
        - If reverse DNS is sparse, pivot by TLS cert reuse on the IP.
    - Data Chaining:
        - Store `ip,asn,org,rdns,source` in `ips/asn/enriched.tsv`.
        - Split into `ips/asn/cdn.txt` and `ips/asn/origin-candidates.txt`.
        - Feed origin candidates to fast port scans and raw-IP HTTP probing.
- `I1 -> [Condition: IP or CIDR is in play] -> Action: fast port discovery`
    - Primary Vector: `masscan` for wide discovery or `naabu` for recon-speed targeted port discovery, then `nmap` only on promoted hits.
    - Dead End Pivot:
        - If common ports are closed, sweep sparse bug-bounty favorites: 2082, 2083, 2375, 50000, 5601, 6443, 7001, 8001, 9200, 10250.
        - If the host rate-limits, drop packet rate and randomize source timing.
        - If all ports seem dark, check whether the asset is IPv6-only, filtered behind ACLs, or bound to an alternate interface.
    - Data Chaining:
        - `masscan`/`naabu` output goes to `ips/ports/discovered.txt`.
        - Promote `(ip,port)` tuples with service banners into `ips/services/live-ports.txt`.
        - Send HTTP-like ports to `httpx -l`, and non-HTTP banners to protocol-specific validation.

Simple promotion one-liner:

```bash
awk -F: '{print $1":"$2}' ips/ports/discovered.txt | sort -u > ips/services/live-ports.txt
```

- `I2 -> [Condition: service banner or port class identified] -> Action: branch by protocol`
    - Primary Vector:
        - HTTP-like -> `httpx`
        - TLS-only -> `openssl s_client` for cert names, ALPN, and issuer pivots
        - SSH/RDP/VPN/mail -> versioning, hostnames, and policy leakage
    - Dead End Pivot:
        - Raw-IP virtual hosts: replay top candidate `Host:` headers.
        - Proxy-aware services: test `X-Forwarded-Host`, `Forwarded`, and absolute-URI requests.
        - Origin leak pivot: compare CDN edge response with direct IP response hash.
    - Data Chaining:
        - Cert SANs become `subdomains/alts/cert-derived.txt`.
        - Service banners become `notes/service-fingerprints.tsv`.
        - New hostnames loop back into `subdomains/all.txt`.


### Script Definition Block: origin-IP candidate correlator

- Input Data:
    - `hosts/httpx/httpx.jsonl`
    - `ips/asn/origin-candidates.txt`
    - TLS certificate SAN/issuer data
    - Response hashes for domain-backed and IP-backed requests
- Core Processing Logic:
    - Normalize URL-to-IP and IP-to-response relationships.
    - Group assets by body hash, title, server banner, and certificate overlap.
    - Score IPs higher when they match a known hostname on multiple dimensions.
    - Down-rank CDN or WAF-owned ranges automatically.
- Dependencies:
    - Python 3, pandas, requests, ssl, hashlib
- Expected Output Format:

```
- TSV: `candidate_ip<TAB>linked_host<TAB>confidence<TAB>reasons`
```


## Cloud Assets

- `C0 -> [Condition: have domains, CNAMEs, headers, or org naming patterns] -> Action: enumerate cloud-facing assets`
    - Primary Vector:
        - Mine hostnames, CNAMEs, response headers, and TLS SANs for provider markers.
        - Generate name candidates from brand, environment, region, and product strings.
    - Dead End Pivot:
        - Bucket-name permutations from JS constants, mobile-app endpoints, and CI/CD leaks.
        - Search public IaC, docs, and support articles for storage and API hostnames.
        - Reverse-pivot from common vendor patterns: `*.cloudfront.net`, `*.azurewebsites.net`, `storage.googleapis.com`, `*.s3.amazonaws.com`.
    - Data Chaining:
        - Store raw provider indicators in `cloud/assets.raw.txt`.
        - Normalize into `cloud/assets.txt` with columns: `asset,provider,type,source`.
        - Feed storage endpoints into unauthenticated read/list checks and misbinding review.
- `C1 -> [Condition: cloud storage candidate exists] -> Action: test existence, exposure, and orphaning`
    - Primary Vector:
        - Check bucket/container existence, public listing, public object read, website hosting, and CNAME binding.
    - Dead End Pivot:
        - If the bucket does not resolve, test alternate region formats and legacy naming styles.
        - If access is denied, probe for object-level public access using guessed filenames from crawls.
        - If the bucket is absent but referenced by a live CNAME, pivot into takeover validation.
    - Data Chaining:
        - Save findings to `cloud/buckets/findings.tsv`.
        - Extract object URLs into `crawl/archives/object-urls.txt`.
        - Feed JS, JSON, CSV, and backup-like objects into content triage.

Simple storage artifact grep:

```bash
grep -RhoE '([a-z0-9.-]+\.s3\.amazonaws\.com|storage.googleapis.com/[a-z0-9._-]+|[a-z0-9.-]+\.blob\.core\.windows\.net)' hosts/ crawl/ js/ 2>/dev/null | sort -u > cloud/assets.txt
```

- `C2 -> [Condition: serverless or managed API hostnames appear] -> Action: enumerate edge trust boundaries`
    - Primary Vector:
        - Identify Lambda/API Gateway, Cloud Functions, Azure Functions, App Engine, App Service, and container-hosted APIs.
    - Dead End Pivot:
        - If the endpoint is fronted by a custom domain, fetch the default platform hostname from cert SANs, headers, and archive indexes.
        - If only the API is visible, pivot into CORS, auth flow, debug routes, and stage names.
        - If staging clues exist, brute environment suffixes and region labels.
    - Data Chaining:
        - Write platform-default endpoints to `cloud/functions/default-hosts.txt`.
        - Push all verified URLs into `hosts/httpx/live.txt` for deeper crawling and nuclei selection.


### Script Definition Block: bucket-name generator

- Input Data:
    - `scope/root-domains.txt`
    - `seeds/brands.txt`
    - words extracted from titles, JS constants, path segments, and TLS SANs
- Core Processing Logic:
    - Tokenize brand/product/environment/region words.
    - Generate permutations using separators `-`, `.`, and none.
    - Add suffix families: `assets`, `static`, `media`, `backup`, `logs`, `dev`, `stage`, `prod`.
    - Score candidates by lexical similarity to observed domains and JS references.
- Dependencies:
    - Python 3, tldextract, itertools, python-Levenshtein
- Expected Output Format:
    - Plain text list of candidate bucket/container names ranked by confidence


## JS Files

- `J0 -> [Condition: live web hosts exist] -> Action: collect JavaScript aggressively`
    - Primary Vector: crawl live hosts with Katana using JS-aware options; Katana supports JS crawling, headless mode, XHR extraction, known-file crawling, JSONL output, and response storage.[^2][^6]
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

**State transition rules**

- Promote data only after a validation gate.
- Any newly discovered hostname loops back to `Subdomains -> S0`.
- Any newly discovered IP loops back to `IP Addresses -> I0`.
- Any cloud indicator loops to `Cloud Assets -> C0`.
- Any live endpoint or JS artifact loops to `JS Files -> J1`.
- Any phase with fewer than 3 net-new assets triggers its corresponding **Dead End Pivot** branch instead of continuing forward.

**Minimal orchestration order**

1. `scope/root-domains.txt`
2. `subfinder -> subdomains/all.txt`[^1][^5]
3. `dnsx -> subdomains/resolved/all.txt`
4. `httpx -> hosts/httpx/httpx.jsonl`[^3]
5. `katana/archive -> js/urls/all.txt`[^6][^2]
6. `IP/cloud/JS pivots -> feed discoveries back upstream`

This keeps the workflow recursive instead of linear, which is the right shape for high-yield recon in large bug-bounty programs.
