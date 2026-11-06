# TLDR;
To solve run, `frida -U -f com.bsidessf.vinyldrop -l frida-validate.js` to test the apk. 
Or create a QR code that has <uid>+100+<unix_timestamp_now>, scan it and get the flag. 

# Overview
Using the app, helps you understand the App's functionality. You can register a new user and login, the authentication is implemented using Firebase Auth (email/password). Once you log in you see a receipt with a sample QR code. If you provide a QR code that meets the following conditions, you will get the flag - 
* Part 1 - Firebase User ID 
* Part 2 - Amount >= $100 
* Part 3 - Unix Timestamp within last 30 days 

# Analyzing the app 
Gemini or ChatGPT can give you an idea of the App's working, specifically the use of FirebaseAuth, Firebase Functions and Firebase AppCheck. Sample output from Codex, 

```
vinyl-drop.apk is a Firebase‑backed Android app (“Vinyl Drop”) that gates a reward behind a QR‑code scan. It’s basically: login/register → scan a QR code → send the payload to a Firebase Cloud Function →
  show the reward (flag) or an error.

  Key behaviors I found from decompiling the app classes:

  - Launch flow: MainActivity shows email/password login (Firebase Auth). On success it goes to WelcomeActivity. There’s a register link that opens RegisterActivity.
  - Registration: RegisterActivity creates a Firebase Auth account with email/password (min 6 chars, confirm password must match).
  - QR scanning: WelcomeActivity launches BarcodeScanActivity. That activity uses the camera plus ML Kit barcode scanning (QR format) and falls back to ZXing decoding if ML Kit doesn’t return a value.
  - Validation: The scanned string is sent to Firebase Functions via validateScanPayload. The response is expected to contain success, reward, or error/reason.
  - Reward display: RewardActivity shows either “Congrats! The flag is,” + the reward text, or “Scan Rejected” + an error reason.
  - App Check: The app installs a custom Firebase App Check provider. It mints App Check tokens by POSTing to https://us-central1-<project_id>.cloudfunctions.net/mintAppCheckToken using the signed‑in user’s
    Firebase Auth ID token as a Bearer token.
  - Firebase config in resources: project id vinyldrop-corgi, storage bucket vinyldrop-corgi.firebasestorage.app, plus the app’s Google API key/app id.

  Permissions are limited to camera + network (INTERNET, ACCESS_NETWORK_STATE, WAKE_LOCK, FCM receive), and there are no custom background services or receivers beyond Firebase/ML Kit.

  If you want, I can dig deeper into the Cloud Functions protocol (e.g., reproduce the validateScanPayload call) or extract the exact request/response format used by the app.
  ```

# Sending requests to Firebase Function 

From here, you can send requests to figure out the right format for the QR code. If you send a request to the Firebase function without App ID will be rejected - `{ success: False, error: True, reason: "pp ID not allowed." }`. You can find the App ID in `google-services.json` - `"mobilesdk_app_id": "1:516080934905:android:ebc650b452408f9aa42728"`. 

A Frida script that runs after creating an account and logging in would allow you to modify the string sent to the Firebase function for validation without being bogged down by the AppCheck logic. 

The errors returned by the server should be helpful in figuring out the format - 
* "Expected three '+'-separated parts."
* "First part: Should be a UID for the current user."
* "Second part: Must be a number.", "Second part: Purchase must be 100 or above."
* "Third part: Must be a unix timestamp.", "Third part: Purchase must be within the last 30 days."

Which brings you to - <uid>+100+<unix_timestamp_now>. 

# Frida setup 
To set-up Frida on your laptop,

```
pip3 install frida-tools
```

To figure out the architecture of the emulator image,

```
adb shell getprop ro.product.cpu.abi
```

Then download the corresponding frida-server from https://github.com/frida/frida/releases. Then copy the Frida server to the emulator and start it.

```
adb root
adb push <path_to_frida_server> /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server
adb shell /data/local/tmp/frida-server &
frida -U -f com.bsidessf.vinyldrop -l frida-validate.js
```

