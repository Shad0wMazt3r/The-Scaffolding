## Stack-Based Overflows

### Primary Probe

- **[Input reaches stack buffer]** `checksec`, pwntools cyclic pattern, crash in GDB, `cyclic_find` on RIP/EIP, confirm saved return-address control before ret2win/ret2libc/ROP/SROP

### Dead End Pivots

- **[No direct RIP control]** Inspect Ghidra for adjacent scalar corruption, frame-pointer corruption, exception-structure → off-by-one, canary leak, longjmp/setjmp
- **[Canary blocks overwrite]** Hunt info leak first (format strings, unterminated prints, stack dumps) → replay with preserved canary
- **[Poor gadget density]** Switch to SROP, ret2csu, or stack pivot into writable segment + short second-stage ROP

### Data Chaining

- **[Offset + one code/libc leak]** Compute PIE/libc base → resolve `system`/syscall gadgets → ret2libc (normal gadgets), full ROP (complex regs), SROP (constrained)
- **[NX disabled]** Prefer shellcode on stack/heap only after proving executable; default to code-reuse (NX usually enabled)
- **[Remote differs from local]** Use pwntools tubes for same logic on `process()` and `remote()`, but separate loader/libc per environment

### Mitigation Branches

- **[PIE off, NX on]** Fixed-binary ROP/ret2plt for leaks → ret2libc
- **[PIE on, ASLR on]** Leak code/GOT/libc pointer first (don't brute-force unless restart is cheap)
- **[Full RELRO]** No GOT overwrite; redirect to saved return pointers/vtables/hooks/FILE/ROP-only

### Gadget One-Liner

```bash
python3 -c 'from pwn import *; elf=ELF("./target"); print(hex(next(elf.search(asm("syscall; ret")))))'
```

***
