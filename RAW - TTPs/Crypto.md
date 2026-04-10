# Crypto - TTPs

Use an isolated workspace and keep raw artifacts separate from derived outputs:

```bash
mkdir -p /crypto/<challenge>/{ciphertext,keys,pcaps,transcripts,scripts,sage,evidence,notes,outputs}
python3 -m venv /crypto/<challenge>/.venv
source /crypto/<challenge>/.venv/bin/activate
pip install --upgrade pip
pip install pycryptodome cryptography angr z3-solver gmpy2
pip install git+https://github.com/RsaCtfTool/RsaCtfTool
sage -n jupyter
jupyter kernelspec list
jupyter kernelspec install --user $(sage -sh -c 'ls -d $SAGE_VENV/share/jupyter/kernels/sagemath') --name sagemath-ctf
```

That baseline matches the documented install paths for PyCryptodome, `cryptography`, `angr`, Z3’s Python bindings, SageMath’s Jupyter kernel, and RsaCtfTool’s preferred virtual-environment workflow.  PyCryptodome installs under `Crypto` with `pip install pycryptodome`, `cryptography` is typically installed with `pip install cryptography`, `angr` is recommended inside an isolated environment, and SageMath can be launched with `sage -n jupyter` and registered into an existing Jupyter install with `jupyter kernelspec install --user ...`. [arxiv](https://arxiv.org/pdf/2306.16812.pdf)

## Classical & Encoding
- Preconditions
  - * -> [Condition: Artifact is short text, printable bytes, or challenge label hints at “warmup/encoding/classical”] -> Action: fingerprint alphabet size, byte entropy, character frequency, digraphs, repeated trigrams, and base-encoding validity before assuming encryption.
  - * -> [Condition: Mixed alphabet plus `=`/URL-safe symbols] -> Action: test Base64/Base32/Base58/Base85 normalization first; many “crypto” CTFs are actually layered encoding plus light obfuscation.
  - * -> [Condition: Low entropy with preserved spacing/punctuation] -> Action: prioritize substitution, Caesar-family, affine, Vigenère, rail-fence, and transposition.
- Parameter fingerprinting
  - * -> [Condition: Single-byte domain or hex pairs] -> Action: score for XOR, nibble substitution, and bytewise affine transforms.
  - * -> [Condition: Repeating-key suspicion] -> Action: estimate key period from IoC/Kasiski/Hamming-distance minima.
- State machine
  - * -> [Condition: Frequency profile strongly matches a natural language] -> Action: run monoalphabetic/shift scoring as the **Primary Probe**.
  - * -> [Condition: Primary Probe weak or inconsistent] -> Action: **Dead End Pivot 1** to periodic-key tests; **Dead End Pivot 2** to transposition heuristics; **Dead End Pivot 3** to layered decode ordering.
  - * -> [Condition: One layer normalizes but output remains semi-structured] -> Action: preserve both raw and transformed artifacts in `evidence/` and recurse on the next layer.
- Data chaining
  - * -> [Condition: Recovered key period or substitution map is partial] -> Action: feed partial plaintext anchors into crib validation, then reuse recovered fragments to separate encoded wrapper from actual ciphertext.
- Simple triage one-liners
  - * -> [Condition: Need Base64 sanity check] -> Action: `import base64; base64.b64decode(s + '='*((4-len(s)%4)%4), validate=False)`
  - * -> [Condition: Need XOR repetition hint] -> Action: `from math import gcd; periods=[i for i in range(1,41) if ct[:len(ct)-i]==bytes(a^b==0 and a or a for a,b in zip(ct[i:],ct[:-i]))]`
- Complexity and tool choice
  - * -> [Condition: Search space is tiny or scoring-driven] -> Action: stay in Python; classical-cipher work is usually \(O(n)\) to \(O(kn)\) with small \(k\).
  - * -> [Condition: Algebraic key recovery on polynomials/permutations appears] -> Action: move to SageMath for symbolic manipulation.

## RSA Attacks
- Preconditions
  - * -> [Condition: Artifact includes PEM, DER, `(n,e)`, multiple public keys, or textbook RSA ciphertext] -> Action: record modulus bit length, exponent, prime-shape hints, ciphertext count, shared modulus reuse, and padding mode.
  - * -> [Condition: Unknown padding] -> Action: treat “successful decryption” claims as invalid until padding and message structure are separately confirmed.
- Parameter fingerprinting
  - * -> [Condition: Small `e`, many recipients, or identical plaintext suspicion] -> Action: flag broadcast/common-structure risk.
  - * -> [Condition: Near-square modulus or suspiciously similar keys] -> Action: flag Fermat/common-factor batch checks.
  - * -> [Condition: Partial private material or masked bits leak] -> Action: prepare a Sage notebook for lattice and small-root validation.
- State machine
  - * -> [Condition: Public key or `(n,e)` available] -> Action: use RsaCtfTool auto-analysis as the **Primary Probe** for weak-key classification and fast-path detection. [github](https://github.com/RsaCtfTool/RsaCtfTool)
  - * -> [Condition: Primary Probe yields no decisive path] -> Action: **Dead End Pivot 1** to batch GCD across all moduli; **Dead End Pivot 2** to close-prime geometry checks; **Dead End Pivot 3** to partial-information/lattice feasibility review.
  - * -> [Condition: Small-private-exponent hypotheses fail] -> Action: pivot from Wiener-style reasoning to broader lattice-based validation rather than deeper brute force.
- Data chaining
  - * -> [Condition: Batch GCD reveals one shared factor] -> Action: factor all affected keys, map key reuse, then correlate decrypted artifacts or signatures to a common operator or challenge stage.
  - * -> [Condition: Partial bit leak appears in logs or key masks] -> Action: convert the leak into a bounded polynomial model, validate candidate roots against the public key, then use only recovered metadata to unlock the next artifact.
- Simple triage one-liners
  - * -> [Condition: Need modulus profile] -> Action: `bits, small_e = n.bit_length(), e in {3,5,17,257,65537}`
  - * -> [Condition: Need common-factor scan pairwise on a small set] -> Action: `import math; hits=[(i,j,math.gcd(N[i],N[j])) for i in range(len(N)) for j in range(i+1,len(N)) if math.gcd(N[i],N[j])>1]`
- Complexity and tool choice
  - * -> [Condition: Parsing keys, batch GCD, and orchestration dominate] -> Action: use Python.
  - * -> [Condition: Coppersmith-style small roots, lattice reduction, or algebraic relation attacks dominate] -> Action: use SageMath.
  - * -> [Condition: Large-scale factoring is the only remaining angle] -> Action: treat runtime as infeasible unless challenge design clearly embeds a weak structure.

## Elliptic Curve Attacks
- Preconditions
  - * -> [Condition: Challenge exposes curve name, point coordinates, signatures, or custom EC arithmetic] -> Action: verify field prime, curve equation, group order, cofactor, point validation rules, and whether points are checked on receipt.
  - * -> [Condition: Repeated or biased nonces suspected in ECDSA/DSA-like signatures] -> Action: collect all signatures, message hashes, and nonce-side-channel observations before testing any recovery hypothesis.
- Parameter fingerprinting
  - * -> [Condition: Named curve with small factors in subgroup order] -> Action: flag Pohlig-Hellman feasibility.
  - * -> [Condition: Embedding degree or pairing-friendly behavior looks abnormal] -> Action: flag MOV-style reduction review.
  - * -> [Condition: Server accepts attacker-supplied points] -> Action: flag invalid-curve and small-subgroup validation failures.
- State machine
  - * -> [Condition: Signature corpus available] -> Action: start with nonce-correlation and duplicate-`r` analysis as the **Primary Probe**.
  - * -> [Condition: No duplicate nonce signal] -> Action: **Dead End Pivot 1** to partial-bias/HNP feasibility; **Dead End Pivot 2** to subgroup/order validation; **Dead End Pivot 3** to invalid-point acceptance testing.
  - * -> [Condition: Standard DLP path stalls] -> Action: pivot to group-structure decomposition before considering generic discrete-log effort.
- Data chaining
  - * -> [Condition: Partial nonce leakage is supported] -> Action: feed leaked bits into a lattice model, validate candidate private keys against the public point, then use the verified key only to confirm artifact access in the lab.
  - * -> [Condition: Invalid-curve acceptance is confirmed] -> Action: enumerate accepted subgroup orders, log residue leaks, and chain residues into CRT-style reconstruction of the secret scalar.
- Simple triage one-liners
  - * -> [Condition: Need duplicate-`r` detection] -> Action: `dups=[r for r in rs if rs.count(r)>1]`
  - * -> [Condition: Need on-curve validation] -> Action: `assert (y*y - (x*x*x + a*x + b)) % p == 0`
- Complexity and tool choice
  - * -> [Condition: Finite-field arithmetic and point validation dominate] -> Action: Python is fine.
  - * -> [Condition: Lattices, subgroup decomposition, or pairings dominate] -> Action: SageMath is the right environment.

## Symmetric Attacks
- Preconditions
  - * -> [Condition: Block size, IV/nonce behavior, and mode are unknown] -> Action: fingerprint by ciphertext length regularity, repeated-block structure, known headers, and API behavior under modified inputs.
  - * -> [Condition: Oracle interaction exists] -> Action: classify it as decrypt, padding-validity, tag-validity, timing, or format oracle before doing anything else.
- Parameter fingerprinting
  - * -> [Condition: Repeated 16-byte blocks] -> Action: flag ECB.
  - * -> [Condition: Stable IV or nonce reuse across same key] -> Action: flag CBC/GCM/CTR misuse immediately.
  - * -> [Condition: Malleability without integrity] -> Action: flag bit-flip or block-splice validation path.
- State machine
  - * -> [Condition: Static ciphertext set available] -> Action: run block/nonce/length analysis as the **Primary Probe**.
  - * -> [Condition: Static analysis is inconclusive] -> Action: **Dead End Pivot 1** to differential chosen-input testing; **Dead End Pivot 2** to error-channel classification; **Dead End Pivot 3** to metadata correlation across sessions.
  - * -> [Condition: Oracle exists but rate-limited] -> Action: optimize for minimal distinguishing queries and cache every response class.
- Data chaining
  - * -> [Condition: Reused nonce or keystream segment identified] -> Action: align affected records, isolate the overlap window, and pass only validated keystream relations to the next parser.
  - * -> [Condition: Padding-validity signal exists] -> Action: map response classes, confirm blockwise dependency, and then treat each validated byte inference as evidence rather than plaintext until rechecked.
- Simple triage one-liners
  - * -> [Condition: Need ECB repeated-block scan] -> Action: `from collections import Counter; reps=[b for b,c in Counter(ct[i:i+16] for i in range(0,len(ct),16)).items() if c>1]`
  - * -> [Condition: Need nonce-reuse detection] -> Action: `reuse = len(nonces) != len(set(nonces))`
- Complexity and tool choice
  - * -> [Condition: Parsing traffic, comparing blocks, and driving APIs dominate] -> Action: Python.
  - * -> [Condition: Differential trail search or algebraic fault modeling appears] -> Action: SageMath for the model, Python for the harness.

## Hash Attacks
- Preconditions
  - * -> [Condition: Raw hash is used as MAC or commitment without domain separation] -> Action: classify construction before testing collisions or extension properties.
  - * -> [Condition: Merkle-Damgård hash used as `hash(secret || msg)`] -> Action: flag length-extension exposure.
- Parameter fingerprinting
  - * -> [Condition: MD5/SHA1 present] -> Action: separate “collision-relevant” from “preimage-relevant” risk.
  - * -> [Condition: Unbounded attacker-controlled keys into hash tables or parsers] -> Action: flag hash-flooding/DoS path.
- State machine
  - * -> [Condition: Construction is visible] -> Action: start with composition review as the **Primary Probe**.
  - * -> [Condition: Construction hidden behind API] -> Action: **Dead End Pivot 1** to behavioral tests on appended data; **Dead End Pivot 2** to duplicate-prefix acceptance; **Dead End Pivot 3** to parser-side collision amplification review.
- Data chaining
  - * -> [Condition: Length-extension feasible] -> Action: derive the exact message framing requirements, then pass the verified framing into token/session revalidation in a sandbox.
  - * -> [Condition: Collision acceptance exists] -> Action: chain it into identity confusion, file-substitution, or certificate-parsing review depending on the challenge surface.
- Simple triage one-liners
  - * -> [Condition: Need algorithm family fingerprint from digest length] -> Action: `algos={16:'MD5',20:'SHA1',32:'SHA256',64:'SHA512'}.get(len(d), 'unknown')`
- Complexity and tool choice
  - * -> [Condition: Construction review dominates] -> Action: Python.
  - * -> [Condition: Differential-path or chosen-prefix mathematics dominate] -> Action: use specialized tooling and treat feasibility as challenge-specific, not generic.

## Protocol Attacks
- Preconditions
  - * -> [Condition: TLS, PKCS#1 v1.5, compressed secrets, legacy CBC, or signature parsing appear] -> Action: map protocol version, ciphersuite, transcript ordering, compression, certificate chain, and alert behavior.
  - * -> [Condition: Network capture exists] -> Action: preserve timing, packet boundaries, retransmits, and server error classes.
- Parameter fingerprinting
  - * -> [Condition: Distinct error paths for RSA decrypt/format checks] -> Action: flag Bleichenbacher-style oracle review.
  - * -> [Condition: Compression before encryption with reflected secrets] -> Action: flag CRIME/BREACH-style leakage class.
  - * -> [Condition: Legacy CBC over TLS 1.0 semantics] -> Action: flag BEAST/Lucky13-family review.
- State machine
  - * -> [Condition: Handshake or API transcript available] -> Action: begin with transcript normalization and oracle classification as the **Primary Probe**.
  - * -> [Condition: No explicit oracle signal] -> Action: **Dead End Pivot 1** to timing clustering; **Dead End Pivot 2** to cross-request length correlation; **Dead End Pivot 3** to parser differential testing.
- Data chaining
  - * -> [Condition: Oracle class confirmed] -> Action: convert each server response into a labeled state, then feed that state map into a minimal-query validation harness.
  - * -> [Condition: Signature verification discrepancy found] -> Action: chain the discrepancy into message-format confusion, certificate misuse, or token forgery review.
- Simple triage one-liners
  - * -> [Condition: Need response clustering stub] -> Action: `classes={(r.status, len(r.body), r.latency_bucket) for r in responses}`
- Complexity and tool choice
  - * -> [Condition: Traffic analysis and harness control dominate] -> Action: Python.
  - * -> [Condition: Formal transcript/state reasoning dominates] -> Action: pair Python with symbolic tooling.

## LCG & PRNG Attacks
- Preconditions
  - * -> [Condition: Session IDs, nonces, OTPs, challenge numbers, or game outputs look patterned] -> Action: collect ordered outputs with timestamps and any truncation rules.
  - * -> [Condition: Output count is small] -> Action: prioritize modulus/recurrence inference before seed guessing.
- Parameter fingerprinting
  - * -> [Condition: Linear relation under modular arithmetic appears] -> Action: flag LCG.
  - * -> [Condition: Bit-level filtration or combiner structure appears] -> Action: flag filter-generator or shrinking/clock-control family.
- State machine
  - * -> [Condition: Consecutive outputs available] -> Action: start with recurrence testing as the **Primary Probe**.
  - * -> [Condition: Probe weak because outputs are truncated or mixed] -> Action: **Dead End Pivot 1** to timestamp/seed-space pruning; **Dead End Pivot 2** to SAT/SMT modeling; **Dead End Pivot 3** to algebraic relation hunting across multiple traces.
- Data chaining
  - * -> [Condition: Internal state candidates survive consistency checks] -> Action: use them only to predict the next few lab outputs and confirm the model before trusting any broader conclusion.
  - * -> [Condition: Partial state leaks across sessions] -> Action: merge traces by clock window or process restart markers.
- Simple triage one-liners
  - * -> [Condition: Need first-difference view] -> Action: `diffs=[(outs[i+1]-outs[i]) for i in range(len(outs)-1)]`
- Complexity and tool choice
  - * -> [Condition: Small-state arithmetic dominates] -> Action: Python.
  - * -> [Condition: bit-vector constraints or filtered generators dominate] -> Action: Z3 or SageMath, depending on whether the model is Boolean-heavy or number-theoretic.

## Custom & Unknown Cipher Analysis
- Preconditions
  - * -> [Condition: No algorithm ID, challenge author hints “homemade,” or code artifact is available] -> Action: separate serialization, compression, padding, checksum, and encryption layers before naming the primitive.
  - * -> [Condition: Binary or source available] -> Action: treat implementation review as first-class evidence, not a later step.
- Parameter fingerprinting
  - * -> [Condition: Block regularity, S-box tables, Feistel/SPN round constants, or rotate-xor-add patterns appear] -> Action: classify structure before attempting any cryptanalysis.
  - * -> [Condition: Mixed symbolic conditions and opaque control flow appear] -> Action: prepare angr/Z3 for path and constraint recovery. `angr` is documented for Python 3.10+ and is intended for use inside a Python environment, while Z3’s Python bindings are installed via `pip install z3-solver`. [docs.angr](https://docs.angr.io/en/latest/getting-started/installing.html)
- State machine
  - * -> [Condition: Source or decompilation available] -> Action: start with round-function and key-schedule extraction as the **Primary Probe**.
  - * -> [Condition: No source-level clarity] -> Action: **Dead End Pivot 1** to known-plaintext differential behavior; **Dead End Pivot 2** to symbolic execution over reduced rounds; **Dead End Pivot 3** to black-box distinguishers on avalanche and linearity.
- Data chaining
  - * -> [Condition: Round constants or subkeys are partially exposed] -> Action: feed them into a reduced-round model, validate against test vectors, then extend only if the model keeps matching.
  - * -> [Condition: Serialization wrapper is stripped] -> Action: hand the normalized core ciphertext to the correct downstream family state machine.
- Script Definition Block
  - Input Data: binary/source, sample plaintext-ciphertext pairs, challenge wrapper format, any provided keys or constants.
  - Core Processing Logic:
    - Parse container and remove framing layers.
    - Recover block size, endianness, and round boundaries.
    - Identify substitutions, permutations, rotations, modular additions, and key-schedule dependencies.
    - Build a reduced-round symbolic model and test consistency against known vectors.
  - Dependencies: Python, angr, z3-solver, optional SageMath for algebraic components.
  - Expected Output Format: JSON with `family_guess`, `block_size`, `round_count_estimate`, `key_schedule_notes`, `candidate_invariants`, `validated_test_vectors`.
- Complexity and tool choice
  - * -> [Condition: Reverse engineering and harnessing dominate] -> Action: Python plus angr.
  - * -> [Condition: algebraic invariants, Gröbner-style reasoning, or lattice structure dominates] -> Action: SageMath.

## Zero-Knowledge & Commitment Scheme Weaknesses
- Preconditions
  - * -> [Condition: Sigma protocol, Fiat-Shamir transform, Pedersen-style commitment, or SNARK/STARK verification code appears] -> Action: record statement language, transcript structure, challenge derivation, randomness source, and subgroup checks.
  - * -> [Condition: Custom transcript hashing or manual challenge assembly exists] -> Action: flag domain-separation and replay risk.
- Parameter fingerprinting
  - * -> [Condition: Commitment base points not independently generated or subgroup checks missing] -> Action: flag binding/hiding ambiguity.
  - * -> [Condition: Fiat-Shamir challenge omits public inputs or context] -> Action: flag transcript malleability and replay.
- State machine
  - * -> [Condition: Verifier code available] -> Action: begin with relation completeness and transcript-binding review as the **Primary Probe**.
  - * -> [Condition: Primary review is clean] -> Action: **Dead End Pivot 1** to randomness reuse checks; **Dead End Pivot 2** to subgroup/cofactor validation; **Dead End Pivot 3** to challenge-domain collision review.
- Data chaining
  - * -> [Condition: Commitment randomness is reused] -> Action: correlate transcripts, test whether witness relations become linearly exposed, and pass only validated algebraic relations into the next model.
  - * -> [Condition: Transcript binding is incomplete] -> Action: map omitted fields and verify whether altered transcripts still satisfy the verifier.
- Simple triage one-liners
  - * -> [Condition: Need transcript-field completeness check] -> Action: `missing=[f for f in required_fields if f not in transcript_hash_inputs]`
- Complexity and tool choice
  - * -> [Condition: Parsing transcripts and verifier logic dominate] -> Action: Python.
  - * -> [Condition: group algebra, polynomial identities, or soundness edge cases dominate] -> Action: SageMath.

If you want this transformed into a challenge-ready worksheet, the next most useful format is a per-artifact template with fixed fields for `fingerprint`, `oracle class`, `evidence`, `pivot chosen`, and `next-state`.