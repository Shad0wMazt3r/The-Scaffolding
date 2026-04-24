# Forensics - TTPs

**Workspace:** Clean forensic VM, snapshot before destructive operations, hash every source + derivative.

```
/forensics/<challenge>/
├── raw/          # original artifacts, immutable
├── mount/        # read-only mounts, partition subdirs
├── memory/       # mem dumps, process dumps, strings, yara
├── network/      # pcaps, extracted streams, JA3/JA4
├── stego/        # carriers, extracted bitplanes, spectrograms
├── timeline/     # bodyfiles, mactime, CSV/JSON
├── evidence/     # tagged findings, decoded payloads
├── logs/         # command transcripts, tool output
└── notes/        # hypothesis tracking, pivot map
```

**Environment:** Use write blocking for physical media. Treat `raw/` immutable; mount partitions read-only.

- Volatility 3: plugins via `volatility3.plugins` namespace
- Autopsy: ingest modules configure on data-source add; timeline in ingest (4.13+)
- Wireshark/TShark: `-Y` for display filters
- Steghide: JPEG/BMP/WAV/AU support; `gem install zsteg` for PNG
- Bulk Extractor: carves binaries/logs/URLs

**Install Baseline:**
```bash
sudo apt install autopsy sleuthkit testdisk foremost scalpel bulk-extractor exiftool binwalk wireshark tshark ffmpeg imagemagick steghide outguess john hashcat yara ssdeep sqlite3 jq gnuplot python3-pip
sudo gem install zsteg
pip install volatility3 yara-python pefile pillow numpy scipy matplotlib pycryptodome oletools
```

**Mount & Snapshot:**
```bash
sha256sum raw/* | tee logs/hashes.sha256
mmls raw/disk.img | tee logs/mmls.txt
sudo losetup -fP --read-only raw/disk.img && sudo mount -o ro /dev/loop0p1 mount/p1
```

***
