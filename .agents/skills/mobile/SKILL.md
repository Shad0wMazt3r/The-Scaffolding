---
name: mobile
description: Drive mobile app testing from static extraction through TLS bypass, storage abuse, intent/WebView abuse, runtime hooks, and backend pivoting.
dependencies: [agent-setup, agent-calibration]
files:
  - 01-baseline-and-setup.md
  - 02-static-analysis-and-reverse-engineering.md
  - 03-certificate-pinning-and-ssl-bypass.md
  - 04-insecure-data-storage.md
  - 05-deeplink-and-intent-abuse.md
  - 06-webview-attacks.md
  - 07-runtime-manipulation-and-hooking.md
  - 08-authentication-and-session-handling.md
  - 09-api-and-backend-abuse.md
  - 10-biometrics-and-passcode-bypass.md
  - 11-ios-specific-weaknesses.md
  - 12-android-specific-weaknesses.md
---

Load files sequentially on activation: see files list above.
Only load the next file when the current file's steps are complete or explicitly requested. Do not preload all files at once.



