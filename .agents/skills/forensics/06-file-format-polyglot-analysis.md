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

