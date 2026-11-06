#!/usr/bin/env bash
#
# Emulator orchestration / entrypoint. This file is generic infrastructure —
# you should not need to edit it per challenge. Put challenge-specific
# provisioning in setup.sh (see CHALLENGE_SETUP below).
#
# Default flow (LOCKDOWN_ROOT=1): the device is a userdebug build, so we use
# FULL root to provision it, then permanently revoke root for players:
#   1. boot with -writable-system
#   2. adb root + make /system writable (adb remount; reboot as overlayfs needs)
#   3. run the challenge setup.sh (rooted, /system writable, adb pre-targeted)
#   4. lock down: delete the su binary AND set ro.debuggable=0 in build.prop
#   5. reboot -> adbd now refuses `adb root` and `adb shell su` is gone
#   6. bridge the localhost-only ADB port to 0.0.0.0 for remote players
#
# Set LOCKDOWN_ROOT=0 to instead keep root for setup and only `adb unroot`
# (NOT a hard boundary on userdebug — players could re-root).
#
set -euo pipefail

# ---- Configuration (override with -e at `docker run`) -----------------------
AVD_NAME="${AVD_NAME:-ctf}"

# The emulator binds its console/adb ports to 127.0.0.1 only. We keep those
# internal and use socat to publish the adb transport on a separate, public
# port (avoids the 0.0.0.0 vs 127.0.0.1 bind conflict on the same port).
EMU_CONSOLE_PORT="${EMU_CONSOLE_PORT:-5556}"   # must be even
EMU_ADB_PORT="${EMU_ADB_PORT:-5557}"           # = console + 1
PUBLIC_ADB_PORT="${PUBLIC_ADB_PORT:-5555}"     # what players connect to

# 1 = permanently revoke root after provisioning (delete su + ro.debuggable=0).
LOCKDOWN_ROOT="${LOCKDOWN_ROOT:-1}"

# Challenge-specific provisioning, run inside the container during the rooted +
# writable-/system window. Lives in the challenge dir (see challenge/setup.sh).
CHALLENGE_DIR="${CHALLENGE_DIR:-/opt/challenge}"
CHALLENGE_SETUP="${CHALLENGE_SETUP:-${CHALLENGE_DIR}/setup.sh}"

EMULATOR_EXTRA_ARGS="${EMULATOR_EXTRA_ARGS:-}"

log() { printf '\033[1;32m[*]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[!]\033[0m %s\n' "$*" >&2; }

# Print the uid adbd is currently running as (0=root, 2000=shell).
adbd_uid() { adb -s "${EMU_SERIAL}" shell id -u 2>/dev/null | tr -d '\r'; }

# Block until adbd's shell is responsive again (adb root/unroot restart adbd).
wait_for_adb() {
    adb -s "${EMU_SERIAL}" wait-for-device
    local tries=60
    until adb -s "${EMU_SERIAL}" shell true >/dev/null 2>&1; do
        ((tries--)) || { err "adbd did not become ready in time"; return 1; }
        sleep 1
    done
}

