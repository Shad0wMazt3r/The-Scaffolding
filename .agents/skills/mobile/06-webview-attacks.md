## WebView Attacks

- * -> [Condition: App embeds WebView] -> Action: Primary Probe: identify load sources, JavaScript settings, bridge exposure, file access, mixed content, cookie scope, and navigation handling.
  - * -> [Condition: URL origin is attacker-influenced] -> Action: test open redirects, deep-link-fed loads, notification-fed URLs, and universal XSS paths.
  - * -> [Condition: No direct load control] -> Action: Dead End Pivot 1: inspect `addJavascriptInterface`, custom URL handlers, and postMessage-like bridges for methods reachable from untrusted content.
  - * -> [Condition: Bridge is hidden by obfuscation] -> Action: Dead End Pivot 2: enumerate bridge objects and WebView methods at runtime with Frida or Objection, then hook `loadUrl`, `evaluateJavascript`, and `shouldOverrideUrlLoading`.
  - * -> [Condition: File access path is unclear] -> Action: Dead End Pivot 3: test `file://`, `content://`, local HTML assets, and exported content providers feeding WebView.
  - * -> [Condition: JS bridge or URL load is controllable] -> Action: Data Chaining: escalate from arbitrary URL load to cookie theft, privileged native method invocation, token exfiltration, or backend action execution under the app session.
  - * -> [Condition: Traffic differs from native API traffic] -> Action: Split testing between WebView transport and native HTTP client because pinning, cookies, and header logic often diverge.
- * -> [Condition: WebView configuration review] -> Action: Treat JavaScript enablement and embedded web-app behavior as a separate trust boundary because Android WebView is an in-app browser surface with its own configuration and security implications. [mas.owasp](https://mas.owasp.org/MASTG-KNOW-0018/)

