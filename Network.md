# Network - TTPs

## Environment

NIST SP 800-115 recommends a repeatable, documented methodology, explicit coordination, and controlled handling of collected data, including collection, storage, transmission, and destruction.  PTES also describes its technical guidelines as baseline methods that should be adapted inside your own standard rather than treated as a complete script.

```text
/vulns/<target>/
├── discovery/
├── services/
├── auth/
├── directory/
├── infra/
├── configs/
├── credentials/
├── loot/
├── evidence/
│   ├── pcaps/
│   ├── screenshots/
│   ├── logs/
│   └── timelines/
├── reports/
│   ├── notes/
│   ├── findings/
│   └── final/
└── ops/
    ├── scope/
    ├── roe/
    ├── connectivity/
    └── chain/
```

- Bind all assessment traffic to a designated interface, document every approved egress path in `/ops/connectivity/`, and record every bastion, SOCKS hop, or VPN handoff in `/ops/chain/chain.md`.
- Keep credentials out of shell history and plaintext notes; store them in a vault such as KeePassXC or `pass`, and mirror checkout history in `/credentials/audit.log`.
- Minimal setup one-liners:
  - `mkdir -p /vulns/$TARGET/{discovery,services,auth,directory,infra,configs,credentials,loot,evidence/{pcaps,screenshots,logs,timelines},reports/{notes,findings,final},ops/{scope,roe,connectivity,chain}}`
  - `umask 077 && export TARGET=<target> && export WORKDIR=/vulns/$TARGET`

## Services & Authentication

NIST groups technical assessment work into review techniques, target identification and analysis, and target vulnerability validation, which is the safest way to organize this workflow without turning it into an exploitation script.  Microsoft’s current AD guidance emphasizes least privilege, secure administrative hosts, MFA for privileged work, restricting NTLM, and using the Protected Users group where appropriate. [learn.microsoft](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/best-practices-for-securing-active-directory)

- Network Services & Banner Grabbing
  - * -> [Condition: Asset is in approved scope and reachable] -> Action: Primary validation — identify live hosts, open ports, service banners, TLS posture, and ownership; normalize results into `/services/open-services.csv`.
  - * -> [Condition: Initial probe is inconclusive] -> Action: Dead-end pivots — compare passive flow data, review firewall/NAT rulesets, and perform authenticated config review on the target or load balancer.
  - * -> [Condition: Legacy or unmanaged service is confirmed] -> Action: Data chaining — feed host, port, owner, and version into patch review, credential exposure review, and segmentation validation.

