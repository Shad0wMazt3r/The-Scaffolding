## Cryptographic Artifact Recovery

- Primary Probe
  - * -> [Condition: Encrypted archive, volume, or blob is present] -> Action: identify format first, then separate “find key material” from “attack password”; do not brute-force until you have harvested every hint from memory, notes, logs, filenames, and metadata.
  - * -> [Condition: Memory image exists] -> Action: search for passphrases, key files, wallet seeds, SSH private keys, browser-saved secrets, and mounted-volume indicators before touching hashcat.
  - * -> [Condition: Password hashes or tickets are exposed] -> Action: extract them cleanly, classify the scheme, and prioritize smart wordlists from case artifacts over generic masks.

- Dead End Pivots
  - * -> [Condition: Password guesses fail] -> Action: derive candidate rules from usernames, hostnames, challenge titles, timestamps, leetspeak, and file metadata rather than expanding brute force blindly.
  - * -> [Condition: Volume header is damaged] -> Action: carve backup headers, inspect nearby sectors or appended keyfiles, and test repaired headers on copies only.
  - * -> [Condition: Archive opens but content is still opaque] -> Action: look for nested XOR/base64/compression layers and treat “decrypted” output as a new artifact, not an endpoint.

- Data Chaining
  - * -> [Condition: Recovered key decrypts PCAP/TLS/archive content] -> Action: push the plaintext back into timeline, network, and file-format analysis.
  - * -> [Condition: Hash cracking reveals user password reuse] -> Action: test it against steghide, ZIP/7z, VeraCrypt, browser profiles, and note files.
  - * -> [Condition: Keyfile path is referenced in logs or LNKs] -> Action: recover that file from disk or carve it from unallocated space.

- Simple one-liners
  - `strings -a raw/mem.raw | grep -Ei 'pass|pwd|secret|token|key|wallet|seed' > memory/crypto_hints.txt`
  - `zip2john evidence/archive.zip > evidence/archive.hash`
  - `7z2hashcat.pl evidence/archive.7z > evidence/archive_7z.hash`

