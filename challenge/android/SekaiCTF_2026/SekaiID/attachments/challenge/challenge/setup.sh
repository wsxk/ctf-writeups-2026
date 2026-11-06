#!/usr/bin/env bash
#
# Challenge setup — runs as root with /system writable, adb pre-targeted.
# See ../start.sh for the surrounding flow.
#
set -euo pipefail

CHALLENGE_DIR="${CHALLENGE_DIR:-/opt/challenge}"
log() { printf '[setup] %s\n' "$*"; }

# ---- Install the VERIFIER as a SYSTEM app -----------------------------------
# The flag is readable by the verifier's uid. If the verifier were a normal
# (/data/app) install, a player could `pm uninstall com.sekai.verifier` to FREE
# that uid, then install their own app to RECLAIM the same uid and read the
# flag directly (no exploit needed).
#
# Placing it under /system/app pins the package and its uid: a system app can't
# be fully uninstalled (only its updates removed) nor replaced by a
# differently-signed apk, so the uid that owns the flag is never released.
# PackageManager registers /system/app on the next boot (the lockdown reboot
# start.sh performs right after this script), and the uid recorded now is
# preserved across that reboot.
log "installing com.sekai.verifier as a system app (pins its uid)"
adb shell 'mkdir -p /system/app/SekaiVerifier && chmod 755 /system/app/SekaiVerifier'
adb push "${CHALLENGE_DIR}/Verifier.apk" /system/app/SekaiVerifier/SekaiVerifier.apk
adb shell 'chmod 644 /system/app/SekaiVerifier/SekaiVerifier.apk'
# Install now too, so it gets a uid immediately for the chown below. After the
# lockdown reboot the /system/app copy makes it a non-removable system package
# while keeping this same uid.
adb install -r -g "${CHALLENGE_DIR}/Verifier.apk"

# ---- Install the other app normally -----------------------------------------
log "installing com.sekai.id"
adb install -r -g "${CHALLENGE_DIR}/SekaiID.apk"

# ---- Seed the flag, owned by the verifier uid -------------------------------
VERIFIER_UID=$(adb shell stat -c '%u' /data/data/com.sekai.verifier | tr -d '\r')
log "flag owner uid = ${VERIFIER_UID}"
adb push "${CHALLENGE_DIR}/flag.txt" /system/flag.txt
adb shell "chown ${VERIFIER_UID}:${VERIFIER_UID} /system/flag.txt"
adb shell "chmod 600 /system/flag.txt"

log "challenge setup complete"
