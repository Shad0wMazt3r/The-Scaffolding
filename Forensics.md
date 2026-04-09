# Forensics - TTPs

Use a clean forensic VM, snapshot before every destructive branch, and preserve a hash ledger for each source plus every carved derivative.

`/forensics/<challenge>/`
```text
/forensics/<challenge>/
├── raw/           # original artifacts, immutable
├── mount/         # read-only mounts, partition subdirs
├── memory/        # mem dumps, process dumps, strings, yara hits
├── network/       # pcaps, extracted streams, JA3/JA4, smb/http objects
├── stego/         # carrier files, extracted bitplanes, palettes, spectrograms
├── timeline/      # bodyfiles, mactime outputs, merged CSV/JSON
├── evidence/      # tagged findings, decoded payloads, recovered flags
├── logs/          # command transcripts, tool stdout/stderr
└── notes/         # hypothesis tracking, pivot map, challenge graph
```

Environment baseline:
- Use hardware or software write blocking for physical media; for image files, treat `raw/` as immutable and mount every partition read-only.
- Volatility 3 loads plugins from the `volatility3.plugins` namespace, and `windows.pslist` is the standard process-listing plugin for Windows memory images. [arxiv](https://arxiv.org/pdf/1908.08269.pdf)
- In Autopsy, ingest modules are configured immediately after a data source is added, and timeline events are generated during ingest in Autopsy 4.13+ cases. [sleuthkit](http://sleuthkit.org/autopsy/docs/user-docs/4.22.0/timeline_page.html)
- Wireshark and TShark share the same display-filter engine, and TShark applies display filters with `-Y`. [wireshark](https://www.wireshark.org/docs/man-pages/tshark.html)
- Steghide is installed with `sudo apt install steghide`, exposes `embed`, `extract`, and `info`, and supports common cover formats including JPEG, BMP, WAV, and AU; `zsteg` is installed with `gem install zsteg`. [kali](https://www.kali.org/tools/steghide/)

Tooling baseline:
```bash
sudo apt update
sudo apt install autopsy sleuthkit testdisk foremost scalpel bulk-extractor exiftool binwalk foremost wireshark tshark ffmpeg imagemagick steghide outguess john hashcat yara ssdeep sqlite3 jq gnuplot python3-pip
sudo gem install zsteg
python3 -m pip install volatility3 yara-python pefile pillow numpy scipy matplotlib pycryptodome oletools
```

Mount and snapshot baseline:
```bash
# hash first
sha256sum raw/* | tee logs/source_hashes.sha256

# list partitions
mmls raw/disk.img | tee logs/mmls.txt

# loop attach read-only
sudo losetup -fP --read-only raw/disk.img
sudo mount -o ro,norecover /dev/loop0p1 mount/p1

# EWF example
ewfmount raw/disk.E01 mount/ewf
sudo mount -o ro,loop,show_sys_files,streams_interface=windows mount/ewf/ewf1 mount/p1
```

Volatility3 and case setup:
- Keep symbols under `~/.cache/volatility3/` or a case-local mirror, then validate the image with `windows.info`, `linux.banner`, or `mac.banner` before target plugins.
- Autopsy case: one host per suspected endpoint, add each artifact as a separate data source, enable Recent Activity, Hash Lookup, File Type Identification, Embedded File Extractor, Interesting Files, Extension Mismatch, and Timeline.
- Forensic VM procedure: snapshot at `clean-base`, `after-ingest`, `after-carving`, `after-decryption`, and `after-custom-script`; revert instead of “cleaning up.”

Wireshark/TShark filter library:
```text
http || dns || tls || smb2 || kerberos || ftp || icmp
tcp.stream eq N
http.request || http.response
dns.qry.name contains "flag" || dns.txt
tls.handshake.type == 1 || tls.handshake.type == 2
tcp.flags.syn == 1 && tcp.flags.ack == 0
smb2 || smb || dcerpc
ftp.request.command == "USER" || ftp.request.command == "PASS"
http.authorization || ftp || imap || pop || smtp.auth
frame contains "flag{" || frame matches "(?i)ctf\\{|flag\\{"
```

## Disk Image Analysis

- Primary Probe
  - * -> [Condition: Partition table parses cleanly] -> Action: enumerate partitions with `mmls`, identify FS type with `fsstat`, mount each partition read-only, and build a quick map of user directories, temp paths, browser stores, shell history, recycle/trash, and unallocated regions.
  - * -> [Condition: Filesystem is NTFS] -> Action: prioritize `$MFT`, `$LogFile`, `$UsnJrnl`, `$Recycle.Bin`, Prefetch, LNK, Jump Lists, ADS, and Volume Shadow Copies; treat timestamp collisions as potential timestomping.
  - * -> [Condition: Filesystem is ext4/APFS/HFS+/XFS] -> Action: prioritize journal/log replay, orphan inodes, shell history, SSH keys, browser profiles, and user cache paths; check for sparse-file abuse and hidden mountpoints.

- Dead End Pivots
  - * -> [Condition: GPT/MBR is corrupt or missing] -> Action: recover partitions with `testdisk`, then carve by offset using `fdisk -lu` math and `mount -o ro,loop,offset=<bytes>`.
  - * -> [Condition: Autopsy misses deleted records or anti-forensics is suspected] -> Action: parse `$MFT`/inodes manually, examine `$UsnJrnl` for create-delete bursts, and compare directory entries against recovered slack/unallocated content.
  - * -> [Condition: Files look benign but challenge behavior implies hidden payloads] -> Action: run entropy triage, inspect slack space and ADS, then carve raw sectors or clusters with `blkls`, `foremost`, or targeted `dd`.

- Data Chaining
  - * -> [Condition: Browser artifacts reveal a download, URI, or paste site] -> Action: pivot the URI, hostname, and timestamps into PCAP, DNS, and memory-resident browser processes.
  - * -> [Condition: Prefetch/LNK/Jump Lists show an executable path or archive] -> Action: recover the binary or container, reverse the Prefetch hash if needed, then compare execution time against memory process start times.
  - * -> [Condition: A script, macro, or note references a password] -> Action: test it against encrypted archives, stego passphrases, VeraCrypt volumes, and office documents before brute-forcing.

- Simple one-liners
  - `fls -r -m / raw/disk.img > timeline/bodyfile.txt`
  - `icat -r raw/disk.img <inode_or_mft_entry> > evidence/recovered.bin`
  - `dd if=raw/disk.img of=evidence/carve.bin bs=512 skip=<start_sector> count=<sector_count>`

- Script Definition Block: NTFS anti-forensic delta detector
  - Input Data: `$MFT`, `$UsnJrnl`, `$LogFile`, Prefetch metadata, LNK timestamps.
  - Core Processing Logic:
    - Parse all MACB values and normalize to UTC.
    - Flag files with improbable create/modify/access sequences.
    - Correlate journaled create-delete-rename bursts against surviving records.
    - Surface ADS-bearing files, duplicate names with divergent file IDs, and executable paths referenced only by shortcuts or Prefetch.
  - Dependencies: MFTECmd/analyzers, UsnJrnl parser, CSV normalizer.
  - Expected Output Format: CSV with `path,file_id,event_source,timestamp,anomaly_score,next_pivot`.

## Memory Forensics

- Primary Probe
  - * -> [Condition: Image type is uncertain] -> Action: identify OS family first, then run `windows.pslist`/`windows.pstree` for Windows, `linux.pslist` plus `linux.bash` for Linux, or the macOS equivalents; use the first pass only to establish process graph, parent-child anomalies, and analyst targets. [arxiv](https://arxiv.org/pdf/1908.08269.pdf)
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

## Steganography

- Primary Probe
  - * -> [Condition: Carrier is an image or audio file] -> Action: start with `file`, `exiftool`, `binwalk`, `strings`, and `steghide info`; then inspect dimensions, channels, palette, compression, and metadata for contradictions. Steghide exposes `info` and `extract` for candidate stego files. [manpages.ubuntu](https://manpages.ubuntu.com/manpages/trusty/man1/steghide.1.html)
  - * -> [Condition: Carrier is PNG or BMP] -> Action: run `zsteg -a` first, then inspect per-channel bit planes, alpha channel, palette ordering, and trailing bytes. `zsteg` is designed to detect hidden data in PNG and BMP, and installs via RubyGems. [github](https://github.com/zed-0xff/zsteg)
  - * -> [Condition: Carrier is JPEG or audio] -> Action: favor metadata, binwalk, appended payload checks, quantization/DCT anomalies, and spectrogram analysis over naive LSB assumptions.

- Dead End Pivots
  - * -> [Condition: Steghide/binwalk returns nothing] -> Action: check for appended archives, trailing ZIP/RAR headers, split payloads across multiple carriers, and entropy spikes in footer or comment segments.
  - * -> [Condition: Visible image looks normal and LSB tools fail] -> Action: inspect individual RGB/A bit planes, palette index ordering, Unicode whitespace in companion text, and filename/EXIF comments as covert channels.
  - * -> [Condition: JPEG challenge implies frequency-domain hiding] -> Action: compare DCT coefficient distributions, quantization tables, restart markers, and recompression artifacts; treat social-media recompression clues as part of the puzzle.

- Data Chaining
  - * -> [Condition: Extracted payload is an archive, script, or key] -> Action: pass it to file-format analysis, password testing, and memory/disk correlation.
  - * -> [Condition: EXIF/comment fields contain coordinates, timestamps, or tool names] -> Action: pivot into logs, browser history, or challenge infrastructure naming patterns.
  - * -> [Condition: Multi-image set shares near-identical visuals] -> Action: diff pixels, palettes, or audio phase against the entire set; CTF authors often shard flags across “almost identical” files.

- Simple one-liners
  - `steghide info raw/carrier.jpg`
  - `zsteg -a raw/carrier.png > stego/zsteg_all.txt`
  - `python3 -c "from PIL import Image;import numpy as np;im=np.array(Image.open('raw/carrier.png'));Image.fromarray(((im[:,:,0]&1)*255).astype('uint8')).save('stego/r_lsb.png')"`

- Script Definition Block: JPEG DCT anomaly scanner
  - Input Data: JPEG carrier set, optional known-clean comparison set.
  - Core Processing Logic:
    - Parse quantization tables and coefficient histograms by block and channel.
    - Detect biased low-frequency/AC distributions inconsistent with natural recompression.
    - Compare coefficient populations across sibling images for sharded embedding.
    - Export suspicious block coordinates and channel-level heatmaps.
  - Dependencies: JPEG parser, numpy/scipy, visualization helper.
  - Expected Output Format: CSV `file,channel,block_x,block_y,score` plus PNG heatmaps.

## File Format & Polyglot Analysis

- Primary Probe
  - * -> [Condition: File type and extension disagree] -> Action: validate magic bytes, container structure, footer markers, and internal offsets; then open with both the declared parser and the actual-format parser.
  - * -> [Condition: Unknown blob or oversized document appears] -> Action: run `binwalk -e`, inspect with hex, identify embedded archives, and verify whether multiple valid headers coexist.
  - * -> [Condition: Office/PDF/media container is suspected as a wrapper] -> Action: enumerate streams, OLE objects, XMP, appended data, and object offsets before touching content macros.

- Dead End Pivots
  - * -> [Condition: Binwalk yields no extraction] -> Action: scan manually for `PK\x03\x04`, `Rar!`, `%PDF`, `7z\xBC\xAF`, ELF, PE, or SQLite signatures and carve by offset.
  - * -> [Condition: Header is broken or challenge intentionally corrupts it] -> Action: repair the minimum required bytes, length fields, or checksums in a working copy, then retry parsers.
  - * -> [Condition: Polyglot behavior is suspected] -> Action: test both front-loaded and appended payload interpretations, including image+zip, pdf+js, png+sqlite, and wav+tar hybrids.

- Data Chaining
  - * -> [Condition: Embedded archive is extracted] -> Action: pass password hints to cryptographic recovery and push recovered documents into log/browser/disk analysis.
  - * -> [Condition: Container metadata references creator software or usernames] -> Action: pivot into OS-specific recent files, shell history, and PCAP hostnames.
  - * -> [Condition: Repaired file exposes a second-stage script] -> Action: correlate script timestamps and names against memory process trees and filesystem artifacts.

- Simple one-liners
  - `xxd -l 64 raw/suspect.bin`
  - `binwalk -eM raw/suspect.bin`
  - `grep -aboP 'PK\x03\x04|Rar!' raw/suspect.bin`

## Log & Artifact Analysis

- Primary Probe
  - * -> [Condition: Windows artifacts exist] -> Action: pull Event Logs from `%SystemRoot%\\System32\\winevt\\Logs\\`, Registry hives from `Windows\\System32\\config\\`, user hives from `NTUSER.DAT`/`UsrClass.dat`, Prefetch from `Windows\\Prefetch\\`, and browser data from Chromium/Edge/Firefox profiles.
  - * -> [Condition: Linux artifacts exist] -> Action: inspect `/var/log/`, `/var/log/journal/`, shell histories, cron/anacron, systemd units, SSH keys, `.bash_history`, `.zsh_history`, and package manager logs.
  - * -> [Condition: macOS artifacts exist] -> Action: inspect Unified Logs, `~/Library/Preferences/`, browser SQLite stores, LaunchAgents/Daemons, recent items, quarantine events, and FSEvents.

- Dead End Pivots
  - * -> [Condition: Event coverage is sparse or wiped] -> Action: recover `.evtx` from unallocated space, compare hive transaction logs, and use Prefetch/LNK/Jump Lists to backfill execution.
  - * -> [Condition: Browser history is cleared] -> Action: mine cache, session restore files, cookies, downloads DBs, favicons, and recovered SQLite freelists.
  - * -> [Condition: Registry or syslog evidence is partial] -> Action: correlate USB, network profile, MRU, Run/RunOnce, service, and SSH known_hosts artifacts to rebuild operator behavior.

- Data Chaining
  - * -> [Condition: Logon or service creation appears] -> Action: pivot to PCAP lateral-movement windows and memory-resident service processes.
  - * -> [Condition: Downloaded filename or URL is found] -> Action: search the disk image, then match network transfer and execution evidence.
  - * -> [Condition: Browser token, cookie, or form fill is recovered] -> Action: test it against web session replay, archive passwords, or challenge portals.

- Simple one-liners
  - `sqlite3 'History' 'select datetime(last_visit_time/1000000-11644473600,"unixepoch"),url,title from urls order by last_visit_time desc;'`
  - `find mount/ -iname '*.evtx' -o -iname 'NTUSER.DAT' -o -iname 'UsrClass.dat' > logs/artifact_paths.txt`
  - `grep -RinE 'flag\\{|ctf\\{|pass|token|key' mount/Users mount/home 2>/dev/null > logs/keyword_hits.txt`

## Multimedia Forensics

- Primary Probe
  - * -> [Condition: Audio file is present] -> Action: inspect metadata, convert to spectrogram, listen for channel imbalance/reversal, and test for appended archives or SSTV/DTMF/Morse-like encodings.
  - * -> [Condition: Video file is present] -> Action: extract frames, thumbnails, subtitles, audio tracks, and container metadata; check for single-frame inserts, QR flashes, or timing-encoded content.
  - * -> [Condition: Photo set is present] -> Action: review EXIF, geotags, orientation inconsistencies, camera serials, and sensor-pattern continuity across the set.

- Dead End Pivots
  - * -> [Condition: Nothing obvious appears in playback] -> Action: analyze individual channels, reverse playback, slow down timing, and inspect frame deltas or hidden subtitle/data tracks.
  - * -> [Condition: EXIF is stripped] -> Action: compare file naming, thumbnails, JPEG quant tables, maker-note remnants, and edit history indicators.
  - * -> [Condition: Multiple files look near-duplicate] -> Action: run image/video differencing and audio subtraction; CTF flags often live in differences, not absolute content.

- Data Chaining
  - * -> [Condition: Spectrogram or frame yields text/QR/key] -> Action: send it to cryptographic recovery or file-format analysis immediately.
  - * -> [Condition: Geolocation or clock data appears] -> Action: align it with logins, transfers, and filesystem events in the global timeline.
  - * -> [Condition: Camera fingerprint or editing signature emerges] -> Action: use it to cluster authentic vs tampered files and isolate the carrier that matters.

- Simple one-liners
  - `ffmpeg -i raw/audio.wav -lavfi showspectrumpic=s=1920x1080 stego/spectrogram.png`
  - `ffmpeg -i raw/video.mp4 -vf fps=1 stego/frames/frame_%05d.png`
  - `exiftool -a -u -g1 raw/mediafile > stego/exif_full.txt`

## Cryptographic Artifact Recovery

- Primary Probe
  - * -> [Condition: Encrypted archive, volume, or blob is present] -> Action: identify format first, then separate “find key material” from “attack password”; do not brute-force until you have harvested every hint from memory, notes, logs, filenames, and metadata.
  - * -> [Condition: Memory image exists] -> Action: search for passphrases, key files, wallet seeds, SSH private keys, browser-saved secrets, and mounted-volume indicators before touching hashcat.
  - * -> [Condition: Password hashes or tickets are exposed] -> Action: extract them cleanly, classify the scheme, and prioritize smart wordlists from case artifacts over generic masks.

- Dead End Pivots
  - * -> [Condition: Password guesses fail] -> Action: derive candidate rules from usernames, hostnames, challenge titles, timestamps, leetspeak, and file metadata rather than expanding brute force blindly.
  - * -> [Condition: Volume header is damaged] -> Action: carve backup headers, inspect nearby sectors or appended keyfiles, and test repaired headers on copies only.
  - * -> [Condition: Archive opens but content is still opaque] -> Action: look for nested XOR/base64/compression layers and treat “decrypted” output as a new artifact, not an endpoint.

- Data Chaining
  - * -> [Condition: Recovered key decrypts PCAP/TLS/archive content] -> Action: push the plaintext back into timeline, network, and file-format analysis.
  - * -> [Condition: Hash cracking reveals user password reuse] -> Action: test it against steghide, ZIP/7z, VeraCrypt, browser profiles, and note files.
  - * -> [Condition: Keyfile path is referenced in logs or LNKs] -> Action: recover that file from disk or carve it from unallocated space.

- Simple one-liners
  - `strings -a raw/mem.raw | grep -Ei 'pass|pwd|secret|token|key|wallet|seed' > memory/crypto_hints.txt`
  - `zip2john evidence/archive.zip > evidence/archive.hash`
  - `7z2hashcat.pl evidence/archive.7z > evidence/archive_7z.hash`

## Timeline Reconstruction & Correlation

- Primary Probe
  - * -> [Condition: At least two artifact classes have timestamps] -> Action: normalize all times to UTC, record source timezone assumptions separately, and build a single event table from FS MACB, logs, browser history, Prefetch, PCAP frame times, and memory process times.
  - * -> [Condition: Windows filesystem is involved] -> Action: include `$MFT`, `$UsnJrnl`, `$LogFile`, Prefetch run counts, LNK/Jump List access times, and Event Log records to catch timestomping or delete/recreate cycles.
  - * -> [Condition: Linux/macOS filesystem is involved] -> Action: include inode times, journal traces, shell history, launch/cron/service artifacts, browser SQLite times, and FSEvents/Unified Log equivalents.

- Dead End Pivots
  - * -> [Condition: Timestamps conflict across sources] -> Action: prefer source-native event semantics over wall-clock intuition, then test for timezone shifts, clock skew, or deliberate tampering.
  - * -> [Condition: Large gaps appear] -> Action: backfill from network frame times, browser caches, journal records, VSS/snapshots, and recovered deleted artifacts.
  - * -> [Condition: Multiple candidate attack chains exist] -> Action: score each chain by cross-source support, not by narrative neatness; CTFs often include decoys.

- Data Chaining
  - * -> [Condition: A coherent sequence emerges] -> Action: express it as `initial access -> staging -> execution -> credential/key harvest -> exfil/decryption -> flag assembly`, then test every link against at least one independent artifact class.
  - * -> [Condition: Flag fragments appear in different media] -> Action: order them by event time and creation lineage before concatenating; many composite CTFs hide fragment order inside the timeline itself.
  - * -> [Condition: Final flag candidate is formed] -> Action: verify encoding layers, delimiters, and challenge-specific conventions such as `flag{}`, `ctf{}`, hex, Base64, XOR, ROT, gzip, or sharded fragments before submission.

- Simple one-liners
  - `mactime -b timeline/bodyfile.txt -d > timeline/fs_timeline.csv`
  - `tshark -r raw/challenge.pcapng -T fields -e frame.time_epoch -e ip.src -e ip.dst -e _ws.col.Protocol -e _ws.col.Info > timeline/pcap_times.tsv`
  - `python3 -c "import pandas as p;df=p.concat([p.read_csv('timeline/fs_timeline.csv'),p.read_csv('timeline/other.csv')],ignore_index=True);df.sort_values(df.columns[0]).to_csv('timeline/merged.csv',index=False)"`

Operational heuristics:
- Treat every recovered string as one of five types: locator, credential, decoder hint, execution trace, or decoy.
- Promote only evidence with a pivot target; do not dump everything into `evidence/`.
- In CTF composites, the most valuable path is usually cross-artifact: disk note -> memory command line -> PCAP stream -> stego passphrase -> encrypted archive -> flag fragment.