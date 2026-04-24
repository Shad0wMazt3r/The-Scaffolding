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
    - Primary Vector: `httpx -l subdomains/promoted.txt -silent -threads 200 -follow-host-redirects -title -tech-detect -status-code -content-length -server -ip -cname -asn -json -o hosts/httpx/httpx.jsonl`; httpx is built for high-volume HTTP probing, multiple probes, and pipeline transitions from asset identification into technology enrichment.
    - Dead End Pivot:
        - If `httpx` yields little, probe by CIDR and raw IP because httpx supports hosts, URLs, and CIDR inputs.
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


