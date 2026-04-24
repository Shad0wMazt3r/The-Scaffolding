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
    - Primary Vector: `subfinder -dL scope/root-domains.txt -all -recursive -silent -o subdomains/raw/subfinder.raw.txt`; Subfinder is purpose-built for passive subdomain enumeration and supports workflow-friendly output modes and STDIN/STDOUT integration.
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


