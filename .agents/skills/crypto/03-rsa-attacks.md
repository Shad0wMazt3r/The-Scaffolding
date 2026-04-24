## RSA Attacks

- Preconditions
  - [Condition: Artifact has PEM, DER, (n,e), multiple keys, or textbook ciphertext] → Record modulus bit length, exponent, prime-shape hints, ciphertext count, shared modulus, padding mode
  - [Condition: Unknown padding] → Treat "successful decryption" as invalid until padding and message structure separately confirmed

- Parameter fingerprinting
  - [Condition: Small e, many recipients, identical plaintext suspicion] → Flag broadcast/common-structure risk
  - [Condition: Near-square modulus or suspiciously similar keys] → Flag Fermat/common-factor batch checks
  - [Condition: Partial private material or masked bits leak] → Prepare Sage notebook for lattice and small-root validation

- State machine
  - [Condition: Public key or (n,e) available] → **Primary Probe:** RsaCtfTool auto-analysis for weak-key classification and fast-path detection
  - [Condition: Primary Probe yields no path] → **Pivot 1:** batch GCD across all moduli; **Pivot 2:** close-prime geometry; **Pivot 3:** partial-information/lattice feasibility
  - [Condition: Small-private-exponent hypotheses fail] → Pivot to lattice-based validation over deeper brute force

- Data chaining
  - [Condition: Batch GCD reveals shared factor] → Factor all affected keys, map reuse, correlate decrypted artifacts to common operator or stage
  - [Condition: Partial bit leak in logs or key masks] → Convert leak to bounded polynomial model, validate roots against public key, use recovered metadata to unlock next artifact

- Triage one-liners
  - Modulus profile: `bits, small_e = n.bit_length(), e in {3,5,17,257,65537}`
  - Common-factor scan: `import math; hits=[(i,j,math.gcd(N[i],N[j])) for i in range(len(N)) for j in range(i+1,len(N)) if math.gcd(N[i],N[j])>1]`

- Tool choice
  - [Condition: Parsing, batch GCD, orchestration dominate] → Python
  - [Condition: Coppersmith small-roots, lattice reduction, algebraic attacks dominate] → SageMath
  - [Condition: Large-scale factoring only remaining] → Infeasible unless challenge embeds weak structure

***
