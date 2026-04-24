# Reverse Engineering - TTPs

## Initial Triage

**Static Analysis Platform:** Ghidra (default) - supports disassembly, decompilation, graphing, scripting, many processor families. FLOSS: `pip install flare-floss`. capa: `pip install flare-capa`. Binary Ninja Python API for interactive/headless use. x64dbg plugins: drop `.dp32`/`.dp64` in `plugins/` directory.

```text
/re/<target>/
├── evidence/{hashes,notes,screenshots,pcaps,timeline}
├── input/{original,renamed,samples}
├── ghidra/{project,exports,scripts,types}
├── ida/{databases,scripts,lumina_off}
├── binja/{bndb,scripts,types}
├── dynamic/{traces,dumps,frida,drio,gdb,x64dbg}
├── unpacked/{stage0,stage1,stage2,oep}
├── firmware/{binwalk,squashfs,qemu,nvram}
├── vm/{bytecode,opcode_maps,traces,lifts}
├── scripts/{one_liners.md,triage,deobf,vm,symexec}
└── reports/
```

**Triage Approach:**
1. File type & architecture: `file`, `readelf -Wh`, `objdump -x`
2. Strings & imports: `strings`, `readelf -Wd`, nm
3. Mitigations: `checksec`
4. Load into Ghidra/IDA/Binja; fingerprint packer/obfuscation
5. Decide: static-only, dynamic-only, or hybrid

**Key Ghidra Setup:**
- Create project in `ghidra/project/`
- Auto-analyze default settings first
- Export: `XREFs`, `functions`, `memory`, `bytes` to `ghidra/exports/`
- Use `FlatProgramAPI` for scripting in `ghidra/scripts/`

***
