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

