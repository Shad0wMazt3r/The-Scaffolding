## iOS-Specific Weaknesses

- * -> [Condition: IPA or live bundle available] -> Action: Primary Probe: inspect `Info.plist`, URL schemes, associated domains, pasteboard use, storyboard/xib strings, keychain groups, app groups, and jailbreak-detection routines.
  - * -> [Condition: URL scheme handlers exist] -> Action: test every scheme/action pair with hostile parameters; `canOpenURL` is the API apps use to determine whether an installed app can handle a URL scheme. [developer.apple](https://developer.apple.com/documentation/uikit/uiapplication/canopenurl(_:)?language=objc)
  - * -> [Condition: No scheme abuse appears] -> Action: Dead End Pivot 1: inspect pasteboard reads/writes, universal links, and document interaction controllers for data leakage or phishing handoff; `UIPasteboard` is expressly designed for data sharing across app boundaries. [developer.apple](https://developer.apple.com/documentation/uikit/uipasteboard/)
  - * -> [Condition: Filesystem review looks clean] -> Action: Dead End Pivot 2: inspect storyboards, localized strings, crash logs, and cached web assets for hidden endpoints, feature names, or credentials.
  - * -> [Condition: Jailbreak detection blocks coverage] -> Action: Dead End Pivot 3: method-swizzle or Frida-hook file checks, URL-scheme checks for `cydia://`, write probes to restricted paths, and loaded-library inspections; those patterns are common jailbreak detection approaches.
  - * -> [Condition: Keychain item, URL action, or pasteboard artifact found] -> Action: Data Chaining: replay the token, invoke the cross-app workflow, or poison shared clipboard data to drive account switching, credential leakage, or hidden state transitions.
  - * -> [Condition: Filza/SSH access available] -> Action: pull `Library/Preferences/*.plist`, app-group containers, `Caches`, and crash logs, then compare them against live runtime hooks.
- * -> [Condition: Jailbroken device setup] -> Action: Frida deployment commonly starts from the Frida package path described for iOS device instrumentation.

Simple inline one-liner:
`plutil -p Info.plist | egrep "CFBundleURLTypes|LSApplicationQueriesSchemes|NSAppTransportSecurity|com.apple.security"`

## Android-Specific Weaknesses
