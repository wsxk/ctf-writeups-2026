FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils-aarch64-linux-gnu \
        gcc-aarch64-linux-gnu \
        libc6-dev-arm64-cross \
        make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY vuln.c /src/vuln.c

RUN mkdir -p /out \
    && aarch64-linux-gnu-gcc -O2 -g \
        -fstack-protector-all \
        -fPIE -pie \
        -Wl,-z,relro,-z,now \
        -z noexecstack \
        -o /out/military-system /src/vuln.c
