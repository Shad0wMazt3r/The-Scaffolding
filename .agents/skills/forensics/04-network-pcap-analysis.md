## Network PCAP Analysis

- Primary Probe
  - * -> [Condition: Capture is large or noisy] -> Action: begin with protocol hierarchy, endpoints, conversations, DNS, HTTP, TLS, SMB2, FTP, and ICMP; reduce to suspected time windows and client IPs first. TShark supports protocol analysis and uses the same display-filter syntax as Wireshark, with `-Y` for display filters. [wireshark](https://www.wireshark.org/docs/man-pages/wireshark-filter.html)
  - * -> [Condition: Application protocols are present] -> Action: reconstruct streams, export files/objects, and inspect hostnames, user agents, cookies, POST bodies, uploads, DNS TXT, and tunneled content.
  - * -> [Condition: Lateral movement or file transfer is likely] -> Action: reassemble SMB2, HTTP, FTP, or email attachments; look for staged binaries, scripts, archives, or screenshot exfiltration.

- Dead End Pivots
  - * -> [Condition: Everything is TLS or QUIC] -> Action: correlate SNI, JA3/JA4-style client patterns, timing, packet sizes, and extracted TLS secrets from memory to recover content.
  - * -> [Condition: No clear C2 stands out] -> Action: inspect low-and-slow beacons, evenly spaced keepalives, rare domains, DNS TXT, odd ICMP payloads, and small POST bursts to single hosts.
  - * -> [Condition: Streams are fragmented or malformed] -> Action: rebuild by `tcp.stream`, reassemble HTTP chunking/compression manually, and inspect packet payloads with hex export for off-spec or custom framing.

- Data Chaining
  - * -> [Condition: DNS or HTTP reveals a file path] -> Action: match the filename and timestamp on disk, then seek the executing process in memory.
  - * -> [Condition: SMB2 file copy or remote execution appears] -> Action: pivot into Prefetch, Event Logs, shellbags, and service creation artifacts on the disk image.
  - * -> [Condition: Authentication material is observed] -> Action: test recovered creds against archives, encrypted documents, stego passphrases, or remote shares referenced elsewhere.

- Simple one-liners
  - `tshark -r raw/challenge.pcapng -q -z io,phs > network/protocol_hierarchy.txt`
  - `tshark -r raw/challenge.pcapng -Y 'http.request || dns || tls.handshake.type==1 || smb2' -T fields -e frame.time -e ip.src -e ip.dst -e _ws.col.Protocol -e _ws.col.Info > network/triage.tsv`
  - `tshark -r raw/challenge.pcapng -Y 'frame contains "flag{" || frame matches "(?i)ctf\\{"' -x > network/raw_flag_hits.txt`

- Script Definition Block: SMB2 reconstruction and host correlation
  - Input Data: PCAP, recovered hostnames/IPs, disk timeline.
  - Core Processing Logic:
    - Identify SMB2 CREATE/READ/WRITE/CLOSE sequences by file ID.
    - Reassemble transferred content in order, preserving timestamps and share paths.
    - Correlate copied filenames with Prefetch, LNKs, RecentDocs, and execution events.
    - Score probable lateral-movement artifacts such as PsExec-style service binaries or renamed tools.
  - Dependencies: Tshark field export, SMB2 parser, timeline joiner.
  - Expected Output Format: JSON and CSV with `share,path,sha256,first_seen,last_seen,related_host,execution_evidence`.

