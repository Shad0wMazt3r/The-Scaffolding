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

