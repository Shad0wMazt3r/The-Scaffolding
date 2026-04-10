---
name: forensics
description: Coordinate forensic investigation across image, memory, network, stego, format, log, multimedia, and timeline phases with disciplined data validation.
dependencies: [agent-setup, agent-calibration]
files:
  - 01-environment-and-tooling.md
  - 02-disk-image-analysis.md
  - 03-memory-forensics.md
  - 04-network-pcap-analysis.md
  - 05-steganography.md
  - 06-file-format-polyglot-analysis.md
  - 07-log-artifact-analysis.md
  - 08-multimedia-forensics.md
  - 09-cryptographic-artifact-recovery.md
  - 10-timeline-reconstruction-and-correlation.md
---

Load files sequentially on activation: see files list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.



