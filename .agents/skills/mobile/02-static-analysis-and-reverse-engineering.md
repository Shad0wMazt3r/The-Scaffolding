## Static Analysis & Reverse Engineering

- **[Primary Probe]** `jadx`, `apktool`, IPA unzip, plist parse, Mach-O/`.so` strings, manifest/entitlements review
  - **[Source readable]** Map auth flows, URLs, GraphQL, feature flags, SDKs, root/jailbreak checks, crypto, storage entry points
  - **[No signal from decompilation]** Pivot 1: `apktool d app.apk -o out && grep -RniE 'secret|token|debug|trust|pin|allowBackup|exported' out/`
  - **[No signal from decompilation]** Pivot 2: `find . -name '*.so' -o -name '*.dylib' | xargs strings | grep -Ei 'api|key|token|secret|bearer'`
  - **[Obfuscation blocks logic]** Pivot 3: resource/manifest correlation, call-graph in Ghidra, runtime class/method enum via Frida
  - **[Secret/endpoint/flag found]** Data Chaining: trace to HTTP path/auth header/JNI export → replay in Burp → test IDOR/role/env drift
  - **[Root/jailbreak detection found]** Queue function names for runtime hook targets

- **[Android manifest]** Check `android:exported`, permissions, backup, providers, app-links, task-affinity, debuggable, `networkSecurityConfig`

- **[iOS bundle]** Check `Info.plist`, URL schemes, associated domains, ATS exceptions, keychain groups, app groups, background modes, entitlements

***
