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

