## Stack-Based Overflows

- Primary Probe:
  - * -> [Condition: Input reaches a stack buffer] -> Action: run `checksec`, then feed a pwntools cyclic pattern, crash under GDB, recover RIP/EIP with `cyclic_find`, and confirm saved return-address control before planning ret2win, ret2libc, ROP, or SROP. [docs.pwntools](https://docs.pwntools.com/en/stable/tubes/processes.html)
- Dead End Pivots:
  - * -> [Condition: No direct RIP control] -> Action: inspect Ghidra decompilation for adjacent scalar corruption, saved frame-pointer corruption, or exception-structure corruption, then pivot to off-by-one, stack canary leak, or longjmp/setjmp abuse.
  - * -> [Condition: Canary blocks contiguous overwrite] -> Action: hunt an information leak first through format strings, unterminated prints, stack dumps, or uninitialized stack reads, then replay the exact frame with a preserved canary.
  - * -> [Condition: Gadget density is poor] -> Action: switch to SROP, ret2csu, or stack pivoting into a writable segment followed by a short second-stage ROP chain.
- Data Chaining:
  - * -> [Condition: Offset confirmed and one code/libc leak obtained] -> Action: compute PIE/libc base, resolve `system` or syscall gadgets, then choose `ret2libc` for normal gadget availability, full ROP for complex register setup, or SROP when gadgets are severely constrained.
  - * -> [Condition: NX disabled] -> Action: prefer direct shellcode on stack/heap only after proving the region is executable; otherwise keep code-reuse as the default because NX is commonly enabled.
  - * -> [Condition: Remote differs from local] -> Action: branch exploit transport through pwntools tubes so the same logic runs against `process()` locally and `remote()` remotely, but keep loader/libc addresses separate per environment. [docs.pwntools](https://docs.pwntools.com/en/stable/tubes.html)
- Mitigation branches:
  - * -> [Condition: PIE off, NX on] -> Action: favor fixed-binary ROP or ret2plt for leaks, then ret2libc.
  - * -> [Condition: PIE on, ASLR on] -> Action: first leak a code pointer or GOT/libc pointer; do not brute-force unless restart cost is trivial.
  - * -> [Condition: Full RELRO] -> Action: do not plan GOT overwrite; redirect to saved return pointers, vtables, hooks, FILE structures, or ROP-only execution.
- Simple automation:
  - `python3 -c 'from pwn import *; elf=ELF("./target"); print(hex(next(elf.search(asm("syscall; ret")))))'`
- Script Definition Block:
  - **Input Data:** core file, crash register state, target ELF, optional remote leak transcript.
  - **Core Processing Logic:** parse core for faulting PC/SP; compute cyclic offset; test candidate pivots (`ret`, `leave; ret`, `xchg rsp,*`); rank gadget chains by register coverage; emit local and remote payload templates.
  - **Dependencies:** pwntools, pyelftools, ROPgadget or ropper.
  - **Expected Output Format:** JSON with `offset`, `stack_pivot`, `leaks_needed`, `candidate_chains`, `local_payload_layout`, `remote_payload_layout`.

