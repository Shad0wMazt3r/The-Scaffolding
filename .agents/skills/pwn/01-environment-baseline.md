# Pwn/Binary Exploitation - TTPs

**Environment baseline**

- Use a fixed workspace so artifacts stay separated by analysis phase and by exploit maturity:
`/pwn/<target>/{bin,libc,ld,src,ghidra,gdb,core,crashes,corpus,asan,ropchains,shellcode,exploits,evidence,notes,docker,remote}`.
- Install a minimum toolset of Ghidra on a supported 64-bit Windows/Linux/macOS host, GDB, one GDB plugin, pwntools in a Python virtualenv, binutils, patchelf, qemu-user/qemu-system, AFL++ with QEMU mode, and Docker for target replication; Ghidra supports 64-bit Windows, Linux, and macOS, pwntools is a Python exploit-development framework, and AFL++ QEMU mode is built with `./build_qemu_support.sh`. [arxiv](https://arxiv.org/pdf/1707.03341.pdf)
- Pin the exploit runtime with a per-target virtualenv and libc bundle:
`python3 -m venv /pwn/<target>/.venv && source /pwn/<target>/.venv/bin/activate && pip install --upgrade pwntools`
`cp ./target ./libc.so.6 ./ld-linux*.so* /pwn/<target>/bin/`
- Standardize GDB around one plugin per session to avoid command collisions. A practical `.gdbinit` core is:
```gdb
set disassembly-flavor intel
set pagination off
set confirm off
set print pretty on
set follow-fork-mode child
set detach-on-fork off
handle SIGALRM nostop noprint pass
handle SIGPIPE nostop noprint pass
# choose one:
# source ~/pwndbg/gdbinit.py
# source ~/gef.py
# source ~/peda/peda.py
```
- Use pwntools features deliberately: `context` sets architecture/runtime knobs, `cyclic()` generates de Bruijn crash patterns, and `process` / `remote` share a similar tube API for local-vs-remote exploit parity. [docs.pwntools](https://docs.pwntools.com/en/stable/util/cyclic.html)
- Fingerprint mitigations before spending time on primitives because `checksec` reports RELRO, stack canary, NX, PIE, and related hardening status, where RELRO protects GOT/PLT writes, canaries detect stack corruption, NX blocks execution from stack/heap, and PIE enables randomized base loading. [linuxcommandlibrary](https://linuxcommandlibrary.com/man/checksec)
- Load symbols and detached debug info explicitly. `symbol-file` replaces the main symbol table, while `add-symbol-file <file> <textaddr> [-s section addr ...]` adds symbols for dynamically loaded images without discarding existing symbols. [sourceware](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Files.html)
- Use `pwndbg rop --grep 'pop rdi' -- --nojop` during constrained gadget hunts because pwndbg exposes a ROPgadget-backed `rop` command with grep and symbol options; for heap work, prefer pwndbg heap views and switch heuristic resolution only when glibc debug symbols are absent. [linkinghub.elsevier](https://linkinghub.elsevier.com/retrieve/pii/S0010465518302042)
- Replicate the target in Docker with the exact loader/libc pair and an explicit entrypoint, then mount `/pwn/<target>` read-write so crash artifacts, cores, and exploit traces persist outside the container.

**High-value one-liners**

- Mitigation triage: `checksec --file=./target && file ./target && readelf -Wl ./target`
- Offset recovery: `python3 -c 'from pwn import *; print(cyclic(1024).decode())'`
- Crash lookup: `python3 -c 'from pwn import *; print(cyclic_find(0x6161616c))'`
- GOT/PLT scan: `readelf -Wr ./target | egrep 'puts|printf|free|exit'`
- Libc hints: `readelf -Ws ./libc.so.6 | egrep '__libc_start_main|system|puts|__free_hook|__malloc_hook'`
- Gadget filter: `ropper -f ./target --search "pop rdi; ret"`
- QEMU-user fast path for foreign arch: `qemu-aarch64 -L ./rootfs ./target`
- Local loader pinning: `./ld-linux-x86-64.so.2 --library-path . ./target`

