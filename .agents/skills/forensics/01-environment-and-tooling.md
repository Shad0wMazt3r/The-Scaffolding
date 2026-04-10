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

