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
