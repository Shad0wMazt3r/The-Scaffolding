## Shellcoding & Restricted Environment Bypass

- Primary Probe:
  - * -> [Condition: You control RIP but environment is constrained] -> Action: fingerprint NX, PIE, seccomp, and available syscalls first, then choose native shellcode, staged shellcode, ROP-only syscalls, or SROP.
- Dead End Pivots:
  - * -> [Condition: NX enabled] -> Action: pivot to ret2libc, mprotect/mmap ROP, or `read`-to-RWX staging if an executable mapping can be created.
  - * -> [Condition: seccomp blocks `execve`] -> Action: switch goal to open/read/write exfiltration, ORW ROP, `dup2` + allowed helper abuse, or SROP to reach an allowed syscall shape.
  - * -> [Condition: PIE + badchars limit gadgets] -> Action: use partial overwrites, ret2csu, sigreturn frames, or short decoder stubs in already-executable memory.
- Data Chaining:
  - * -> [Condition: Leak + write primitive exist] -> Action: call `mprotect`/`mmap` via ROP, copy shellcode, then jump; if that is blocked, keep the entire payload in code-reuse form.
  - * -> [Condition: No libc base yet] -> Action: use PLT/GOT leaks or stack disclosures first, then commit to either ret2libc or syscall-oriented chains.
  - * -> [Condition: Remote libc uncertain] -> Action: prefer raw syscalls or SROP over version-sensitive libc gadgets when feasible.
- Simple automation:
  - `python3 -c 'from pwn import *; context.clear(arch="amd64"); print(asm(shellcraft.sh()).hex())'`
  - `python3 -c 'from pwn import *; context.clear(arch="amd64"); print(ROP(ELF("./target")).find_gadget(["pop rdi","ret"]))'`

