#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 challenge.js.raw" >&2
    exit 1
fi

cd /challenge

payload="$1"
if [[ ! -s "$payload" ]]; then
    echo "[-] missing or empty payload file: $payload" >&2
    exit 1
fi

exec ./qemu-system-x86_64 \
    -L ./pc-bios \
    -kernel ./bzImage \
    -cpu max,+smap,+smep,+fsgsbase \
    -smp 1 \
    -m 256M \
    -initrd ./initramfs.cpio \
    -append "console=ttyS0 quiet loglevel=3 oops=panic panic_on_warn=1 panic=-1 page_alloc.shuffle=1 rdinit=/init" \
    -no-reboot \
    -display none \
    -monitor none \
    -chardev stdio,id=serial0,signal=off,mux=off \
    -serial chardev:serial0 \
    -audiodev none,id=snd0,in.mixing-engine=off,out.mixing-engine=off,in.fixed-settings=off,out.fixed-settings=off,timer-period=10000 \
    -device virtio-sound-pci,audiodev=snd0,streams=4,ioeventfd=off \
    -drive format=raw,file="$payload",if=virtio,readonly=on,cache=unsafe
