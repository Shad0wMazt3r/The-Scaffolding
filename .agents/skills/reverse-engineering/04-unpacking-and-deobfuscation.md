## Unpacking & Deobfuscation

- Primary Probe
  - * -> [Condition: UPX or known packer signature present] -> Action: try native unpacker first, then validate sections, IAT, relocations, and OEP before trusting the result.
  - * -> [Condition: Custom packer suspected] -> Action: trace `VirtualAlloc`/`VirtualProtect`/`WriteProcessMemory`/`mmap`/`mprotect`, break on execution from newly written pages, and dump memory at the first stable OEP.
  - * -> [Condition: Encoded strings/config] -> Action: search for tight XOR/ROL/RC4-like loops, repeated small-key usage, or decode-then-compare patterns; pair static recognition with runtime buffer capture.
  - * -> [Condition: Self-modifying code] -> Action: log memory writes to executable regions and diff page snapshots before and after major dispatcher transitions.
- Dead End Pivots
  - * -> [Condition: OEP never stabilizes] -> Action: switch to DBI-based write tracing and reconstruct stage boundaries from control transfers into freshly materialized code.
  - * -> [Condition: Static decode loop not obvious] -> Action: search backward from plaintext use-sites, especially `strcmp`/`memcmp`/formatting/network send calls, to the last writer of the compared buffer.
  - * -> [Condition: Import table is destroyed] -> Action: rebuild imports from thunk usage, syscall stubs, API hash resolvers, and dynamic loader traces.
- Data Chaining
  - * -> [Condition: New stage dump obtained] -> Action: treat it as a fresh binary, re-run triage/static analysis, and preserve stage lineage in `unpacked/stageN`.
  - * -> [Condition: Decoder recovered] -> Action: batch-decode all referenced blobs and use results to rename code paths and seed symbolic constraints.
  - * -> [Condition: API hash resolver understood] -> Action: resolve hashed imports and feed names back into disassembler annotations.

angr’s documentation explicitly recommends mixing concrete Unicorn-backed execution with symbolic execution when unpacking or self-modification would make pure symbolic emulation too slow.  Unicorn is derived from QEMU internals and uses translated basic-block caching, so any workflow that patches executing code must account for translation-cache invalidation or a controlled restart at the current PC. [docs.angr](https://docs.angr.io/en/latest/examples.html)

Simple one-liners:
- `upx -d sample -o unpacked/stage1/sample.upx.out`
- `binwalk -Me firmware.bin -C firmware/binwalk/`
- `python3 -c "from pwn import *; d=open('blob','rb').read(); print(xor(d,0x41)[:128])"`

Script Definition Block — staged unpack monitor
- Input Data: memory map events, page permissions, write traces, executed-address timeline.
- Core Processing Logic:
  - Track writes into non-image or newly RWX pages.
  - Mark transitions where execution enters recently written regions.
  - Snapshot memory and metadata at candidate OEPs.
  - Rebuild PE/ELF headers if missing; emit import-rebuild candidates.
- Dependencies: Frida or DynamoRIO, pefile/LIEF, Capstone.
- Expected Output Format: directory per stage with `dump.bin`, `map.json`, `oep.txt`, `imports.json`.

