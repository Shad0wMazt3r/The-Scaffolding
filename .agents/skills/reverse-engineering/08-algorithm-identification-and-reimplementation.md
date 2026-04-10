## Algorithm Identification & Reimplementation

- Primary Probe
  - * -> [Condition: Unknown transform or keygen present] -> Action: classify by constants, rotation counts, block size, table layout, and state-machine shape; compare against AES/RC4/ChaCha/SHA/MD5/CRC/LFSR archetypes.
  - * -> [Condition: Hash/crypto suspected] -> Action: map round constants, endian behavior, message schedule style, and permutation structure before naming the primitive.
  - * -> [Condition: Home-grown checker] -> Action: lift the logic into clean pseudocode, replace machine-width artifacts with explicit typed operations, and derive algebraic constraints.
- Dead End Pivots
  - * -> [Condition: Constants are hidden] -> Action: break on table initialization and dump post-init memory, or derive constants from loop recurrence and rotation structure.
  - * -> [Condition: Algorithm is interleaved with junk] -> Action: slice by taint from final compare or output buffer to remove unrelated arithmetic.
  - * -> [Condition: Multiple candidate algorithms fit] -> Action: feed known test vectors or trace snapshots through each candidate model and eliminate mismatches.
- Data Chaining
  - * -> [Condition: Primitive identified] -> Action: reimplement it in a reference script and compare outputs against runtime snapshots byte-for-byte.
  - * -> [Condition: Key schedule recovered] -> Action: derive the exact secret-generation or verification pipeline and move to solver/replay.
  - * -> [Condition: Reimplementation matches] -> Action: use it to generate valid inputs, decrypt blobs, or reconstruct flags at scale.

Simple one-liners:
- `python3 -c "import zlib,sys; print(hex(zlib.crc32(open('blob','rb').read()) & 0xffffffff))"`
- `python3 -c "from pwn import *; print(hexdump(open('blob','rb').read()[:256]))"`

Script Definition Block — constant-signature matcher
- Input Data: immediates, tables, rotate counts, loop bounds, candidate round functions.
- Core Processing Logic:
  - Normalize constants by width and endianness.
  - Match against a signature bank of common crypto/hash/checksum primitives.
  - Score partial matches and annotate missing pieces.
  - Emit a hypothesis list with validation probes.
- Dependencies: Capstone or disassembler export, signature database, optional NumPy for table comparison.
- Expected Output Format: ranked JSON list with `algorithm`, `score`, `evidence`, `next_probe`.

