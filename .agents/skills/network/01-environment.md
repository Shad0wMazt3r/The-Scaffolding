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

