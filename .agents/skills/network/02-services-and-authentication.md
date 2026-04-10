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

