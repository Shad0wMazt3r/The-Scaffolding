## Custom Virtual Machine Reversing

- Primary Probe
  - * -> [Condition: Dispatcher loop suspected] -> Action: locate the bytecode fetch, opcode decode, handler jump table, VM context struct, virtual PC, and operand stack/register file.
  - * -> [Condition: Static handler grouping works] -> Action: cluster handlers by state-variable deltas, stack effects, and memory footprint; derive tentative opcode classes such as load/store, arithmetic, branch, crypto, compare.
  - * -> [Condition: Runtime is reachable] -> Action: instrument one VM-step at a time, logging `vpc`, opcode byte(s), decoded operands, virtual registers, and branch outcomes.
- Dead End Pivots
  - * -> [Condition: Handlers are flattened or merged] -> Action: trace indirect branch targets under DBI and split handler identities by pre/post-state signatures rather than function boundaries.
  - * -> [Condition: Bytecode encrypted in memory] -> Action: break on last writer of the bytecode buffer or dump immediately after decryption before execution starts.
  - * -> [Condition: VM context layout unclear] -> Action: use taint from bytecode fetch and handler side effects to infer field roles, then rename by mutation pattern.
- Data Chaining
  - * -> [Condition: Opcode map stabilizes] -> Action: write an interpreter spec, replay traces offline, and validate semantics against captured state transitions.
  - * -> [Condition: Branch/compare opcodes are understood] -> Action: lift bytecode to SSA or an IR, then run symbolic execution on the VM program rather than on native dispatcher noise.
  - * -> [Condition: Virtualized checker found] -> Action: reconstruct the exact input transformation path and extract the constant/secret path predicate.

Simple one-liners:
- `python3 -c "import r2pipe; r=r2pipe.open('sample'); r.cmd('aaa'); print(r.cmd('/cj dispatch'))"`
- `objdump -d sample | grep -E 'jmp\\*|call\\*'`

Script Definition Block — VM ISA reconstructor
- Input Data: native trace of dispatcher iterations, memory dumps of bytecode, candidate VM-context offsets.
- Core Processing Logic:
  - Segment traces into individual VM steps.
  - Infer operand widths and addressing modes from bytecode consumption and state deltas.
  - Assign provisional mnemonic classes from side effects.
  - Validate by replaying traces in an offline emulator and diffing state after each step.
- Dependencies: DBI trace source, Capstone, Python data model, optional Z3 for validation.
- Expected Output Format: `opcode_map.yaml`, `context_layout.json`, `trace_replay_report.md`.

