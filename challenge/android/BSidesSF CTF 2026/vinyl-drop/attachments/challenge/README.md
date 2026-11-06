### Setup Instructions

## Console 
* Requires Firebase Project
* Turn on Firebase Auth with Email/password 
* Turn on Firebase Function 
* Configure the project to have an Android App, add the SHA 256 fingerprint `2c:8e:76:12:2c:c3:c3:da:77:2f:39:39:38:2d:dc:5f:20:44:d2:2d:33:6a:cf:89:9a:12:94:e1:92:c0:9a:1a`
* Turn on Firebase AppCheck
** It's ok if it is Play Integrity in the console, since it will use custom AppCheck
** Turn off enforcement for Auth, since the custom AppCheck implementation uses the AppID and the UserId 

## Function
* Change the AppID in the firebase function index.js:line8 - `const ALLOWED_APP_ID = "1:516080934905:android:ebc650b452408f9aa42728";`
* To deploy firebase function - firebase deploy --only functions --project $Project_name --force 

## GCP Console
* `$some_number-compute@developer.gserviceaccount.com` make sure this has the following roles, this is the default service account used by the Firebase Function - `roles/iam.serviceAccountTokenCreator`, `roles/firebaseappcheck.admin`.

## New signed APK
* Add the google-services.json to the app 
* Regenerate a new signed APK using the same key
* Update distfiles 