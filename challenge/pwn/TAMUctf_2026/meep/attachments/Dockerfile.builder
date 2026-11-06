FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    gcc-mips-linux-gnu \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY meep.c /src/
COPY meep_prod.c /src/
COPY lib-mips /src/lib-mips