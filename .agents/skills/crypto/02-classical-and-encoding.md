## Classical & Encoding

- Preconditions
  - [Condition: Short text, printable bytes, or "warmup/encoding/classical" hints] → Fingerprint alphabet size, entropy, character frequency, digraphs, repeated trigrams, base-encoding validity
  - [Condition: Mixed alphabet + `=`/URL-safe symbols] → Test Base64/Base32/Base58/Base85 normalization; many CTF "crypto" are layered encoding + obfuscation
  - [Condition: Low entropy with spacing/punctuation] → Prioritize substitution, Caesar, affine, Vigenère, rail-fence, transposition

- Parameter fingerprinting
  - [Condition: Single-byte domain or hex pairs] → Score XOR, nibble substitution, bytewise affine
  - [Condition: Repeating-key suspicion] → Estimate key period via IoC/Kasiski/Hamming-distance minima

- State machine
  - [Condition: Frequency profile matches natural language] → **Primary Probe:** monoalphabetic/shift scoring
  - [Condition: Primary Probe weak/inconsistent] → **Pivot 1:** periodic-key tests; **Pivot 2:** transposition; **Pivot 3:** layered decode ordering
  - [Condition: One layer normalizes, output semi-structured] → Preserve both raw and transformed in evidence/; recurse next layer

- Data chaining
  - [Condition: Partial key period or substitution map] → Feed partial plaintext anchors into crib validation, reuse fragments to separate wrapper from actual ciphertext

- Triage one-liners
  - Base64 sanity: `import base64; base64.b64decode(s + '='*((4-len(s)%4)%4), validate=False)`
  - XOR repetition: `from math import gcd; periods=[i for i in range(1,41) if ct[:len(ct)-i]==bytes(a^b==0 and a or a for a,b in zip(ct[i:],ct[:-i]))]`

- Tool choice
  - [Condition: Tiny search space or scoring-driven] → Python (usually O(n) to O(kn) with small k)
  - [Condition: Algebraic key recovery on polynomials/permutations] → SageMath for symbolic manipulation

***
