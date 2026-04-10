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

