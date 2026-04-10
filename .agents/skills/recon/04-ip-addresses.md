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
