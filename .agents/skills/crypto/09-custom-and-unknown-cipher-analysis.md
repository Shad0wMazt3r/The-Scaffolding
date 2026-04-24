## Custom & Unknown Cipher Analysis

- Preconditions
  - [Condition: No algorithm ID, "homemade" hints, or code available] → Separate serialization, compression, padding, checksum, encryption before naming primitive
  - [Condition: Binary or source available] → Treat implementation review as first-class evidence

- Parameter fingerprinting
  - [Condition: Block regularity, S-boxes, Feistel/SPN constants, rotate-xor-add patterns appear] → Classify structure before cryptanalysis
  - [Condition: Mixed symbolic conditions and opaque control flow] → Prepare angr/Z3 for path and constraint recovery

- State machine
  - [Condition: Source or decompilation available] → **Primary Probe:** round-function and key-schedule extraction
  - [Condition: No source-level clarity] → **Pivot 1:** known-plaintext differential behavior; **Pivot 2:** symbolic execution over reduced rounds; **Pivot 3:** black-box distinguishers (avalanche, linearity)

- Data chaining
  - [Condition: Round constants/subkeys partially exposed] → Feed into reduced-round model, validate against test vectors, extend if matches
  - [Condition: Serialization wrapper stripped] → Hand normalized ciphertext to correct downstream state machine

- Analysis Pipeline
  - Parse container, remove framing layers
  - Recover block size, endianness, round boundaries
  - Identify substitutions, permutations, rotations, modular additions, key-schedule dependencies
  - Build reduced-round symbolic model; test consistency against known vectors
  - Output: `family_guess`, `block_size`, `round_count_estimate`, `key_schedule_notes`, `test_vector_validation`

- Tool choice
  - [Condition: Reverse engineering and harnessing dominate] → Python + angr
  - [Condition: Algebraic invariants or Gröbner reasoning dominate] → SageMath

***
