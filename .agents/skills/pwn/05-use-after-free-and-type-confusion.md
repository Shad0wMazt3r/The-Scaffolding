## Use-After-Free & Type Confusion

- Primary Probe:
  - * -> [Condition: Freed object remains reachable or casted inconsistently] -> Action: build an object-lifetime map, then force allocator reuse with same-size or adjacent-size objects until the stale reference points at attacker-controlled data.
- Dead End Pivots:
  - * -> [Condition: Reuse is unstable] -> Action: spray same-size objects, pad the heap, and control free order to improve alias probability.
  - * -> [Condition: Virtual dispatch is not obvious] -> Action: walk manual vtables, callback tables, ops structs, or function-pointer arrays in Ghidra instead of waiting for decompiler type recovery.
  - * -> [Condition: Confusion is cross-language or JIT-adjacent] -> Action: model producer/consumer ownership separately and look for stale inline caches, tagged-union mistakes, or deserializer class mismatches.
- Data Chaining:
  - * -> [Condition: UAF gives attacker-controlled object substitution] -> Action: replace the freed object with a fake instance whose first fields satisfy program invariants while late fields redirect code flow through callbacks or vtables.
  - * -> [Condition: Only read-after-free exists] -> Action: leak heap/libc pointers from stale metadata, then revisit the same bug as a safe-linking bypass or allocator-poisoning setup.
  - * -> [Condition: Type confusion yields OOB length] -> Action: reinterpret it as arbitrary read/write and feed that primitive into a standard ret2libc, FSOP, or hook overwrite path.
- Mitigation branches:
  - * -> [Condition: CFI-like checks or vptr validation exist] -> Action: target legitimate-but-dangerous method tables, partial overwrites, or data-only corruption that changes a later indirect target.
  - * -> [Condition: Remote service restarts between requests] -> Action: keep the entire lifetime bug within one connection unless the service persists shared state.

