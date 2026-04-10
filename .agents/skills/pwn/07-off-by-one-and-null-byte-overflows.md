## Off-by-One & Null Byte Overflows

- Primary Probe:
  - * -> [Condition: Single-byte overwrite or stray terminator is suspected] -> Action: determine whether the target byte lands in saved frame state, chunk size metadata, a string terminator boundary, or a length field.
- Dead End Pivots:
  - * -> [Condition: Saved return address is unreachable] -> Action: look for saved RBP corruption and use `leave; ret` style frame walking to gain a stack pivot.
  - * -> [Condition: Heap metadata impact seems minor] -> Action: model null-byte size shrinking, chunk consolidation side effects, and phantom-chunk creation rather than expecting immediate arbitrary write.
  - * -> [Condition: Only string truncation is visible] -> Action: abuse it as an authentication, pathname, or parser-boundary bug first, then revisit memory impact.
- Data Chaining:
  - * -> [Condition: Null byte hits chunk size / prev_inuse path] -> Action: convert the byte-level corruption into overlapping chunks or consolidation abuse, then recover arbitrary allocation/write.
  - * -> [Condition: Off-by-one hits saved frame state] -> Action: drive a controlled stack pivot to a second-stage ROP chain in a writable region.
  - * -> [Condition: Remote variance is high] -> Action: reduce payload entropy and make heap layout deterministic before attempting byte-precise corruption.
- Mitigation branches:
  - * -> [Condition: Canary present] -> Action: a one-byte write is often better spent below the canary, against frame pointers or metadata, than on the canary itself.

