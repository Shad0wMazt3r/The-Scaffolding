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

## Static Disassembly & Decompilation

Ghidra is suitable as the cross-platform baseline because it supports scripting and automated modes in addition to interactive disassembly/decompilation, while Binary Ninja is strongest when you want API-driven MLIL/HLIL transformations and headless automation. [mintlify](https://www.mintlify.com/Vector35/binaryninja-api/api/python/overview)

- Primary Probe
  - * -> [Condition: Normal native binary] -> Action: perform a first-pass Ghidra/IDA/Binja auto-analysis, then manually validate entry, imports, TLS callbacks, exception handlers, constructor arrays, and dispatch-heavy basic blocks before trusting recovered functions.
  - * -> [Condition: Stripped ELF/PE/Mach-O] -> Action: recover boundaries from prologues/epilogues, switch tables, call targets, unwind metadata, and relocation consumers; then classify calling conventions from register preservation and argument setup.
  - * -> [Condition: Compiler artifact recovery] -> Action: fingerprint MSVC vs GCC/Clang vs Rust/Go using CRT start stubs, panic/logging patterns, SEH metadata, RTTI, vtable shapes, stack canaries, and allocator behavior.
  - * -> [Condition: Obfuscated control flow] -> Action: switch from decompiler-first to CFG-first analysis, annotate dominators/post-dominators, collapse trampoline nodes, and separate real dispatch from junk edges.
- Dead End Pivots
  - * -> [Condition: Decompiler output is nonsensical] -> Action: rebuild stack variables manually, force function signatures, define structs/unions, and re-run limited analysis on a narrowed address set.
  - * -> [Condition: Function recovery misses large regions] -> Action: sweep for code references in data sections, indirect call targets, jump tables, vtables, and manually carved executable pages.
  - * -> [Condition: Cross-references are sparse] -> Action: search for immediate constants, error strings, S-boxes, syscall numbers, and format strings to back into logic clusters.
- Data Chaining
  - * -> [Condition: You identify compare chains, memcmp wrappers, or validator loops] -> Action: map those addresses into debugger breakpoints and symbolic targets.
  - * -> [Condition: You identify a custom dispatcher] -> Action: tag the state variable, handler table, and bytecode fetch/decode logic, then move directly into VM trace collection.
  - * -> [Condition: You identify decryption routines] -> Action: collect keys, seeds, and buffer lifetimes for runtime dumping or reimplementation.

Simple one-liners:
- `objdump -dM intel sample | less`
- `ghidraRun /re/<target>/ghidra/project`
- `python3 -c "import r2pipe; r=r2pipe.open('sample'); r.cmd('aaa'); print(r.cmd('afl'))"`

Script Definition Block — CFG repair helper
- Input Data: function start candidates, basic block edges, indirect branch sites, disassembler export.
- Core Processing Logic:
  - Build a provisional CFG from known edges.
  - Score blocks by inbound legitimacy, fall-through plausibility, and constant-state transitions.
  - Collapse trampoline/junk nodes and re-emit a simplified graph.
  - Export recovered switch tables and likely handler starts.
- Dependencies: NetworkX, r2pipe or Ghidra headless export, optional Capstone.
- Expected Output Format: JSON with `functions`, `blocks`, `edges`, `suspect_junk`, `indirect_targets`.

## Anti-Analysis Bypass

- Primary Probe
  - * -> [Condition: Target exits immediately under debugger] -> Action: inspect `IsDebuggerPresent`, `CheckRemoteDebuggerPresent`, `NtQueryInformationProcess`, `ptrace`, `/proc/self/status`, `rdtsc`, `QueryPerformanceCounter`, `cpuid`, SIDT/SGDT, MAC/vendor checks, and sleep-skipping logic.
  - * -> [Condition: Native Linux] -> Action: patch or hook `ptrace`, `seccomp`, `prctl`, and timing functions; use `LD_PRELOAD` or `rr` if the program tolerates it.
  - * -> [Condition: Native Windows] -> Action: use x64dbg/WinDbg with API breakpoints, hardware breakpoints for anti-int3 logic, and patch return values at the call boundary instead of NOP-spraying whole routines.
  - * -> [Condition: Junk code / opaque predicates] -> Action: identify invariants, constant branches, and dead-store storms; simplify at IR or microcode level instead of byte-patching blindly.
- Dead End Pivots
  - * -> [Condition: Software breakpoints are detected] -> Action: switch to hardware breakpoints on execute/read/write or guard-page traps.
  - * -> [Condition: Anti-VM blocks execution] -> Action: patch vendor string and device checks, or move to bare-metal/less-fingerprinted nested VM with minimal guest additions.
  - * -> [Condition: Timing checks remain unstable] -> Action: hook the timer source, normalize deltas, or record once and replay via debugger scripts.
- Data Chaining
  - * -> [Condition: Anti-debug API list is recovered statically] -> Action: pre-place hooks and return-value overrides before the protected region runs.
  - * -> [Condition: Opaque predicate simplification succeeds] -> Action: re-run decompilation and treat newly reachable blocks as fresh triage targets.
  - * -> [Condition: Environment gates are bypassed] -> Action: advance immediately to unpacking or secret-comparison tracing before secondary checks trigger.

Simple one-liners:
- `strace -f -s 256 -o dynamic/traces/strace.txt ./sample`
- `ltrace -f -s 256 -o dynamic/traces/ltrace.txt ./sample`
- `gdb -q ./sample -ex 'catch syscall ptrace' -ex run`

Script Definition Block — anti-analysis normalizer
- Input Data: API/symbol hit list, timing call sites, debugger-detection branches, environment strings.
- Core Processing Logic:
  - Map anti-analysis primitives to hook points.
  - Generate a patch/hook plan with minimal semantic disturbance.
  - Prioritize boundary interception over deep inline patching.
  - Emit per-platform debugger commands and Frida hook templates.
- Dependencies: Capstone, Keystone, Frida templates, PE/ELF symbol parser.
- Expected Output Format: YAML with `site`, `method`, `override`, `risk`, `rollback`.

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

## Dynamic Analysis & Tracing

- Primary Probe
  - * -> [Condition: Syscall-visible behavior matters] -> Action: start with `strace`/`ltrace`/Procmon-class telemetry before intrusive debugging; learn files, sockets, crypto material locations, and comparison sinks first.
  - * -> [Condition: User-space logic is rich but anti-debug is moderate] -> Action: instrument with Frida or DynamoRIO to hook comparison functions, allocators, crypto APIs, and string decoders at runtime.
  - * -> [Condition: Secret validation suspected] -> Action: set breakpoints on `strcmp`, `memcmp`, `strncmp`, custom compare loops, or branch instructions fed by those results; inspect operands before flags are consumed.
  - * -> [Condition: Multi-process or injected child] -> Action: follow forks/spawns, log inherited handles, and trace the first branch into unpacked child code.
- Dead End Pivots
  - * -> [Condition: API hooks miss inline routines] -> Action: instrument basic-block execution and memory accesses instead of library boundaries.
  - * -> [Condition: Debugger kills process] -> Action: switch to DBI or emulation-first tracing where fewer debugger artifacts exist.
  - * -> [Condition: Trace volume is unmanageable] -> Action: gate logging to suspect regions, comparison sinks, key schedules, and recently written executable pages.
- Data Chaining
  - * -> [Condition: Runtime buffer with plaintext/flag candidate appears] -> Action: capture producer PC, last-writer chain, and call stack; move backward into decryption or parser routines.
  - * -> [Condition: Branch outcome depends on transformed user input] -> Action: export the transform pipeline into the symbolic or algorithm-reimplementation section.
  - * -> [Condition: Dynamic trace resolves indirect calls] -> Action: import those targets back into IDA/Ghidra/Binja to repair CFG and rename handlers.

Simple one-liners:
- `frida-trace -f ./sample -i memcmp -i strcmp -i strncmp`
- `rr record ./sample`
- `perf record -e intel_pt//u -- ./sample`

Script Definition Block — compare-sink interceptor
- Input Data: addresses of compare calls or custom compare loops, register snapshots, relevant memory windows.
- Core Processing Logic:
  - Hook every compare sink and record both operands before evaluation.
  - Correlate operands with call stack and prior decode routines.
  - Cluster recurring transformed-input patterns.
  - Emit candidate “expected” values and the routines that produced them.
- Dependencies: Frida or DynamoRIO, symbol resolver, Capstone.
- Expected Output Format: CSV/JSON rows with `ts`, `pc`, `lhs`, `rhs`, `stack`, `producer_chain`.

## Custom Virtual Machine Reversing

- Primary Probe
  - * -> [Condition: Dispatcher loop suspected] -> Action: locate the bytecode fetch, opcode decode, handler jump table, VM context struct, virtual PC, and operand stack/register file.
  - * -> [Condition: Static handler grouping works] -> Action: cluster handlers by state-variable deltas, stack effects, and memory footprint; derive tentative opcode classes such as load/store, arithmetic, branch, crypto, compare.
  - * -> [Condition: Runtime is reachable] -> Action: instrument one VM-step at a time, logging `vpc`, opcode byte(s), decoded operands, virtual registers, and branch outcomes.
- Dead End Pivots
  - * -> [Condition: Handlers are flattened or merged] -> Action: trace indirect branch targets under DBI and split handler identities by pre/post-state signatures rather than function boundaries.
  - * -> [Condition: Bytecode encrypted in memory] -> Action: break on last writer of the bytecode buffer or dump immediately after decryption before execution starts.
  - * -> [Condition: VM context layout unclear] -> Action: use taint from bytecode fetch and handler side effects to infer field roles, then rename by mutation pattern.
- Data Chaining
  - * -> [Condition: Opcode map stabilizes] -> Action: write an interpreter spec, replay traces offline, and validate semantics against captured state transitions.
  - * -> [Condition: Branch/compare opcodes are understood] -> Action: lift bytecode to SSA or an IR, then run symbolic execution on the VM program rather than on native dispatcher noise.
  - * -> [Condition: Virtualized checker found] -> Action: reconstruct the exact input transformation path and extract the constant/secret path predicate.

Simple one-liners:
- `python3 -c "import r2pipe; r=r2pipe.open('sample'); r.cmd('aaa'); print(r.cmd('/cj dispatch'))"`
- `objdump -d sample | grep -E 'jmp\\*|call\\*'`

Script Definition Block — VM ISA reconstructor
- Input Data: native trace of dispatcher iterations, memory dumps of bytecode, candidate VM-context offsets.
- Core Processing Logic:
  - Segment traces into individual VM steps.
  - Infer operand widths and addressing modes from bytecode consumption and state deltas.
  - Assign provisional mnemonic classes from side effects.
  - Validate by replaying traces in an offline emulator and diffing state after each step.
- Dependencies: DBI trace source, Capstone, Python data model, optional Z3 for validation.
- Expected Output Format: `opcode_map.yaml`, `context_layout.json`, `trace_replay_report.md`.

## Symbolic & Concolic Execution

- Primary Probe
  - * -> [Condition: Validation path is narrow and input-bound] -> Action: isolate the checker function, stub non-essential environment calls, symbolize only the true input bytes, and target success blocks directly.
  - * -> [Condition: Heavy unpacking or self-modifying front-end exists] -> Action: concretely execute to the post-unpack/post-decrypt checkpoint, then hand execution to angr or Triton from the simplified state.
  - * -> [Condition: Data-dependency clarity is low] -> Action: apply taint first to find which bytes truly influence rejection branches before full constraint solving.
- Dead End Pivots
  - * -> [Condition: Path explosion] -> Action: slice to the validator, merge equivalent states, concretize irrelevant bytes, and replace known library calls with summaries.
  - * -> [Condition: Indirect memory or VM noise breaks the model] -> Action: lift only the reduced checker or the recovered VM bytecode, not the full native wrapper.
  - * -> [Condition: Solver returns unstable models] -> Action: add domain constraints from observed runtime values, character classes, checksums, or length invariants.
- Data Chaining
  - * -> [Condition: Dynamic tracing identifies compare sinks] -> Action: use those PCs as find/avoid targets in the symbolic harness.
  - * -> [Condition: Deobfuscation recovers transform routines] -> Action: reimplement them faithfully and replace opaque native blocks with clean symbolic summaries.
  - * -> [Condition: Model produces candidate flag/key] -> Action: validate against a traced concrete run and preserve the accepted path constraints as proof.

angr’s published examples call out Unicorn-backed concrete execution as essential for some self-modifying challenges because symbolically simulating unpacking is too slow. [docs.angr](https://docs.angr.io/en/latest/examples.html)

Script Definition Block — symbolic harness planner
- Input Data: validator entry PC, success/fail PCs, initial memory/register snapshot, imported-function stubs, input buffer location.
- Core Processing Logic:
  - Build a minimal state from a post-unpack checkpoint.
  - Symbolize only user-controlled bytes that taint decision points.
  - Add library summaries and environment models.
  - Run directed exploration to success while recording blocking predicates.
- Dependencies: angr, Triton or PyVEX, Unicorn checkpoint, Z3.
- Expected Output Format: `solution.bin`, `constraints.smt2`, `path_report.json`.

## Algorithm Identification & Reimplementation

- Primary Probe
  - * -> [Condition: Unknown transform or keygen present] -> Action: classify by constants, rotation counts, block size, table layout, and state-machine shape; compare against AES/RC4/ChaCha/SHA/MD5/CRC/LFSR archetypes.
  - * -> [Condition: Hash/crypto suspected] -> Action: map round constants, endian behavior, message schedule style, and permutation structure before naming the primitive.
  - * -> [Condition: Home-grown checker] -> Action: lift the logic into clean pseudocode, replace machine-width artifacts with explicit typed operations, and derive algebraic constraints.
- Dead End Pivots
  - * -> [Condition: Constants are hidden] -> Action: break on table initialization and dump post-init memory, or derive constants from loop recurrence and rotation structure.
  - * -> [Condition: Algorithm is interleaved with junk] -> Action: slice by taint from final compare or output buffer to remove unrelated arithmetic.
  - * -> [Condition: Multiple candidate algorithms fit] -> Action: feed known test vectors or trace snapshots through each candidate model and eliminate mismatches.
- Data Chaining
  - * -> [Condition: Primitive identified] -> Action: reimplement it in a reference script and compare outputs against runtime snapshots byte-for-byte.
  - * -> [Condition: Key schedule recovered] -> Action: derive the exact secret-generation or verification pipeline and move to solver/replay.
  - * -> [Condition: Reimplementation matches] -> Action: use it to generate valid inputs, decrypt blobs, or reconstruct flags at scale.

Simple one-liners:
- `python3 -c "import zlib,sys; print(hex(zlib.crc32(open('blob','rb').read()) & 0xffffffff))"`
- `python3 -c "from pwn import *; print(hexdump(open('blob','rb').read()[:256]))"`

Script Definition Block — constant-signature matcher
- Input Data: immediates, tables, rotate counts, loop bounds, candidate round functions.
- Core Processing Logic:
  - Normalize constants by width and endianness.
  - Match against a signature bank of common crypto/hash/checksum primitives.
  - Score partial matches and annotate missing pieces.
  - Emit a hypothesis list with validation probes.
- Dependencies: Capstone or disassembler export, signature database, optional NumPy for table comparison.
- Expected Output Format: ranked JSON list with `algorithm`, `score`, `evidence`, `next_probe`.

## Firmware & Embedded RE

- Primary Probe
  - * -> [Condition: Firmware blob received] -> Action: identify container format, endian, CPU family, filesystem type, compression, and bootloader markers; separate whole-image analysis from extracted component analysis.
  - * -> [Condition: Filesystem embedded] -> Action: extract with binwalk first, then inspect init scripts, web roots, update agents, credentials, certificates, and hard-coded NVRAM keys.
  - * -> [Condition: Executable component found] -> Action: cross-analyze with the correct ISA and ABI, paying close attention to ARM Thumb, MIPS delay slots, RISC-V calling patterns, and position-dependent code.
  - * -> [Condition: Runtime emulation needed] -> Action: boot the minimal service set in QEMU/chroot, stub missing peripherals/NVRAM, and instrument syscalls plus config-file reads.
- Dead End Pivots
  - * -> [Condition: Extraction fails] -> Action: carve manually by magic bytes, LZMA/U-Boot headers, SquashFS/JFFS2 patterns, and entropy boundaries.
  - * -> [Condition: Service crashes in emulation] -> Action: patch peripheral checks, preload expected `/proc` or `/dev` artifacts, and fake NVRAM responses.
  - * -> [Condition: Secret is generated from hardware state] -> Action: hook the syscall or ioctl boundary and capture the derived material rather than reproducing the full board environment.
- Data Chaining
  - * -> [Condition: Web/API creds or update keys are found statically] -> Action: map them to runtime consumers and trace validation flows.
  - * -> [Condition: Init script reveals service order] -> Action: emulate only the necessary dependency chain to reach the checker/decryptor.
  - * -> [Condition: Filesystem plus emulation yields decrypted config] -> Action: feed recovered constants/keys back into native algorithm reimplementation.

Simple one-liners:
- `binwalk -Me firmware.bin -C firmware/binwalk/`
- `grep -RInaE 'password|secret|token|key|flag' firmware/binwalk/`
- `find firmware/binwalk/ -type f -exec file {} + | grep -E 'ELF|script|archive'`

Script Definition Block — firmware secret extractor
- Input Data: extracted filesystem tree, emulated rootfs, syscall/ioctl trace, NVRAM key/value accesses.
- Core Processing Logic:
  - Instrument reads of config, NVRAM, and secure-storage abstractions.
  - Correlate them with service startup and decrypt/validate routines.
  - Capture derived secrets at API boundaries and on successful comparisons.
  - Reconcile secrets with static constants to locate the root derivation path.
- Dependencies: QEMU user/system mode, `strace`, optional custom syscall hook, disassembler export.
- Expected Output Format: `secrets.json`, `callsites.csv`, `derivation_graph.dot`.

## .NET / JVM / Scripting Language RE

- Primary Probe
  - * -> [Condition: Managed sample detected] -> Action: choose dnSpy/ILSpy for .NET, jadx for JVM/Android, and source-first reconstruction for PyInstaller, zipapp, or Electron/ASAR packages.
  - * -> [Condition: .NET] -> Action: inspect resources, embedded assemblies, Confuser-style control-flow transforms, string decryptors, delegate trampolines, and reflection-heavy loaders.
  - * -> [Condition: JVM/Android] -> Action: decompile APK/JAR, inspect manifest/entry components, native JNI bridges, reflection, dynamic class loading, and asset/resource blobs.
  - * -> [Condition: PyInstaller/Electron/Node] -> Action: extract the archive, locate entry scripts, inspect bytecode bundles or ASAR contents, then treat native addons as separate RE targets.
- Dead End Pivots
  - * -> [Condition: Reflection hides real control flow] -> Action: log resolved method names and types at runtime, then map them back to decompiled stubs.
  - * -> [Condition: Obfuscator destroys names/strings] -> Action: hook string decryptors and resource loaders, dump plaintext results, and repopulate the decompiler database.
  - * -> [Condition: Managed wrapper delegates to native validator] -> Action: pivot to the native DLL/SO and continue with the static/dynamic sections above.
- Data Chaining
  - * -> [Condition: Decompiler reveals resource-embedded payload] -> Action: extract and re-triage it as a fresh sample.
  - * -> [Condition: Managed validation logic is readable] -> Action: reimplement directly and solve constraints at source/IL level before touching native instrumentation.
  - * -> [Condition: JNI/PInvoke boundary found] -> Action: set argument/return capture hooks there; that is often the narrowest point for flag or secret extraction.

Simple one-liners:
- `jadx -d out_apk app.apk`
- `python3 -m pyinstxtractor.py sample.exe`
- `npx asar extract app.asar extracted_app/`