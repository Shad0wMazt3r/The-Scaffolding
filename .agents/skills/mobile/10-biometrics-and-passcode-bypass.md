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