- Authentication Attacks (Brute Force, Pass-the-Hash, Kerberoasting, AS-REP Roasting)
  - * -> [Condition: Kerberos, NTLM, LDAP, RDP, SMB, SSH, or VPN auth is present] -> Action: Primary validation — review lockout policy, password policy, SPN inventory, preauthentication settings, delegation settings, NTLM usage, and privileged account placement. [semperis](https://www.semperis.com/blog/active-directory-security/active-directory-security-best-practices-checklist/)
  - * -> [Condition: No obvious auth weakness appears] -> Action: Dead-end pivots — inspect GPO drift, compare interactive logon rights against admin tiering, and review service account lifecycle and rotation evidence.
  - * -> [Condition: Weak service-account hygiene or delegation exposure is found] -> Action: Data chaining — move into privilege review, secure-admin-host coverage, and tier boundary validation rather than credential replay.

- Safe parsing helpers
  - `xmlstarlet sel -t -m '//port[state/@state="open"]' -v '../../address/@addr' -o ',' -v '@portid' -o ',' -v 'service/@name' -o ',' -v 'service/@product' -n /vulns/$TARGET/discovery/full.xml | sort -u > /vulns/$TARGET/services/open-services.csv`
  - `awk -F, '$3 ~ /(ftp|telnet|snmp|ldap|rdp|smb|ssh)/ {print}' /vulns/$TARGET/services/open-services.csv > /vulns/$TARGET/services/auth-surface.csv`

## MITM, SMB & Directory

Microsoft recommends monitoring sensitive AD objects, preventing powerful accounts from being used on unauthorized systems, eliminating permanent membership in highly privileged groups where possible, and using secure administrative hosts.  Microsoft and related AD hardening guidance also call out disabling SMBv1, restricting NTLM, applying SID filtering across forest trusts, and marking sensitive accounts as non-delegable where appropriate. [learn.microsoft](https://learn.microsoft.com/en-us/training/modules/manage-security-active-directory/)

- Man-in-the-Middle & Protocol Abuse
  - * -> [Condition: Windows name resolution or IPv6 is present] -> Action: Primary validation — verify LLMNR, NBT-NS, WPAD, DHCPv6, RA guard, SMB signing, and LDAP signing/channel binding controls through configuration review and controlled packet capture.
  - * -> [Condition: No misconfiguration is visible from configs] -> Action: Dead-end pivots — compare switch hardening, validate DHCP snooping and ARP inspection state, and inspect endpoint baseline policy for multicast name resolution.
  - * -> [Condition: Weak resolution or signing controls are confirmed] -> Action: Data chaining — map which auth paths would be exposed, then test whether privileged accounts are segregated onto secure admin hosts. [learn.microsoft](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/best-practices-for-securing-active-directory)

- SMB & Windows Protocol Attacks
  - * -> [Condition: SMB or RPC services exist] -> Action: Primary validation — verify SMB dialects, signing requirements, guest access, admin share exposure, spooler posture, and NTLM fallback paths.
  - * -> [Condition: Baseline looks clean] -> Action: Dead-end pivots — review file-server GPOs, compare endpoint exceptions, and inspect backup or print infrastructure for inherited legacy settings.
  - * -> [Condition: Legacy SMB or NTLM dependency is found] -> Action: Data chaining — link the host list to patching, admin tiering, and service-account ownership for remediation prioritization. [semperis](https://www.semperis.com/blog/active-directory-security/active-directory-security-best-practices-checklist/)

- Active Directory Enumeration & Privilege Escalation
  - * -> [Condition: Domain assets are in scope] -> Action: Primary validation — review privileged groups, trusts, delegation types, admin workstation separation, replication rights, and high-risk account flags such as “Account is sensitive and cannot be delegated.” [learn.microsoft](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/best-practices-for-securing-active-directory)
  - * -> [Condition: No obvious directory weakness appears] -> Action: Dead-end pivots — inspect GPO delegation, compare ACL baselines on OUs and key objects, and review temporary privileged access workflows.
  - * -> [Condition: Trust, delegation, or ACL drift is confirmed] -> Action: Data chaining — map affected admin paths, then validate whether monitoring covers changes to sensitive AD objects and privileged group membership. [learn.microsoft](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/best-practices-for-securing-active-directory)

- Complex script definition block: Directory control-gap mapper
  - Input Data: LDAP export, GPO report, privileged group membership export, trust inventory, admin-host inventory, event log summaries.
  - Core Processing Logic:
    - Normalize identities, groups, OUs, trusts, and hosts into one graphable dataset.
    - Flag permanent privileged membership, unconstrained or risky delegation, legacy auth dependencies, and tier violations.
    - Score each finding by blast radius, privilege level, and compensating-control coverage.
    - Emit remediation owners by OU, service owner, or platform team.
  - Dependencies: Python, `pandas`, LDAP export parser, GPO report parser.
  - Expected Output Format: `jsonl` for findings, `csv` for owner/action tracking, `md` narrative for the report appendix.

## Exposure & Remote Access

NIST states that no single technique gives a complete security picture and recommends combining techniques while tailoring intrusiveness to acceptable risk.  NIST also notes that risk can be reduced through skilled assessors, comprehensive plans, activity logging, off-hours testing, and testing against duplicates of production systems where possible.

- Unpatched Services & CVE Exploitation
  - * -> [Condition: Versioned service or device firmware is identified] -> Action: Primary validation — correlate version, platform, and configuration against vendor advisories and patch baselines; validate only with non-destructive checks in production.
  - * -> [Condition: Version data is missing or obfuscated] -> Action: Dead-end pivots — use authenticated package inventory, maintenance records, and device configuration review.
  - * -> [Condition: Exposure is likely but confidence is low] -> Action: Data chaining — move the asset into change-control review, owner confirmation, and duplicate-environment validation before any deeper testing.

- Firewall & IDS/IPS Evasion
  - * -> [Condition: Segmentation or filtering effectiveness must be validated] -> Action: Primary validation — review rulesets, route paths, NAT behavior, and sensor placement rather than attempting evasion against production controls.
  - * -> [Condition: Rules appear correct but behavior disagrees] -> Action: Dead-end pivots — compare asymmetric routing, load balancer policy, and upstream ACLs.
  - * -> [Condition: A control gap is confirmed] -> Action: Data chaining — attach flow evidence, affected VLANs/subnets, and rule-owner metadata for remediation.

- VPN & Remote Access Weaknesses
  - * -> [Condition: Remote access is in scope] -> Action: Primary validation — review MFA enforcement, certificate validation, split tunneling, idle timeout, device posture checks, and fallback authentication paths.
  - * -> [Condition: Config review is incomplete] -> Action: Dead-end pivots — compare AAA logs, endpoint VPN posture logs, and help-desk exception workflows.
  - * -> [Condition: Weak remote-access policy is found] -> Action: Data chaining — feed exposed identities and network ranges into segmentation review and privileged-access review.

- SNMP, IPMI & Out-of-Band Management
  - * -> [Condition: Infrastructure devices or BMC interfaces exist] -> Action: Primary validation — inventory management protocols, verify version and exposure, review community-string or local-account policy, and confirm management-plane isolation.
  - * -> [Condition: Direct access is blocked] -> Action: Dead-end pivots — review device backups, NMS configuration, and switch/router ACLs.
  - * -> [Condition: Weak management exposure is found] -> Action: Data chaining — map the device role to upstream routing, switching, or virtualization dependencies so remediation is prioritized by operational impact.

## Pivoting, Automation & Evidence

NIST explicitly calls out coordination, analysis, and data handling as execution-stage concerns, and its appendices include a Rules of Engagement template plus recommendations for remote access testing.  That makes evidence normalization and chain-of-custody more important than offensive “next steps” when the goal is a defensible assessment record.

- Lateral Movement & Pivoting
  - * -> [Condition: Multiple internal segments or trust boundaries are in scope] -> Action: Primary validation — map approved management paths, jump hosts, trust links, and east-west ACL intent; document where administrative reach exceeds business need.
  - * -> [Condition: Reachability data is sparse] -> Action: Dead-end pivots — compare routing tables, NAC policy, and host firewall baselines.
  - * -> [Condition: Excessive trust or management reach is confirmed] -> Action: Data chaining — tie the path to specific accounts, ports, and admin tools so the finding is framed as control failure, not movement opportunity.

- Credential Harvesting & Exfiltration
  - * -> [Condition: Secrets handling or egress monitoring is in scope] -> Action: Primary validation — review vault usage, local secret sprawl, browser-stored credentials, DNS logging, proxy logs, mail egress policy, and DLP alert coverage.
  - * -> [Condition: No obvious weakness is visible] -> Action: Dead-end pivots — compare privileged workstation baselines, endpoint control exceptions, and service account secret distribution methods.
  - * -> [Condition: Secret sprawl or weak egress visibility is found] -> Action: Data chaining — map the issue to business systems, retention policies, and incident-detection gaps, then attach packet, log, and owner evidence.

- Complex script definition block: Exposure correlator
  - Input Data: Open-service CSV, CMDB export, patch inventory, device inventory, AD ownership map, ticketing export.
  - Core Processing Logic:
    - Join assets by hostname, IP, serial, and owner.
    - Flag unsupported protocols, end-of-life platforms, privileged-system exposure, and ownerless assets.
    - Add severity using exposure, privilege proximity, and control coverage.
    - Generate remediation queues grouped by team and maintenance window.
  - Dependencies: Python, `pandas`, CSV/JSON parsers.
  - Expected Output Format: `csv` for remediation queue, `jsonl` for machine-readable findings, `md` for analyst-ready notes.

- Reporting rule
  - Every finding should end in this shape: `asset -> control gap -> validation evidence -> affected trust boundary -> owner -> remediation -> retest date`.
  - Keep raw evidence in `/evidence/`, normalized datasets in `/reports/findings/`, and only analyst-written claims in `/reports/final/`.