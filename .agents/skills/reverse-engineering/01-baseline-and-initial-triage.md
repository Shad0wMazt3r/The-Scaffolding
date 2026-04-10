# Reverse Engineering - TTPs

## Initial Triage

Ghidra should be the default shared static-analysis platform here because the official release expects a 64-bit JDK 21, supports disassembly, decompilation, graphing, scripting, many processor families, and both interactive and automated use.  FLOSS installs with `pip install flare-floss`, while capa supports both standalone binaries and `pip`-based installation as `flare-capa`, so both belong in the base image instead of being rebuilt per target.  Binary Ninja’s Python API supports interactive console use, headless scripts, and plugins, and x64dbg plugins load by dropping `.dp32` or `.dp64` files into its `plugins` directory. [arxiv](https://arxiv.org/abs/2407.16132)

```text
/re/<target>/
├── evidence/
│   ├── hashes/
│   ├── notes/
│   ├── screenshots/
│   ├── pcaps/
│   └── timeline/
├── input/
│   ├── original/
│   ├── renamed/
│   └── samples/
├── ghidra/
│   ├── project/
│   ├── exports/
│   ├── scripts/
│   └── types/
├── ida/
│   ├── databases/
│   ├── scripts/
│   └── lumina_off/
├── binja/
│   ├── bndb/
│   ├── scripts/
│   └── types/
├── dynamic/
│   ├── traces/
│   ├── dumps/
│   ├── frida/
│   ├── drio/
│   ├── gdb/
│   └── x64dbg/
├── unpacked/
│   ├── stage0/
│   ├── stage1/
│   ├── stage2/
│   └── oep/
├── firmware/
│   ├── binwalk/
│   ├── squashfs/
│   ├── qemu/
│   └── nvram/
├── vm/
│   ├── bytecode/
│   ├── opcode_maps/
│   ├── traces/
│   └── lifts/
├── scripts/
│   ├── one_liners.md
│   ├── triage/
│   ├── deobf/
│   ├── vm/
│   └── symexec/
└── reports/
    ├── iocs/
    ├── recovered_secrets/
    └── repro_steps/
```

- Primary Probe
  - * -> [Condition: New sample arrives] -> Action: hash it, duplicate the original into `input/original/`, make all edits against copies only, and record architecture, format, endianness, linker/packer hints, and import style.
  - * -> [Condition: Binary type unknown] -> Action: run `file`, `readelf -h`, `objdump -f`, `rabin2 -I`, `checksec`, `lief` or `pefile` to fingerprint x86/x64/ARM/MIPS/RISC-V, PIE/NX/RELRO, stripped state, and static-vs-dynamic linkage.
  - * -> [Condition: Malware sample] -> Action: restore an isolated VM snapshot, disable shared folders, use host-only or no network, record snapshot IDs (`clean`, `tools`, `pre-run`, `post-unpack`), and never execute the original on the host.
  - * -> [Condition: Ghidra import] -> Action: create a non-shared project in `/re/<target>/ghidra/project`, enable Function ID, demangler, reference analyzers, and external entry recovery on pass 1; defer aggressive stack/constant propagation when obfuscation is suspected.
  - * -> [Condition: IDA/Binja environment] -> Action: bind both to the case venv at `/re/<target>/venv`, keep reusable helpers in `/re/common/`, and mirror script names across `ida/scripts` and `binja/scripts` for parity.
  - * -> [Condition: x64dbg/GDB setup] -> Action: install x64dbg plugins into its `plugins` directory, and load pwndbg/GEF plus `rr`, `strace`, `ltrace`, and `ret-sync` in Linux VMs for synchronized debugger/disassembler stepping.
  - * -> [Condition: Fast triage needed] -> Action: run FLOSS for stack/decoded strings, capa for capability clustering, and a quick entropy scan before opening a full disassembler.
- Dead End Pivots
  - * -> [Condition: `strings` yields nothing] -> Action: compute per-section entropy and look for high-entropy islands, tiny import tables, or RWX sections indicating packing or runtime decryption.
  - * -> [Condition: Headers look malformed] -> Action: compare parser output across `lief`, `rabin2`, PE-bear/Detect It Easy, and raw hex to distinguish corruption from deliberate anti-tooling.
  - * -> [Condition: Architecture unclear] -> Action: inspect prologue idioms, syscall ABI, relocation style, and literal pools; infer compiler family from CRT thunks, switch tables, EH metadata, and TLS callbacks.
- Data Chaining
  - * -> [Condition: Triage identifies imported crypto, decompression, VM, or anti-debug APIs] -> Action: turn those findings into first-pass breakpoint sets, rename seeds, and decompiler bookmarks.
  - * -> [Condition: FLOSS/capa expose config or behavior] -> Action: pivot those artifacts into YARA-like anchors, string decryptor hunts, and targeted emulation.
  - * -> [Condition: Entropy marks suspect regions] -> Action: feed those offsets into unpacking, memory-write tracing, or custom loader reconstruction.

Simple one-liners:
- `file sample && rabin2 -I sample && checksec --file=sample`
- `python3 -m pip install flare-floss flare-capa`
- `floss sample && capa -r /opt/capa-rules sample`

