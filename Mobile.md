# Mobile - TTPs

Use this fixed workspace so artifacts, hooks, traffic, and evidence stay correlated across static and runtime phases:

```text
/mobile/<target>/
├── apk/
│   ├── original/
│   ├── jadx/
│   ├── apktool/
│   └── rebuilt/
├── ipa/
│   ├── original/
│   ├── unzip/
│   ├── classdump/
│   └── decrypted/
├── frida/
│   ├── android/
│   ├── ios/
│   ├── common/
│   └── traces/
├── burp/
│   ├── project/
│   ├── certs/
│   └── logger/
├── evidence/
│   ├── screenshots/
│   ├── pcaps/
│   ├── requests/
│   ├── storage/
│   └── runtime/
└── reports/
    ├── notes.md
    ├── vulns/
    └── repro/
```

- Baseline host stack: Android Studio emulator, `adb`, `jadx`, `apktool`, `burp`, `frida-tools`, `objection`, `mitmproxy`, `ghidra`, `radare2`, `sqlite3`, `libimobiledevice`, `ideviceinstaller`, `iproxy`, `class-dump`, `plutil`, `keychain_dumper`, `Cycript` or Frida-only iOS flow.
- On Android, keep `adb` ready for both Activity Manager and content-provider entry points because `adb shell am` and `adb shell content` expose those attack surfaces directly from shell. [stackoverflow](https://stackoverflow.com/questions/27988069/query-android-content-provider-from-command-line-adb-shell)
- For TLS interception, assume Android trusts system CAs by default, and note that apps targeting API 23 or lower also trust user-added CAs by default unless app configuration changes that trust behavior. [developer.android](https://developer.android.com/privacy-and-security/security-config)
- For Android backup review, check whether the target targets and runs on Android 6.0+ because Auto Backup applies there and can expose app data selection rules. [developer.android](https://developer.android.com/identity/data/autobackup)
- For iOS, treat Keychain, app container files, URL-scheme handlers, and pasteboard as first-class data sources because Keychain stores small secrets in an encrypted database, `canOpenURL` reveals whether a scheme handler exists, and `UIPasteboard` is a cross-app data-sharing primitive. [developer.apple](https://developer.apple.com/documentation/security/keychain-services)
- On jailbroken iOS, deploy Frida through the Frida repository package path, and on non-jailbroken devices prefer `objection patchipa` / `patchapk` with Frida Gadget when the assessment allows repackaging. [appsecsanta](https://appsecsanta.com/objection)

- Android setup:
  - `adb devices -l && adb shell getprop ro.build.version.release`
  - `apktool d /mobile/<target>/apk/original/app.apk -o /mobile/<target>/apk/apktool`
  - `jadx -d /mobile/<target>/apk/jadx /mobile/<target>/apk/original/app.apk`
  - `adb push frida-server /data/local/tmp/ && adb shell "su -c 'chmod 755 /data/local/tmp/frida-server && /data/local/tmp/frida-server &'"`
  - `objection -g <package.name> explore`
  - Proxy: set Burp listener on `127.0.0.1:8080`, install Burp CA to emulator or user store, then verify whether app pins or overrides trust with manifest / `network_security_config`.
- iOS setup:
  - Jailbroken: install Filza, OpenSSH, Frida package, confirm `ssh root@<device-ip>` and `frida-ps -U`.
  - Non-jailbroken: decrypt IPA if allowed, patch with Frida Gadget, sideload to dedicated test device.
  - SSH/USB bridge: `iproxy 2222 22` then `ssh -p 2222 root@127.0.0.1`
  - Filza path targets: `/var/mobile/Containers/Data/Application/<UUID>/`, app group containers, `Library/Preferences`, `Library/Caches`, `Documents`, `tmp`.
- SSL-kill deployment:
  - Android: keep generic pinning bypass Frida scripts plus manual trust-manager and OkHttp hooks.
  - iOS: keep SSL Kill Switch 2 where compatible; if it fails, fall back to Frida method hooks on `NSURLSession`, `SecTrustEvaluate*`, or custom wrappers.
- Evidence discipline:
  - Save every decompiled path, intercepted request, Frida trace, sqlite dump, and screenshot under one timestamped case folder.
  - Name files with `<phase>_<component>_<finding>_<timestamp>` so chains stay reproducible.

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

## Certificate Pinning & SSL Bypass

- * -> [Condition: App launches and proxy is configured] -> Action: Primary Probe: route traffic through Burp/mitmproxy and observe whether requests fail, disappear, or switch transports.
  - * -> [Condition: Normal interception works] -> Action: Test auth-state replay, certificate error handling, environment switching, and whether WebView traffic differs from native stack.
  - * -> [Condition: No signal because pinning blocks traffic] -> Action: Dead End Pivot 1: use Objection SSL bypass or generic Frida hooks against common Java stacks; Objection is built on Frida and is commonly used to disable certificate pinning interactively. [appsecsanta](https://appsecsanta.com/objection)
  - * -> [Condition: Generic bypass fails] -> Action: Dead End Pivot 2: hook the app’s custom trust manager / OkHttp `CertificatePinner` / `HostnameVerifier`, or on iOS hook `NSURLSession`, trust-evaluation calls, and wrapper methods around `SecTrust`.
  - * -> [Condition: Pinning is partly native] -> Action: Dead End Pivot 3: patch smali or hook JNI/native verification routines and re-sign the APK, or instrument the iOS binary around trust-evaluation branches.
  - * -> [Condition: Traffic becomes visible] -> Action: Data Chaining: capture login, refresh, device-binding, and feature-flag requests; use any secret or token discovered in static analysis to authenticate requests and probe backend authorization drift.
  - * -> [Condition: Local bypass only] -> Action: Remote-vs-local divergence: if exploitation requires a rooted or repackaged client, reframe as malware-on-device / hostile-OS / rogue-device threat; if the same weakness permits MITM on stock devices, escalate to remote account compromise.
- * -> [Condition: Android trust behavior unclear] -> Action: Check manifest and `network_security_config` because Android’s trust handling can differ by app configuration and target API, including user-added CA trust on older-targeted apps. [developer.android](https://developer.android.com/privacy-and-security/security-config)

Simple inline one-liner:  
`frida -U -f <package> -l /mobile/<target>/frida/common/ssl_bypass.js --no-pause`

Script Definition Block — Custom Pinning Locator  
- Input Data: Decompiled classes, stack traces from failed TLS sessions, runtime-loaded class names.
- Core Processing Logic:
  - Search for trust manager, pinner, host verifier, or trust-evaluation wrappers.
  - Match failure stack frames to candidate methods.
  - Generate hook plan: method name, return type, bypass behavior, evidence path.
- Dependencies: `jadx`, Frida, logcat or iOS device logs.
- Expected Output Format: Markdown table with `class/method,platform,hook_strategy,expected_result,verification_step`.

## Insecure Data Storage

- * -> [Condition: App container accessible] -> Action: Primary Probe: inspect SharedPreferences, Room/SQLite DBs, plist files, caches, logs, WebView storage, cookies, and Keychain / Keystore usage.
  - * -> [Condition: Android package is debuggable or testable on rooted device] -> Action: `adb shell "su -c 'cd /data/data/<package> && find . -maxdepth 3 -type f | sort'"` 
  - * -> [Condition: iOS app container reachable] -> Action: browse `Documents`, `Library/Preferences`, `Library/Caches`, and Keychain-linked artifacts through Filza or SSH.
  - * -> [Condition: No cleartext secrets found] -> Action: Dead End Pivot 1: inspect backup pathways, including Android extraction rules and iTunes/iCloud-style app backup artifacts where permitted; Android Auto Backup exists for Android 6.0+ targets. [developer.android](https://developer.android.com/identity/data/autobackup)
  - * -> [Condition: Filesystem looks clean] -> Action: Dead End Pivot 2: hook runtime reads/writes for `SharedPreferences`, `sqlite`, `NSUserDefaults`, `SecItemAdd`, `SecItemCopyMatching`, and log sinks to catch transient secrets.
  - * -> [Condition: Secrets may be native-protected] -> Action: Dead End Pivot 3: hook JNI or iOS crypto wrappers before encryption/decryption boundaries to capture plaintext in memory.
  - * -> [Condition: Token, key, or PII found] -> Action: Data Chaining: replay the token against live endpoints, test token scope and expiry, then correlate stored user IDs or device IDs into IDOR, session fixation, or account recovery abuse.
  - * -> [Condition: Finding is local-only] -> Action: Remote-vs-local divergence: classify whether compromise requires physical/device control or whether cloud backups, logs, or sync endpoints expose the same material remotely.
- * -> [Condition: iOS secret storage observed] -> Action: Treat Keychain items as high-value because Keychain Services is intended for encrypted storage of small secrets. [developer.apple](https://developer.apple.com/documentation/security/keychain-services)

Simple inline one-liner:  
`sqlite3 app.db ".tables" && sqlite3 app.db "select * from users limit 20;"`

## Deeplink & Intent Abuse (Android)

- * -> [Condition: Manifest and intent filters extracted] -> Action: Primary Probe: enumerate custom schemes, browsable activities, app links, exported receivers/services, and intent extras accepted by each entry point.
  - * -> [Condition: Deep link handlers identified] -> Action: `adb shell am start -W -a android.intent.action.VIEW -d 'target://path?uid=1&next=/admin' <package>`
  - * -> [Condition: No obvious exploitable path] -> Action: Dead End Pivot 1: fuzz extras, serialized objects, and nested intents for hidden routes, auth skips, or privilege confusion.
  - * -> [Condition: App Links are present but custom schemes are absent] -> Action: Dead End Pivot 2: validate associated-domain routing, fallback browser behavior, and whether unverified links still open internal screens; verified App Links are the Android 6+ mechanism for trusted website-to-app deep linking. [developer.android](https://developer.android.com/training/app-links)
  - * -> [Condition: Route handling is guarded] -> Action: Dead End Pivot 3: target task affinity, `singleTask`/`singleTop`, pending intents, or auth-race windows created during cold start.
  - * -> [Condition: Internal screen opens or parameter reaches backend] -> Action: Data Chaining: pivot from route parameter control to WebView load, object ID substitution, support-ticket view, payment state tampering, or password-reset token reuse.
  - * -> [Condition: Parcelable objects are accepted] -> Action: Test Parcel serialization mismatch or type confusion against exported components for privilege escalation or crash-to-bypass conditions.
- * -> [Condition: External invocation control matters] -> Action: Remember that `android:exported` determines whether other apps can launch a component, so any browsable or exported handler deserves full hostile-intent testing. [developer.android](https://developer.android.com/privacy-and-security/risks/android-exported)

Simple inline one-liner:  
`adb shell am start -n <package>/<activity> --es role admin --es uid 1001 --ez skipAuth true`

## WebView Attacks

- * -> [Condition: App embeds WebView] -> Action: Primary Probe: identify load sources, JavaScript settings, bridge exposure, file access, mixed content, cookie scope, and navigation handling.
  - * -> [Condition: URL origin is attacker-influenced] -> Action: test open redirects, deep-link-fed loads, notification-fed URLs, and universal XSS paths.
  - * -> [Condition: No direct load control] -> Action: Dead End Pivot 1: inspect `addJavascriptInterface`, custom URL handlers, and postMessage-like bridges for methods reachable from untrusted content.
  - * -> [Condition: Bridge is hidden by obfuscation] -> Action: Dead End Pivot 2: enumerate bridge objects and WebView methods at runtime with Frida or Objection, then hook `loadUrl`, `evaluateJavascript`, and `shouldOverrideUrlLoading`.
  - * -> [Condition: File access path is unclear] -> Action: Dead End Pivot 3: test `file://`, `content://`, local HTML assets, and exported content providers feeding WebView.
  - * -> [Condition: JS bridge or URL load is controllable] -> Action: Data Chaining: escalate from arbitrary URL load to cookie theft, privileged native method invocation, token exfiltration, or backend action execution under the app session.
  - * -> [Condition: Traffic differs from native API traffic] -> Action: Split testing between WebView transport and native HTTP client because pinning, cookies, and header logic often diverge.
- * -> [Condition: WebView configuration review] -> Action: Treat JavaScript enablement and embedded web-app behavior as a separate trust boundary because Android WebView is an in-app browser surface with its own configuration and security implications. [mas.owasp](https://mas.owasp.org/MASTG-KNOW-0018/)

Simple inline one-liner:  
`grep -Rni "addJavascriptInterface\|setJavaScriptEnabled\|allowFileAccess\|loadUrl(" /mobile/<target>/apk/jadx`

## Runtime Manipulation & Hooking

- * -> [Condition: App executes on test device] -> Action: Primary Probe: attach Frida/Objection, enumerate classes, methods, views, and loaded libraries, then hook auth gates, root checks, crypto wrappers, JNI bridges, and anti-debug logic.
  - * -> [Condition: Objection can attach] -> Action: use it for quick filesystem, heap, keychain, and SSL exploration; Objection is a Frida-powered runtime toolkit for Android and iOS. [dev](https://dev.to/whatminjacodes/mobile-security-tools-part-3-objection-531h)
  - * -> [Condition: Anti-Frida or anti-debug triggers] -> Action: Dead End Pivot 1: spawn instead of attach, rename server/process artifacts, patch anti-Frida checks, or hook `ptrace`, `syscall`, and string-based detector functions.
  - * -> [Condition: Java/ObjC layer is thin] -> Action: Dead End Pivot 2: hook JNI/native exports, C functions, or Swift symbol boundaries to recover secrets and decision outcomes.
  - * -> [Condition: Runtime symbols are stripped] -> Action: Dead End Pivot 3: use behavior hooks on call sites, return values, and argument patterns instead of symbol names.
  - * -> [Condition: Boolean gate or secret recovered] -> Action: Data Chaining: use bypassed auth, hidden menus, decrypted blobs, or native tokens to reach backend endpoints or local privileged actions that static analysis could not trigger.
  - * -> [Condition: Device-state checks block testing] -> Action: add hooks for root/jailbreak, emulator, debugger, and mock-location checks before moving deeper.
- * -> [Condition: Non-root/non-jailbreak device is mandated] -> Action: Prefer repackaging with Frida Gadget where allowed because Objection supports `patchapk` and `patchipa` workflows for that mode. [appsecsanta](https://appsecsanta.com/objection)

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

## Authentication & Session Handling

- * -> [Condition: Login or session flows identified] -> Action: Primary Probe: trace credential submission, refresh token issuance, device binding, local session persistence, logout invalidation, and MFA / biometric fallbacks.
  - * -> [Condition: Standard traffic review shows no obvious flaw] -> Action: Dead End Pivot 1: hook in-memory token creation, refresh scheduling, and cookie/header injection to recover tokens before pinning or encryption layers transform them.
  - * -> [Condition: Tokens seem device-bound] -> Action: Dead End Pivot 2: clone app state across emulator/device pairs, alter device identifiers, and replay refresh flows to detect weak binding.
  - * -> [Condition: Auth UX hides alternate paths] -> Action: Dead End Pivot 3: trigger deep links, password reset, account recovery, guest flows, and offline states to discover desynchronized auth checks.
  - * -> [Condition: Token or state bug found] -> Action: Data Chaining: replay against high-value API routes, combine with IDOR candidates, and test whether session upgrade or cross-user access leads to account takeover.
  - * -> [Condition: Local bypass exists only in-app] -> Action: Remote-vs-local divergence: determine whether bypass merely reveals local UI or whether backend trusts the manipulated client state.
- * -> [Condition: Biometrics wrap tokens locally] -> Action: verify whether a successful biometric unlock actually gates a server-side operation or only unlocks already-issued local credentials.

Simple inline one-liner:  
`grep -RniE "Bearer |refresh|access_token|session|biometric|deviceId" /mobile/<target>/apk/jadx /mobile/<target>/ipa/unzip`

## API & Backend Abuse from Mobile Context

- * -> [Condition: Endpoint inventory exists] -> Action: Primary Probe: build a mobile-specific API map from intercepted traffic, hardcoded URLs, GraphQL docs, protobuf schemas, and hidden feature flags.
  - * -> [Condition: Straight request tampering shows no issue] -> Action: Dead End Pivot 1: test mobile-only headers, version gates, locale/device claims, and hidden parameters lifted from static analysis.
  - * -> [Condition: Authz looks consistent on obvious routes] -> Action: Dead End Pivot 2: pivot to secondary object types such as invoices, tickets, media, drafts, or notification settings where mobile backends often lag web controls.
  - * -> [Condition: REST looks hardened] -> Action: Dead End Pivot 3: probe batch APIs, GraphQL introspection remnants, websocket channels, file uploads, and pre-signed URL issuance flows.
  - * -> [Condition: Secret or mobile key was found statically] -> Action: Data Chaining: use that key to emulate the app, authenticate hidden endpoints, enumerate objects, then combine any IDOR with session/token weakness for takeover or horizontal/vertical access.
  - * -> [Condition: Server trusts client-calculated values] -> Action: test discounts, reward balances, KYC states, or entitlement flags modified from rooted runtime hooks.
- * -> [Condition: Mobile transport is different from browser transport] -> Action: keep separate replay collections for app-only headers, protobuf bodies, certificate-bound flows, and feature-flag endpoints.

Script Definition Block — Mobile Endpoint Correlator  
- Input Data: Burp history, decompiled base URLs, Retrofit/Alamofire models, GraphQL/protobuf artifacts.
- Core Processing Logic:
  - Normalize routes and group by auth context.
  - Match parameters to UI screens and storage keys.
  - Flag endpoints with user-controlled IDs, role claims, or hidden booleans.
- Dependencies: Burp export, `jq`, protobuf/GraphQL schema tools, manual notes.
- Expected Output Format: CSV with `method,path,auth_type,source_screen,user_object_id,interesting_param,next_test`.

## Biometric & Passcode Bypass

- * -> [Condition: App exposes biometric unlock or re-auth] -> Action: Primary Probe: identify whether biometrics protect local secret release, server re-auth, or only UI gating.
  - * -> [Condition: Biometric success only flips a local boolean] -> Action: hook the success callback / prompt result and force success without touching the sensor.
  - * -> [Condition: No direct local gate found] -> Action: Dead End Pivot 1: hook keystore/keychain access right after biometric success and compare behavior when the prompt is bypassed.
  - * -> [Condition: App uses custom passcode layer] -> Action: Dead End Pivot 2: patch comparison logic, retry counters, and lockout timers in smali or via runtime return-value hooks.
  - * -> [Condition: iOS secure enclave / LAContext path is used] -> Action: Dead End Pivot 3: hook `evaluatePolicy`/completion paths or downstream secret fetchers rather than the prompt UI.
  - * -> [Condition: Secret release occurs after forced success] -> Action: Data Chaining: extract session tokens, offline keys, or account-switch material; then validate whether backend accepts actions without true recent authentication.
  - * -> [Condition: Exploit works only on modified device] -> Action: classify as local post-compromise unless the app reuses long-lived tokens that can be exfiltrated and replayed remotely.

Simple inline one-liner:  
`grep -RniE "BiometricPrompt|FingerprintManager|LAContext|evaluatePolicy|setUserAuthenticationRequired" /mobile/<target>`

## iOS-Specific Weaknesses

- * -> [Condition: IPA or live bundle available] -> Action: Primary Probe: inspect `Info.plist`, URL schemes, associated domains, pasteboard use, storyboard/xib strings, keychain groups, app groups, and jailbreak-detection routines.
  - * -> [Condition: URL scheme handlers exist] -> Action: test every scheme/action pair with hostile parameters; `canOpenURL` is the API apps use to determine whether an installed app can handle a URL scheme. [developer.apple](https://developer.apple.com/documentation/uikit/uiapplication/canopenurl(_:)?language=objc)
  - * -> [Condition: No scheme abuse appears] -> Action: Dead End Pivot 1: inspect pasteboard reads/writes, universal links, and document interaction controllers for data leakage or phishing handoff; `UIPasteboard` is expressly designed for data sharing across app boundaries. [developer.apple](https://developer.apple.com/documentation/uikit/uipasteboard/)
  - * -> [Condition: Filesystem review looks clean] -> Action: Dead End Pivot 2: inspect storyboards, localized strings, crash logs, and cached web assets for hidden endpoints, feature names, or credentials.
  - * -> [Condition: Jailbreak detection blocks coverage] -> Action: Dead End Pivot 3: method-swizzle or Frida-hook file checks, URL-scheme checks for `cydia://`, write probes to restricted paths, and loaded-library inspections; those patterns are common jailbreak detection approaches. [kayssel](https://www.kayssel.com/newsletter/issue-29/)
  - * -> [Condition: Keychain item, URL action, or pasteboard artifact found] -> Action: Data Chaining: replay the token, invoke the cross-app workflow, or poison shared clipboard data to drive account switching, credential leakage, or hidden state transitions.
  - * -> [Condition: Filza/SSH access available] -> Action: pull `Library/Preferences/*.plist`, app-group containers, `Caches`, and crash logs, then compare them against live runtime hooks.
- * -> [Condition: Jailbroken device setup] -> Action: Frida deployment commonly starts from the Frida package path described for iOS device instrumentation. [frida](https://frida.re/docs/ios/)

Simple inline one-liner:  
`plutil -p Info.plist | egrep "CFBundleURLTypes|LSApplicationQueriesSchemes|NSAppTransportSecurity|com.apple.security"`

## Android-Specific Weaknesses

- * -> [Condition: Decompiled manifest available] -> Action: Primary Probe: enumerate exported activities, services, receivers, and providers; then test each externally reachable component with hostile inputs because `android:exported` governs whether other apps can launch them. [developer.android](https://developer.android.com/privacy-and-security/risks/android-exported)
  - * -> [Condition: Exported activity/service found] -> Action: `adb shell am start -n <package>/<activity>` and `adb shell am startservice -n <package>/<service> --es cmd test`
  - * -> [Condition: No exploit via basic launches] -> Action: Dead End Pivot 1: abuse broadcast receivers with crafted actions/extras, sticky broadcasts, and race conditions around boot/network/account events.
  - * -> [Condition: Receivers/services are protected] -> Action: Dead End Pivot 2: target content providers with traversal, over-broad query/update/delete, or file-backed URIs; `adb shell content query` gives a direct CLI path to provider testing. [stackoverflow](https://stackoverflow.com/questions/27988069/query-android-content-provider-from-command-line-adb-shell)
  - * -> [Condition: Provider exposure looks minimal] -> Action: Dead End Pivot 3: test implicit intents, task hijacking edges, WebView/file-provider joins, and Parcel deserialization mismatch in exported IPC surfaces.
  - * -> [Condition: Component accepts foreign input] -> Action: Data Chaining: turn the component into a stepping stone for arbitrary file read, account context switch, hidden admin screen access, or backend requests executed under victim state.
  - * -> [Condition: Provider serves filesystem paths] -> Action: probe `..`, encoded traversal, alternate document IDs, and MIME confusion to reach arbitrary files.
  - * -> [Condition: Backup or trust configuration is suspicious] -> Action: validate `allowBackup`, extraction rules, cleartext allowances, and custom trust config; Android network security config and Auto Backup both materially affect exploitability. [developer.android](https://developer.android.com/privacy-and-security/security-config)
- * -> [Condition: App targets modern Android] -> Action: remember that deep links, exported components, and trust behavior may shift with target SDK and verified-link configuration, so always test on both declared target behavior and the actual device OS. [developer.android](https://developer.android.com/training/app-links)

Simple inline one-liners:  
`adb shell content query --uri content://<authority>/`  
`adb shell am broadcast -a <package>.ACTION_SYNC --es path "../../../../data/data/<package>/shared_prefs/auth.xml"`