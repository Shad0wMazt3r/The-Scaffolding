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

