# deployment vars
NAME := hyper-neighbor
# ============================================================
# NOTE: the following are only necessary if hosting containers
# This can be safely removed
# ============================================================

REGISTRY :=
SUFFIX :=

# configurable vars:
# HPORTS="8888 8889" make -e ...
CPORTS := 6969
HPORTS := $(CPORTS)
SERVICES := SHELL

# generate service -> port mappings: SERVICE_PORT := PORT
# this is necessary for docker compose string substitution via env variables
# also useful for containers requiring build args for setting ports on multiple services
$(foreach var, \
	$(shell \
		python3 -c "for s, p in zip('$(SERVICES)'.split(), '$(CPORTS)'.split()): print(f'{s}_CPORT:={p}')" \
	), $(eval $(var)) \
)

# docker
DOCKER_CONTEXT := default
DOCKER_GLOBAL := --context $(DOCKER_CONTEXT)
# we MUST bind this to a single (hyperthreaded) core
DOCKER_RUNTIME := --memory=128m --cpuset-cpus 1 --privileged --restart=always --read-only --tmpfs /tmp

# ============================================================
# NOTE: if not compiling, the $(NAME) dep along with compilation
# 	directive can be safely removed
#	docker directives may be removed if docker is not used
#	dist directives should be omitted if there is no distributable
# ============================================================

# removes all build artifacts
# modify as needed
clean:
	rm -rf build
	rm -f $(NAME).tar.gz
	docker container rm -f $(NAME)$(SUFFIX)
	docker container rm -f $(NAME)-adjacent

build: Dockerfile
	docker $(DOCKER_GLOBAL) build -t $(NAME) \
		--build-arg name=$(NAME) \
		--build-arg shell_port=$(SHELL_CPORT) \
		.
	docker $(DOCKER_GLOBAL) build -t $(NAME)-adjacent \
	    --build-arg name=$(NAME) \
	    --file Dockerfile.adjacent \
	    .

run:
	$(eval ports := $(shell python3 -c "for h, c in zip('$(HPORTS)'.split(), '$(CPORTS)'.split()): print(f' -p {h}:{c}')"))
	docker $(DOCKER_GLOBAL) run $(DOCKER_RUNTIME) -d --name $(NAME)$(SUFFIX) $(ports) $(REGISTRY)$(NAME)
	-docker $(DOCKER_GLOBAL) run --cpuset-cpus 0 --restart=always -d --name $(NAME)-adjacent $(REGISTRY)$(NAME)-adjacent

extract: build
	mkdir build
	$(eval id := $(shell docker create $(NAME)-adjacent))
	docker cp $(id):/send build/$(NAME)
	docker rm -v $(id)

dist: extract
	cp solver-template.py build
	cp Dockerfile build
	mv build $(NAME)
	tar -czf $(NAME).tar.gz $(NAME)
	rm -rf $(NAME)

.PHONY: clean build run extract dist
