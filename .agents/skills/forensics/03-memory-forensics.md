## Memory Forensics

### Primary Probe

- **[Image type uncertain]** Identify OS, run `windows.pslist`/`pslist` (Windows), `linux.pslist`/`linux.bash` (Linux) → process graph, parent-child anomalies, targets
- **[Suspicious process tree]** Collect `cmdline`, modules, handles, connections, environment, VAD ranges → dump high-value processes
- **[Userland malware suspected]** Walk `windows.vadinfo` → compare mapped regions vs PE headers, RX/RWX perms, private executable pages, unbacked regions (reflective DLL, shellcode)

### Dead End Pivots

- **[Standard plugins fail/sparse]** Validate symbols, fall back to raw strings/YARA, target by service names/browser/scripting engines
- **[No obvious malware]** Check hidden/unlinked tasks, handles, mutexes, clipboard, console buffers, shell history; CTF payloads hide in PowerShell, Python, rundll32, mshta, wscript, browser helpers
- **[Encrypted traffic visible, no app content]** Inspect browser/TLS for session secrets, URLs, cookies, POST in heap/strings before assuming opaque

### Data Chaining

- **[cmdline shows Base64/gzip/XOR/PowerShell]** Decode immediately → pivot URLs/domains/mutex/filenames to PCAP/disk
- **[Browser memory yields tokens/TLS secrets]** Use to decrypt/replay app-layer sessions from PCAP
- **[Creds in LSASS/keychains/SSH/shells]** Test against encrypted archives, stego, volumes, lateral-movement shares

### One-Liners

```bash
python3 vol.py -f raw/mem.raw windows.pslist > memory/pslist.txt
python3 vol.py -f raw/mem.raw windows.cmdline --pid <PID> | tee memory/cmdline_<PID>.txt
strings -a raw/mem.raw | grep -Eoi 'flag\{[^}]+\}|ctf\{[^}]+\}|[A-Za-z0-9+/]{40,}={0,2}' > memory/interesting_strings.txt
```

***
