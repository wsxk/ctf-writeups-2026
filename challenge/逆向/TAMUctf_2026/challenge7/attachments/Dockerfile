FROM python:3.14-slim-bookworm

ARG name=challenge7

RUN apt-get update -y \
	&& apt-get install -y --no-install-recommends build-essential binutils \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY scripts ./scripts
COPY src ./src

RUN mkdir -p build \
	&& python3 scripts/gen_inner_expected.py \
	&& gcc -O2 -fno-stack-protector -fPIE -fPIC -fvisibility=hidden -I src -c src/inner.c -o build/inner.o \
	&& python3 scripts/gen_inner_chunks.py \
	&& gcc -O2 -fno-stack-protector -fPIE -fvisibility=hidden -I src src/main.c build/inner.o -pie -s -o build/${name} \
	&& CHALLENGE_BIN=build/${name} python3 scripts/gen_self_hash.py \
	&& gcc -O2 -fno-stack-protector -fPIE -fvisibility=hidden -I src src/main.c build/inner.o -pie -s -o build/${name} \
	&& cp build/${name} /tmp/${name}

