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
