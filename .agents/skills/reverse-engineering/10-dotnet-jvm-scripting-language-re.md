## .NET / JVM / Scripting Language RE

- Primary Probe
  - * -> [Condition: Managed sample detected] -> Action: choose dnSpy/ILSpy for .NET, jadx for JVM/Android, and source-first reconstruction for PyInstaller, zipapp, or Electron/ASAR packages.
  - * -> [Condition: .NET] -> Action: inspect resources, embedded assemblies, Confuser-style control-flow transforms, string decryptors, delegate trampolines, and reflection-heavy loaders.
  - * -> [Condition: JVM/Android] -> Action: decompile APK/JAR, inspect manifest/entry components, native JNI bridges, reflection, dynamic class loading, and asset/resource blobs.
  - * -> [Condition: PyInstaller/Electron/Node] -> Action: extract the archive, locate entry scripts, inspect bytecode bundles or ASAR contents, then treat native addons as separate RE targets.
- Dead End Pivots
  - * -> [Condition: Reflection hides real control flow] -> Action: log resolved method names and types at runtime, then map them back to decompiled stubs.
  - * -> [Condition: Obfuscator destroys names/strings] -> Action: hook string decryptors and resource loaders, dump plaintext results, and repopulate the decompiler database.
  - * -> [Condition: Managed wrapper delegates to native validator] -> Action: pivot to the native DLL/SO and continue with the static/dynamic sections above.
- Data Chaining
  - * -> [Condition: Decompiler reveals resource-embedded payload] -> Action: extract and re-triage it as a fresh sample.
  - * -> [Condition: Managed validation logic is readable] -> Action: reimplement directly and solve constraints at source/IL level before touching native instrumentation.
  - * -> [Condition: JNI/PInvoke boundary found] -> Action: set argument/return capture hooks there; that is often the narrowest point for flag or secret extraction.

Simple one-liners:
- `jadx -d out_apk app.apk`
- `python3 -m pyinstxtractor.py sample.exe`
- `npx asar extract app.asar extracted_app/`
