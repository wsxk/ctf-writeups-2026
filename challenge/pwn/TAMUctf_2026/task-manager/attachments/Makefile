# deployment vars
NAME := task-manager
# ============================================================
# NOTE: the following are only necessary if hosting containers
# This can be safely removed
# ============================================================

REGISTRY :=
SUFFIX :=

# configurable vars:
# HPORTS="8888 8889" make -e ...
CPORTS := 1337
HPORTS := $(CPORTS)
SERVICES := PWN #DASHBOARD UART0

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
DOCKER_RUNTIME := --memory=128m --cpus=0.2 --read-only --restart=always

# ============================================================
# NOTE: if not compiling, the $(NAME) dep along with compilation
# 	directive can be safely removed
#	docker directives may be removed if docker is not used
#	dist directives should be omitted if there is no distributable
# ============================================================

# build vars
CC := $(or $(CC),gcc)
CFLAGS := -fstack-protector-all -Wl,-z,relro,-z,now -fPIE -pie -Wl,-z,noexecstack -D_FORTIFY_SOURCE=2 -fcf-protection=none
LDFLAGS := 
all: $(NAME)

$(NAME): $(NAME).c
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@ 

# removes all build artifacts
# modify as needed
clean:
	rm -f $(NAME).tar.gz
	docker container rm -f $(NAME)$(SUFFIX)

build: Dockerfile
	docker $(DOCKER_GLOBAL) build -t $(NAME) \
		--build-arg name=$(NAME) \
		--build-arg port=$(PWN_CPORT) \
		.

run:
	$(eval ports := $(shell python -c "for h, c in zip('$(HPORTS)'.split(), '$(CPORTS)'.split()): print(f' -p {h}:{c}')"))
	docker $(DOCKER_GLOBAL) run $(DOCKER_RUNTIME) -d --name $(NAME)$(SUFFIX) $(ports) $(REGISTRY)$(NAME)

extract:
	mkdir build
	$(eval id := $(shell docker create $(NAME)))
	docker cp $(id):/pwn/$(NAME) build/$(NAME)
	docker cp $(id):/lib/x86_64-linux-gnu/libc.so.6 build/libc.so.6
	docker cp $(id):/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 build/ld-linux-x86-64.so.2
	docker rm -v $(id)

dist: extract
	cp $(NAME).c build
	cp solver-template.py build
	mv build $(NAME)
	tar -czf $(NAME).tar.gz $(NAME)
	rm -rf $(NAME)

.PHONY: all clean build run extract dist