# Block until the guest has fully booted (used after the initial boot and each
# adb reboot). The qemu process (EMU_PID) survives guest reboots.
wait_for_boot() {
    local label="${1:-boot}"
    sleep 3                                   # let an in-flight reboot drop the link
    adb -s "${EMU_SERIAL}" wait-for-device
    local tries=180
    until [[ "$(adb -s "${EMU_SERIAL}" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; do
        if ! kill -0 "${EMU_PID}" 2>/dev/null; then
            err "Emulator process died during ${label}. Check KVM / system image."
            exit 1
        fi
        ((tries--)) || { err "Timed out waiting for ${label}."; exit 1; }
        sleep 2
    done
}

# Returns 0 once /system can be written to (as root).
system_writable() {
    adb -s "${EMU_SERIAL}" shell 'touch /system/.wtest 2>/dev/null && rm -f /system/.wtest' >/dev/null 2>&1
}

# Disable verity + enable overlayfs so /system is writable. The first remount
# only stages the change; a reboot + second remount actually mounts it RW.
make_system_writable() {
    adb -s "${EMU_SERIAL}" root >/dev/null; wait_for_adb
    [[ "$(adbd_uid)" == "0" ]] || { err "Could not obtain root (user build?)."; return 1; }
    adb -s "${EMU_SERIAL}" remount >/dev/null 2>&1 || true
    if ! system_writable; then
        log "Rebooting to apply verity/overlay change..."
        adb -s "${EMU_SERIAL}" reboot
        wait_for_boot "post-remount reboot"
        adb -s "${EMU_SERIAL}" root >/dev/null; wait_for_adb
        adb -s "${EMU_SERIAL}" remount >/dev/null 2>&1 || true
    fi
    system_writable
}

# Hand control to the challenge's setup.sh. It runs in the container with adb
# already targeting the emulator (ANDROID_SERIAL), as root, with /system
# writable. CHALLENGE_DIR points at the bundled assets (apks, flag, etc.).
provision() {
    if [[ -f "${CHALLENGE_SETUP}" ]]; then
        log "Running challenge setup '${CHALLENGE_SETUP}' (uid $(adbd_uid), /system writable)..."
        ANDROID_SERIAL="${EMU_SERIAL}" CHALLENGE_DIR="${CHALLENGE_DIR}" \
            bash "${CHALLENGE_SETUP}" || err "challenge setup exited non-zero"
    else
        log "No challenge setup script at ${CHALLENGE_SETUP} (skipping)."
    fi
}

# Permanently revoke root: remove every su binary and make the build
# non-debuggable so adbd refuses `adb root`. Requires writable /system.
lockdown_root() {
    log "Removing su binaries..."
    adb -s "${EMU_SERIAL}" shell 'for p in /system/bin/su /system/xbin/su /sbin/su /vendor/bin/su /vendor/xbin/su; do rm -f "$p" 2>/dev/null; done; true'
    log "Setting ro.debuggable=0 in /system/build.prop..."
    adb -s "${EMU_SERIAL}" shell "sed -i 's/^ro.debuggable=1/ro.debuggable=0/' /system/build.prop"
    log "Rebooting into the locked-down (root-rejecting) state..."
    adb -s "${EMU_SERIAL}" reboot
    wait_for_boot "lockdown reboot"
}

cleanup() {
    log "Shutting down..."
    [[ -n "${SOCAT_PID:-}" ]] && kill "${SOCAT_PID}" 2>/dev/null || true
    [[ -n "${EMU_PID:-}"   ]] && kill "${EMU_PID}"   2>/dev/null || true
    adb kill-server 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ---- KVM sanity check --------------------------------------------------------
if [[ ! -e /dev/kvm ]]; then
    err "/dev/kvm not found. The x86_64 emulator needs hardware acceleration."
    err "Run the container with:  --device /dev/kvm   (host must support KVM)."
    err "Continuing anyway with software rendering (this will be very slow)..."
fi

# ---- Start ADB + emulator ----------------------------------------------------
log "Starting ADB server..."
adb start-server

emu_args=(-avd "${AVD_NAME}"
          -ports "${EMU_CONSOLE_PORT},${EMU_ADB_PORT}"
          -no-window -no-audio -no-boot-anim -no-snapshot
          -gpu swiftshader_indirect -wipe-data)
# Lockdown edits /system, which requires the writable-system overlay.
[[ "${LOCKDOWN_ROOT}" == "1" ]] && emu_args+=(-writable-system)
# Append any user-supplied flags (intentional word-splitting).
read -ra _extra <<< "${EMULATOR_EXTRA_ARGS}"
(( ${#_extra[@]} )) && emu_args+=("${_extra[@]}")

EMU_SERIAL="emulator-${EMU_CONSOLE_PORT}"

log "Booting AVD '${AVD_NAME}' on console ${EMU_CONSOLE_PORT} / adb ${EMU_ADB_PORT}..."
emulator "${emu_args[@]}" &
EMU_PID=$!

# ---- Boot --------------------------------------------------------------------
log "Waiting for device + full boot..."
wait_for_boot "initial boot"
adb -s "${EMU_SERIAL}" shell input keyevent 82 >/dev/null 2>&1 || true   # dismiss lockscreen
log "Device booted: ${EMU_SERIAL}"

# ---- Provision (+ optional permanent root lockdown) -------------------------
if [[ "${LOCKDOWN_ROOT}" == "1" ]]; then
    log "Making /system writable for provisioning + lockdown..."
    if make_system_writable; then
        log "/system is writable."
        provision
        lockdown_root
        dbg="$(adb -s "${EMU_SERIAL}" shell getprop ro.debuggable | tr -d '\r')"
        root_resp="$(adb -s "${EMU_SERIAL}" root 2>&1 | tr -d '\r')"
        log "Lockdown result: ro.debuggable=${dbg}, served uid=$(adbd_uid), 'adb root' => ${root_resp}"
        if [[ "${dbg}" == "0" && "$(adbd_uid)" == "2000" ]]; then
            log "Root permanently revoked: 'adb root' and 'adb shell su' both fail."
        else
            err "WARNING: lockdown verification failed (debuggable=${dbg})."
        fi
    else
        err "Could not make /system writable; skipping lockdown. Provisioning without it."
        provision
    fi
else
    # Soft mode: root for setup, then drop to non-root (re-rootable on userdebug).
    log "LOCKDOWN_ROOT=0: provisioning as root, then adb unroot (not a hard boundary)."
    adb -s "${EMU_SERIAL}" root >/dev/null && wait_for_adb || err "adb root failed"
    provision
    adb -s "${EMU_SERIAL}" unroot >/dev/null && wait_for_adb || err "adb unroot failed"
    log "Served ADB session uid: $(adbd_uid) (2000=shell)."
fi

# ---- Publish ADB to the network ---------------------------------------------
log "Bridging 0.0.0.0:${PUBLIC_ADB_PORT} -> 127.0.0.1:${EMU_ADB_PORT}"
socat "TCP-LISTEN:${PUBLIC_ADB_PORT},reuseaddr,fork" "TCP:127.0.0.1:${EMU_ADB_PORT}" &
SOCAT_PID=$!

printf '\n\033[1;36m============================================================\033[0m\n'
printf ' Android CTF device is ready.\n'
printf ' Connect:  adb connect <host>:%s  &&  adb shell\n' "${PUBLIC_ADB_PORT}"
printf '\033[1;36m============================================================\033[0m\n\n'

# ---- Keep the container alive; exit if either child dies --------------------
wait -n "${EMU_PID}" "${SOCAT_PID}"
