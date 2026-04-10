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

