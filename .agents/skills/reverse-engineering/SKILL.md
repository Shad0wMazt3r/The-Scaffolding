---
name: reverse-engineering
description: Progress binary analysis from sample intake through static, anti-analysis, unpacking, dynamic tracing, VM reverse engineering, and symbolic review.
dependencies: []
files:
  - 01-baseline-and-initial-triage.md
  - 02-static-disassembly-and-decompilation.md
  - 03-anti-analysis-bypass.md
  - 04-unpacking-and-deobfuscation.md
  - 05-dynamic-analysis-and-tracing.md
  - 06-custom-virtual-machine-reversing.md
  - 07-symbolic-and-concolic-execution.md
  - 08-algorithm-identification-and-reimplementation.md
  - 09-firmware-and-embedded-re.md
  - 10-dotnet-jvm-scripting-language-re.md
---

Load files sequentially on activation: see iles list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.
