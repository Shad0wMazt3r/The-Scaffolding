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


