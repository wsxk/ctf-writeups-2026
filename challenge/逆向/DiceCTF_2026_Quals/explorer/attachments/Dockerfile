# syntax=docker/dockerfile:1.7

FROM busybox:musl AS busybox

FROM rust:1.90-bookworm AS toolchain

ARG LINUX_VERSION=6.19.6
ARG LLVM_VERSION=15

RUN apt-get update && apt-get install -y --no-install-recommends \
    bc \
    bison \
    build-essential \
    ca-certificates \
    clang-${LLVM_VERSION} \
    cpio \
    curl \
    file \
    flex \
    gawk \
    gzip \
    libelf-dev \
    libssl-dev \
    lld-${LLVM_VERSION} \
    llvm-${LLVM_VERSION} \
    libclang-${LLVM_VERSION}-dev \
    pahole \
    pkg-config \
    python3 \
    rsync \
    wget \
    xz-utils \
    musl-tools \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/clang clang /usr/lib/llvm-${LLVM_VERSION}/bin/clang 100 \
    && update-alternatives --install /usr/bin/clang++ clang++ /usr/lib/llvm-${LLVM_VERSION}/bin/clang++ 100 \
    && update-alternatives --install /usr/bin/ld.lld ld.lld /usr/lib/llvm-${LLVM_VERSION}/bin/ld.lld 100 \
    && update-alternatives --install /usr/bin/llvm-ar llvm-ar /usr/lib/llvm-${LLVM_VERSION}/bin/llvm-ar 100 \
    && update-alternatives --install /usr/bin/llvm-nm llvm-nm /usr/lib/llvm-${LLVM_VERSION}/bin/llvm-nm 100 \
    && update-alternatives --install /usr/bin/llvm-objcopy llvm-objcopy /usr/lib/llvm-${LLVM_VERSION}/bin/llvm-objcopy 100 \
    && update-alternatives --install /usr/bin/llvm-objdump llvm-objdump /usr/lib/llvm-${LLVM_VERSION}/bin/llvm-objdump 100 \
    && update-alternatives --install /usr/bin/llvm-readelf llvm-readelf /usr/lib/llvm-${LLVM_VERSION}/bin/llvm-readelf 100 \
    && update-alternatives --install /usr/bin/llvm-strip llvm-strip /usr/lib/llvm-${LLVM_VERSION}/bin/llvm-strip 100

FROM toolchain AS kernel-build

ARG LINUX_VERSION=6.19.6

WORKDIR /work
RUN wget -q https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${LINUX_VERSION}.tar.xz \
    && tar -xf linux-${LINUX_VERSION}.tar.xz \
    && mv linux-${LINUX_VERSION} linux
RUN cargo install --locked bindgen-cli
RUN rustup component add rust-src rustfmt
WORKDIR /work/linux

COPY challenge.rs drivers/misc/challenge.rs
RUN echo 'obj-y\t\t\t+= challenge.o' >> drivers/misc/Makefile

# Disable big drivers for build times
RUN make LLVM=1 tinyconfig \
    && scripts/config \
        --enable MULTIUSER \
        --enable PRINTK \
        --enable RUST \
        --enable KALLSYMS \
        --enable BINFMT_ELF \
        --enable BINFMT_SCRIPT \
        --enable RD_GZIP \
        --enable PROC_FS \
        --enable SYSFS \
        --enable SHMEM \
        --enable TMPFS \
        --enable TMPFS_POSIX_ACL \
        --enable UNIX \
        --enable DEVPTS_FS \
        --enable UNIX98_PTYS \
        --enable DEVTMPFS \
        --enable DEVTMPFS_MOUNT \
        --enable BLK_DEV_INITRD \
        --enable SERIAL_8250 \
        --enable SERIAL_8250_CONSOLE \
        --enable HYPERVISOR_GUEST \
        --enable TTY \
        --enable 64BIT \
    && make LLVM=1 olddefconfig \
    && make LLVM=1 rustavailable \
    && make LLVM=1 -j$(nproc) bzImage

RUN mkdir -p /artifacts \
    && cp arch/x86/boot/bzImage /artifacts/bzImage \
    && cp System.map /artifacts/System.map \
    && cp .config /artifacts/kernel.config

FROM toolchain AS rootfs-build

ARG INCLUDE_SOLVER=0

WORKDIR /work

RUN mkdir -p /work/rootfs-build/bin /work/rootfs-build/dev /work/rootfs-build/proc /work/rootfs-build/sys /work/rootfs-build/tmp /work/rootfs-build/home/ctf /work/rootfs-build/etc

COPY rootfs /src/rootfs
COPY --from=busybox /bin/busybox /work/rootfs-build/bin/busybox

RUN cp -a /src/rootfs/. /work/rootfs-build/ \
    && chmod +x /work/rootfs-build/bin/busybox \
    && /work/rootfs-build/bin/busybox --install /work/rootfs-build/bin \
    && if [ "${INCLUDE_SOLVER}" = "1" ]; then musl-gcc -O2 -static -s -o /work/rootfs-build/user /src/rootfs/user.c; chmod +x /work/rootfs-build/user; fi \
    && rm -f /work/rootfs-build/user.c \
    && if [ ! -f /work/rootfs-build/etc/passwd ]; then printf 'root:x:0:0:root:/root:/bin/sh\nctf:x:1000:1000:ctf:/home/ctf:/bin/sh\n' > /work/rootfs-build/etc/passwd; fi \
    && if [ ! -f /work/rootfs-build/etc/group ]; then printf 'root:x:0:\nctf:x:1000:\n' > /work/rootfs-build/etc/group; fi \
    && chmod 0755 /work/rootfs-build/init

RUN mkdir -p /artifacts \
    && (cd /work/rootfs-build && find . -print0 | cpio --null -ov --format=newc 2>/dev/null | gzip -9 > /artifacts/initramfs.cpio.gz)

FROM scratch AS artifacts
COPY --from=kernel-build /artifacts/bzImage /bzImage
COPY --from=rootfs-build /artifacts/initramfs.cpio.gz /initramfs.cpio.gz

FROM debian:bookworm-slim AS jail-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    qemu-system-x86 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=artifacts /bzImage bzImage
COPY --from=artifacts /initramfs.cpio.gz initramfs.cpio.gz

RUN printf '%s\n' \
    '#!/bin/sh' \
    'exec /usr/bin/qemu-system-x86_64 \' \
    '  -m 512M -smp 1 -nographic -no-reboot -monitor /dev/null \' \
    '  -kernel /app/bzImage \' \
    '  -initrd /app/initramfs.cpio.gz \' \
    '  -append "console=ttyS0 loglevel=3 panic=-1 oops=panic init=/init"' \
    > run \
    && chmod +x run

FROM pwn.red/jail AS jail
COPY --from=jail-base / /srv
ENV JAIL_PORT=5000
ENV JAIL_PIDS=20
ENV JAIL_MEM=2G
ENV JAIL_TIME=120
