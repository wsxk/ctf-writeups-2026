# deployment vars
NAME := challenge7
# ============================================================
# NOTE: the following are only necessary if hosting containers
# This can be safely removed
# ============================================================

REGISTRY :=
SUFFIX :=


# generate service -> port mappings: SERVICE_PORT := PORT
# this is necessary for docker compose string substitution via env variables
# also useful for containers requiring build args for setting ports on multiple services
$(foreach var, \
	$(shell \
		python -c "for s, p in zip('$(SERVICES)'.split(), '$(CPORTS)'.split()): print(f'{s}_CPORT:={p}')" \
	), $(eval $(var)) \
)

# docker
DOCKER_CONTEXT := default
DOCKER_GLOBAL := --context $(DOCKER_CONTEXT)
DOCKER_RUNTIME := --memory=256m --cpus=0.3 --read-only --restart=always

# ============================================================
# NOTE: if not compiling, the $(NAME) dep along with compilation
# 	directive can be safely removed
#	docker directives may be removed if docker is not used
#	dist directives should be omitted if there is no distributable
# ============================================================

# build vars
CC := $(or $(CC),gcc)
CFLAGS := -O2 -fno-stack-protector -fPIE -fvisibility=hidden -I src
LDFLAGS := -pie -s

all: compile

compile: build/$(NAME)

build/inner.o: src/inner.c src/inner_expected.h src/loader_abi.h
	mkdir -p build
	$(CC) $(CFLAGS) -fPIC -c src/inner.c -o build/inner.o

src/inner_expected.h: scripts/gen_inner_expected.py
	python3 scripts/gen_inner_expected.py

src/inner_chunks.h: scripts/gen_inner_chunks.py build/inner.o
	python3 scripts/gen_inner_chunks.py

src/self_hash.h: scripts/gen_self_hash.py build/$(NAME)
	CHALLENGE_BIN=build/$(NAME) python3 scripts/gen_self_hash.py

build/$(NAME): src/main.c src/loader_abi.h src/inner_chunks.h src/inner_expected.h build/inner.o
	mkdir -p build
	$(CC) $(CFLAGS) src/main.c build/inner.o -o build/$(NAME) $(LDFLAGS)
	CHALLENGE_BIN=build/$(NAME) python3 scripts/gen_self_hash.py
	$(CC) $(CFLAGS) src/main.c build/inner.o -o build/$(NAME) $(LDFLAGS)

regen: src/inner_expected.h src/inner_chunks.h src/self_hash.h

# removes all build artifacts
# modify as needed
clean:
	rm -f $(NAME).tar.gz
	rm -f build/$(NAME) build/inner.o build/$(NAME).text.bin build/challenge7_main.text.bin build/inner.text.bin
	docker container rm -f $(NAME)$(SUFFIX) >/dev/null 2>&1 || true

build: Dockerfile
	docker $(DOCKER_GLOBAL) build -t $(NAME) \
		--build-arg name=$(NAME) \
		.

extract: build
	mkdir -p build
	$(eval id := $(shell docker create $(NAME)))
	docker cp $(id):/tmp/$(NAME) build/$(NAME)
	docker rm -v $(id)

dist: extract
	mv build $(NAME)
	tar -czf $(NAME).tar.gz $(NAME)
	rm -rf $(NAME)

.PHONY: all compile regen clean build extract dist
