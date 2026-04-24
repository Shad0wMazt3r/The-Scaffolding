## Memory Forensics

- Primary Probe
  - * -> [Condition: Image type is uncertain] -> Action: identify OS family first, then run `windows.pslist`/`windows.pstree` for Windows, `linux.pslist` plus `linux.bash` for Linux, or the macOS equivalents; use the first pass only to establish process graph, parent-child anomalies, and analyst targets.
  - * -> [Condition: Suspicious process tree exists] -> Action: collect `cmdline`, loaded modules, handles, network connections, environment strings, and VAD ranges; then dump only high-value processes.
  - * -> [Condition: Userland malware is suspected] -> Action: walk `windows.vadinfo` and compare mapped regions against PE headers, RX/RWX permissions, private executable pages, and unbacked regions indicative of reflective DLL injection or shellcode staging.

- Dead End Pivots
  - * -> [Condition: Standard plugins misidentify the image or return sparse output] -> Action: validate symbols, fall back to raw strings/YARA scans on the image, and target likely processes by known service names, browser names, or scripting engines.
  - * -> [Condition: No obvious malicious process appears] -> Action: check hidden/unlinked tasks via cross-view concepts, scan handles, mutexes, clipboard, console buffers, and shell history; CTF payloads often hide in PowerShell, Python, `rundll32`, `mshta`, `wscript`, browser helpers, or terminal sessions.
  - * -> [Condition: Encrypted traffic is visible but application content is absent] -> Action: inspect browser and TLS client processes for session secrets, URLs, cookies, and POST bodies in heap/strings regions before assuming the PCAP is opaque.

- Data Chaining
  - * -> [Condition: `cmdline` or console history shows Base64, gzip, XOR, or PowerShell] -> Action: decode it immediately and pivot any URLs, domains, mutex names, or filenames into PCAP and disk.
  - * -> [Condition: Browser memory yields cookies, bearer tokens, or TLS secrets] -> Action: use them to decrypt or replay application-layer sessions from the PCAP.
  - * -> [Condition: Credential material appears in LSASS, keychains, SSH agents, or shells] -> Action: test it against encrypted archives, password-protected stego files, mounted volumes, and lateral-movement shares.

- Simple one-liners
  - `python3 vol.py -f raw/mem.raw windows.pslist > memory/pslist.txt`
  - `python3 vol.py -f raw/mem.raw windows.cmdline --pid <PID> | tee memory/cmdline_<PID>.txt`
  - `strings -a raw/mem.raw | grep -Eoi 'flag\\{[^}]+\\}|ctf\\{[^}]+\\}|[A-Za-z0-9+/]{40,}={0,2}' > memory/interesting_strings.txt`

- Script Definition Block: TLS secret and browser pivot harvester
  - Input Data: dumped browser process memory, PCAP metadata, candidate hostnames/URIs.
  - Core Processing Logic:
    - Locate NSS/BoringSSL/OpenSSL-related structures or ASCII markers for key logging material.
    - Extract candidate client randoms, secrets, cookies, tokens, and WebSocket endpoints.
    - Validate each candidate against PCAP TLS handshakes and SNI values.
    - Emit a reusable key log plus a host-to-process mapping.
  - Dependencies: Volatility3 dumps, custom parser, Wireshark-compatible SSLKEYLOGFILE formatter.
  - Expected Output Format: `sslkeys.log` plus CSV `pid,process,hostname,client_random,secret_type,confidence`.

