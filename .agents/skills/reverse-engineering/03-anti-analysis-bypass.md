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

