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
