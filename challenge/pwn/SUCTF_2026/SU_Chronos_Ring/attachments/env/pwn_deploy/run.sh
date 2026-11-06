#!/bin/bash
set -e

ROOTFS_DIR="rootfs"
INITRD_NAME="initramfs.cpio.gz"
KERNEL_IMAGE="./bzImage"
FLAG_FILE="flag"
echo "[*] === Chronos Ring Docker Environment Runner ==="

if [ ! -f "$INITRD_NAME" ]; then
    echo "[-] Error: $INITRD_NAME not found! Need base image to decompress."
    exit 1
fi
echo "[+] Decompressing $INITRD_NAME into $ROOTFS_DIR..."
rm -rf "$ROOTFS_DIR"
mkdir -p "$ROOTFS_DIR"
cd "$ROOTFS_DIR"
zcat "../$INITRD_NAME" | cpio -idmv --quiet
cd ..

if [ -f "$FLAG_FILE" ]; then
    echo "[+] Injecting $FLAG_FILE..."
    cp "$FLAG_FILE" "$ROOTFS_DIR/flag"
fi


cd "$ROOTFS_DIR"
find . -print0 | cpio --null -ov --format=newc --quiet | gzip -9 > "../$INITRD_NAME"
cd ..
exec qemu-system-x86_64 \
    -m 256M \
    -nographic \
    -enable-kvm \
    -smp 2 \
    -cpu max \
    -kernel "$KERNEL_IMAGE" \
    -initrd "./$INITRD_NAME" \
    -monitor /dev/null \
    -append "console=ttyS0 kaslr no5lvl pti=on oops=panic panic=1 quiet" \
    -no-reboot