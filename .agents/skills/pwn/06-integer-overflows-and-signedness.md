## Integer Overflows & Signedness Bugs

- Primary Probe:
  - * -> [Condition: Length, count, or index math exists] -> Action: audit every multiplication, addition, cast, and bounds check that crosses signed/unsigned or 32/64-bit boundaries, then test allocator and copy sizes around wrap points.
- Dead End Pivots:
  - * -> [Condition: Direct wrap is not reachable] -> Action: search for parser differentials where one layer validates signed values and another consumes them unsigned.
  - * -> [Condition: Crash disappears under sanitizer builds] -> Action: compare optimized and unoptimized binaries for compiler-inserted changes that hide or expose truncation.
  - * -> [Condition: No corruption yet] -> Action: chase the integer bug as a logic primitive first, such as negative index read, undersized allocation, or oversized loop bound.
- Data Chaining:
  - * -> [Condition: Integer overflow causes undersized heap allocation] -> Action: follow with controlled overwrite into adjacent chunk metadata, then convert into overlap or tcache poisoning.
  - * -> [Condition: Signedness allows negative indexing] -> Action: turn it into relative arbitrary read/write against stack, heap, or object arrays.
  - * -> [Condition: Counter wrap bypasses auth or refcount] -> Action: chain the logic bug into UAF, double free, or privilege boundary bypass rather than forcing code execution immediately.
- Mitigation branches:
  - * -> [Condition: Memory protections are strong] -> Action: integer bugs often win via structure mis-sizing and object adjacency, not direct shellcode or GOT attacks.
- Simple automation:
