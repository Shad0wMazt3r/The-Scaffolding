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

