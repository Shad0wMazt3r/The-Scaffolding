## Services & Authentication

### Network Services & Banner Grabbing

- **[Primary validation]** Identify live hosts, open ports, service banners, TLS posture, ownership → normalize to `/services/open-services.csv`
- **[Inconclusive probe]** Pivot: passive flow data, firewall/NAT rules, authenticated config review
- **[Legacy/unmanaged confirmed]** Data Chaining: feed host/port/owner/version → patch review → cred exposure → segmentation

**Parsing Helpers:**
```bash
xmlstarlet sel -t -m '//port[state/@state="open"]' -v '../../address/@addr' -o ',' -v '@portid' -o ',' -v 'service/@name' -n full.xml | sort -u > open-services.csv
awk -F, '$3 ~ /(ftp|telnet|snmp|ldap|rdp|smb|ssh)/ {print}' open-services.csv > auth-surface.csv
```

### Authentication Attacks (Brute Force, Pass-the-Hash, Kerberoasting, AS-REP)

- **[Kerberos/NTLM/LDAP/RDP/SMB/SSH/VPN present]** Review lockout policy, password policy, SPN inventory, preauthentication, delegation, NTLM usage, privileged account placement
- **[No obvious weakness]** Pivot: GPO drift, interactive logon vs admin tiers, service account lifecycle/rotation
- **[Weak service-account hygiene or delegation found]** Data Chaining: privilege review → secure-admin-host coverage → tier boundary validation

***
