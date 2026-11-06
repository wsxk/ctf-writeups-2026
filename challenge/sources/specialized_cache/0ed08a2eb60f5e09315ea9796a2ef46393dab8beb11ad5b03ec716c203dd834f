#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 solver.raw" >&2
    exit 1
fi

cd /challenge

payload="$1"
flag="./flag.txt"
if [[ ! -s "$payload" ]]; then
    echo "[-] missing or empty solver payload: $payload" >&2
    exit 1
fi
if [[ ! -s "$flag" ]]; then
    echo "[-] missing or empty flag file: $flag" >&2
    exit 1
fi

exec ./qemu-system-aarch64 \
    -machine virt,mte=on,gic-version=3 \
    -accel tcg,thread=multi \
    -cpu max,pauth-qarma3=on \
    -smp 3 \
    -m 1024M \
    -kernel ./Image \
    -initrd ./initramfs.cpio.gz \
    -append "console=ttyAMA0 loglevel=7 ignore_loglevel oops=panic panic_on_warn=1 panic=-1 page_alloc.shuffle=1 rdinit=/init ctf.root_shell=0 ctf.shell_login=0" \
    -nodefaults \
    -no-reboot \
    -display none \
    -monitor none \
    -chardev stdio,id=serial0,signal=off,mux=off \
    -serial chardev:serial0 \
    -drive if=none,id=solver,format=raw,file="$payload",readonly=on,cache=unsafe \
    -device virtio-blk-device,drive=solver,serial=sekai-solver \
    -drive if=none,id=flag,format=raw,file="$flag",readonly=on,cache=unsafe \
    -device virtio-blk-device,drive=flag,serial=sekai-flag
