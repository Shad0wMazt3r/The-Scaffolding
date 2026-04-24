## Runtime Manipulation & Hooking

- * -> [Condition: App executes on test device] -> Action: Primary Probe: attach Frida/Objection, enumerate classes, methods, views, and loaded libraries, then hook auth gates, root checks, crypto wrappers, JNI bridges, and anti-debug logic.
  - * -> [Condition: Objection can attach] -> Action: use it for quick filesystem, heap, keychain, and SSL exploration; Objection is a Frida-powered runtime toolkit for Android and iOS.
  - * -> [Condition: Anti-Frida or anti-debug triggers] -> Action: Dead End Pivot 1: spawn instead of attach, rename server/process artifacts, patch anti-Frida checks, or hook `ptrace`, `syscall`, and string-based detector functions.
  - * -> [Condition: Java/ObjC layer is thin] -> Action: Dead End Pivot 2: hook JNI/native exports, C functions, or Swift symbol boundaries to recover secrets and decision outcomes.
  - * -> [Condition: Runtime symbols are stripped] -> Action: Dead End Pivot 3: use behavior hooks on call sites, return values, and argument patterns instead of symbol names.
  - * -> [Condition: Boolean gate or secret recovered] -> Action: Data Chaining: use bypassed auth, hidden menus, decrypted blobs, or native tokens to reach backend endpoints or local privileged actions that static analysis could not trigger.
  - * -> [Condition: Device-state checks block testing] -> Action: add hooks for root/jailbreak, emulator, debugger, and mock-location checks before moving deeper.
- * -> [Condition: Non-root/non-jailbreak device is mandated] -> Action: Prefer repackaging with Frida Gadget where allowed because Objection supports `patchapk` and `patchipa` workflows for that mode.

Simple inline one-liner:
`frida-ps -Uai && objection -g <bundle_or_package> explore`

Script Definition Block — JNI Secret Interceptor
- Input Data: Suspect native library path, exported/native method list, Java/Swift call sites, runtime trigger sequence.
- Core Processing Logic:
  - Hook entry and return points of JNI/native functions tied to auth, pinning, or crypto.
  - Log plaintext arguments, derived keys, and decoded endpoint values.
  - Correlate outputs to network requests or local writes.
- Dependencies: Frida, `nm`/`otool`, Ghidra notes.
- Expected Output Format: JSON lines with `timestamp,function,args_preview,retval_preview,thread,trigger_screen,next_chain`.

