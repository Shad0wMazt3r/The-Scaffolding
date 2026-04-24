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
- On Android, keep `adb` ready for both Activity Manager and content-provider entry points because `adb shell am` and `adb shell content` expose those attack surfaces directly from shell.
- For TLS interception, assume Android trusts system CAs by default, and note that apps targeting API 23 or lower also trust user-added CAs by default unless app configuration changes that trust behavior. [developer.android](https://developer.android.com/privacy-and-security/security-config)
- For Android backup review, check whether the target targets and runs on Android 6.0+ because Auto Backup applies there and can expose app data selection rules. [developer.android](https://developer.android.com/identity/data/autobackup)
- For iOS, treat Keychain, app container files, URL-scheme handlers, and pasteboard as first-class data sources because Keychain stores small secrets in an encrypted database, `canOpenURL` reveals whether a scheme handler exists, and `UIPasteboard` is a cross-app data-sharing primitive. [developer.apple](https://developer.apple.com/documentation/security/keychain-services)
- On jailbroken iOS, deploy Frida through the Frida repository package path, and on non-jailbroken devices prefer `objection patchipa` / `patchapk` with Frida Gadget when the assessment allows repackaging.

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

