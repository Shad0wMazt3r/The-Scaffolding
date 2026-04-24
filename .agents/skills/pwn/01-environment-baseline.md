# Pwn/Binary Exploitation - TTPs

**Workspace:** `/pwn/<target>/{bin,libc,ld,src,ghidra,gdb,core,crashes,corpus,asan,ropchains,shellcode,exploits,evidence,notes,docker,remote}`

**Toolset:** Ghidra (64-bit), GDB, pwntools (virtualenv), binutils, patchelf, qemu-user/qemu-system, AFL++ QEMU mode, Docker

**Runtime Setup:**
```bash
python3 -m venv /pwn/<target>/.venv && source /pwn/<target>/.venv/bin/activate
pip install --upgrade pwntools
cp ./target ./libc.so.6 ./ld-linux*.so* /pwn/<target>/bin/
```

**.gdbinit Core:**
```gdb
set disassembly-flavor intel
set pagination off
set confirm off
set print pretty on
set follow-fork-mode child
set detach-on-fork off
handle SIGALRM nostop noprint pass
handle SIGPIPE nostop noprint pass
# Choose one: pwndbg / gef / peda
```

**pwntools Key Features:**
- `context` - architecture/runtime knobs
- `cyclic()` - de Bruijn crash patterns
- `process`/`remote` - tube API for local/remote parity

**Before exploiting:** Run `checksec` to profile RELRO, canary, NX, PIE, FORTIFY, CFI status.

**Symbol Loading:**
- `symbol-file <file>` - replace main symbol table
- `add-symbol-file <file> <addr> [-s section addr ...]` - add symbols for dynamic images

**High-Value One-Liners:**
```bash
checksec --file=./target && file ./target && readelf -Wl ./target
python3 -c 'from pwn import *; print(cyclic(1024).decode())'
python3 -c 'from pwn import *; print(cyclic_find(0x6161616c))'
readelf -Wr ./target | egrep 'puts|printf|free|exit'
ropper -f ./target --search "pop rdi; ret"
qemu-aarch64 -L ./rootfs ./target
./ld-linux-x86-64.so.2 --library-path . ./target
```

**Docker for Replication:** Mount `/pwn/<target>` read-write so crash artifacts and cores persist outside container.

***
