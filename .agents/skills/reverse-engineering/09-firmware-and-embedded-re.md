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

