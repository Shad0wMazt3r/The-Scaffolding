## Static Analysis & Reverse Engineering

- * -> [Condition: Artifact acquired] -> Action: Run `jadx`, `apktool`, IPA unzip, plist parsing, Mach-O / `.so` string extraction, and manifest / entitlements review as the **primary probe**.
  - * -> [Condition: Source is readable] -> Action: Map auth flows, hardcoded URLs, GraphQL schemas, feature flags, third-party SDKs, root/jailbreak checks, crypto wrappers, and local storage entry points.
  - * -> [Condition: No signal from normal decompilation] -> Action: Dead End Pivot 1: `apktool d app.apk -o out && grep -RniE 'secret|token|debug|trust|pin|allowBackup|exported' out/`
  - * -> [Condition: No signal from normal decompilation] -> Action: Dead End Pivot 2: `find . -name '*.so' -o -name '*.dylib' | xargs strings | grep -Ei 'api|key|token|secret|bearer|private'`
  - * -> [Condition: Obfuscation blocks logic recovery] -> Action: Dead End Pivot 3: switch to resource/manifest correlation, call-graph recovery in Ghidra, and runtime class/method enumeration through Frida.
  - * -> [Condition: Secret, endpoint, or feature toggle found] -> Action: Data Chaining: trace the constant into the exact HTTP path, auth header, or JNI export it feeds; replay the request in Burp; then test whether the same server object model exposes IDOR, role confusion, or environment drift.
  - * -> [Condition: Root / jailbreak detection found statically] -> Action: Queue those function names for runtime hook targets before launching dynamic analysis.
- * -> [Condition: Android manifest review] -> Action: Inspect `android:exported`, permissions, backup flags, providers, app links, task affinity, debuggable state, and custom `networkSecurityConfig`; exported controls whether outside apps can launch components. [developer.android](https://developer.android.com/privacy-and-security/risks/android-exported)
- * -> [Condition: iOS bundle review] -> Action: Inspect `Info.plist`, URL schemes, associated domains, ATS exceptions, keychain groups, app groups, background modes, and entitlements for over-privilege or unexpected cross-app exposure.

Script Definition Block — Native Secret Mapper  
- Input Data: Decompiled Java/Kotlin or Objective-C/Swift symbols, `.so` / Mach-O exports, `strings` output, endpoint list.  
- Core Processing Logic:
  - Correlate JNI or native export names to Java/Swift call sites.
  - Rank strings by entropy, credential patterns, hostname likeness, and request adjacency.
  - Emit a map from secret candidate -> calling function -> network/API consumer.
- Dependencies: `jadx`, `nm`, `objdump` or `otool`, `strings`, optional Ghidra export.
- Expected Output Format: CSV with `artifact,function,secret_candidate,confidence,linked_endpoint,next_probe`.

