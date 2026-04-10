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

