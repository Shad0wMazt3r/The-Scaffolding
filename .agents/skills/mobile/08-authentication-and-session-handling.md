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

