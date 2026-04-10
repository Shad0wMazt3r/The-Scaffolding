## Format String Attacks

- Primary Probe:
  - * -> [Condition: User input reaches `printf`-family as format] -> Action: brute the stack index with controlled markers, confirm `%p/%s/%n` behavior, and determine whether you have read-only disclosure, constrained writes, or full arbitrary write.
- Dead End Pivots:
  - * -> [Condition: Direct `%n` is filtered] -> Action: use width/precision-controlled partial writes, positional specifiers, or UTF-8/locale edge cases to rebuild write capability.
  - * -> [Condition: Stack leak is noisy] -> Action: pivot to `%s` using known writable pointers or GOT entries to turn stack noise into deterministic memory reads.
  - * -> [Condition: Output truncates early] -> Action: reroute through repeated small writes or a staged leak-then-reconnect model rather than a single monolithic payload.
- Data Chaining:
  - * -> [Condition: One libc or PIE pointer leaks] -> Action: compute base, then use `%n` to rewrite a saved return address, function pointer, `.fini_array`, or weakly protected GOT entry depending on RELRO.
  - * -> [Condition: Only read primitive exists] -> Action: use it to disclose canary, PIE base, libc base, heap base, and stack addresses, then hand off to a stack or heap exploit that needed those values.
  - * -> [Condition: Remote libc differs] -> Action: leak at least two anchors, such as `puts` plus `__libc_start_main`-adjacent state, before fingerprinting offsets.
- Mitigation branches:
  - * -> [Condition: Full RELRO] -> Action: treat format string mainly as leak + stack-retarget primitive.
  - * -> [Condition: PIE + Canary + NX] -> Action: format strings often become the cleanest first-stage leak because they can disclose all three relevant bases/values in one interface.
- Simple automation:
  - `python3 -c 'from pwn import *; print(fmtstr_payload(6,{0x404040:0x4011d6},write_size="short"))'`

