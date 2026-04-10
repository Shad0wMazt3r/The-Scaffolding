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

