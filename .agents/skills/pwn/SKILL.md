---
name: pwn
description: Advance pwn workflows from environment setup into stack, heap, format-string, UAF, integer, TOCTOU, kernel, and shellcode exploitation.
dependencies: []
files:
  - 01-environment-baseline.md
  - 02-stack-based-overflows.md
  - 03-heap-exploitation.md
  - 04-format-string-attacks.md
  - 05-use-after-free-and-type-confusion.md
  - 06-integer-overflows-and-signedness.md
  - 07-off-by-one-and-null-byte-overflows.md
  - 08-race-conditions-and-toctou.md
  - 09-kernel-exploitation.md
  - 10-sandbox-and-vm-escape.md
  - 11-shellcoding-and-restricted-environment-bypass.md
  - 12-firmware-and-embedded-binary.md
---

Load files sequentially on activation: see iles list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.
