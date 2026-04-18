**State transition rules**

- Promote data only after a validation gate.
- Any newly discovered hostname loops back to `Subdomains -> S0`.
- Any newly discovered IP loops back to `IP Addresses -> I0`.
- Any cloud indicator loops to `Cloud Assets -> C0`.
- Any live endpoint or JS artifact loops to `JS Files -> J1`.
- Any phase with fewer than 3 net-new assets triggers its corresponding **Dead End Pivot** branch instead of continuing forward.

**Minimal orchestration order**

1. `scope/root-domains.txt`
2. `subfinder -> subdomains/all.txt` [projectdiscovery](https://docs.projectdiscovery.io/tools/subfinder/overview)
3. `dnsx -> subdomains/resolved/all.txt`
4. `httpx -> hosts/httpx/httpx.jsonl` [projectdiscovery](https://docs.projectdiscovery.io/tools/httpx/overview)
5. `katana/archive -> js/urls/all.txt` [projectdiscovery](https://docs.projectdiscovery.io/tools/katana/overview)
6. `IP/cloud/JS pivots -> feed discoveries back upstream`

This keeps the workflow recursive instead of linear, which is the right shape for high-yield recon in large bug-bounty programs.
