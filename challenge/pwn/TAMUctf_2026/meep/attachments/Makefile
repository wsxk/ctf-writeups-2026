NAME := meep

REGISTRY :=
SUFFIX :=

CPORTS := 9001
HPORTS := $(CPORTS)
SERVICES := PWN

$(foreach var, \
	$(shell \
		python -c "for s, p in zip('$(SERVICES)'.split(), '$(CPORTS)'.split()): print(f'{s}_CPORT:={p}')" \
	), $(eval $(var)) \
)

DOCKER_CONTEXT := default
DOCKER_GLOBAL := --context $(DOCKER_CONTEXT)
DOCKER_RUNTIME := --memory=128m --cpus=0.2 --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --restart=always

compile-prod:
	docker build -f Dockerfile.builder -t $(NAME)-builder .
	docker run --rm -v $(PWD):/src -w /src $(NAME)-builder \
		mips-linux-gnu-gcc -O0 -mips32 -g \
		-Wl,--dynamic-linker=/lib/ld.so.1 \
		-Wl,-rpath=/lib \
		-L /src/lib-mips \
		-I /src/lib-mips/include \
		-fno-stack-protector \
		-no-pie \
		-o meep meep_prod.c

compile-debug:
	docker build -f Dockerfile.builder -t $(NAME)-builder .
	docker run --rm -v $(PWD):/src -w /src $(NAME)-builder \
		mips-linux-gnu-gcc -O0 -mips32 -g \
		-Wl,--dynamic-linker=/lib/ld.so.1 \
		-Wl,-rpath=/lib \
		-L /src/lib-mips \
		-I /src/lib-mips/include \
		-fno-stack-protector \
		-no-pie \
		-o meep meep.c

build: compile-prod
	docker $(DOCKER_GLOBAL)  build -f Dockerfile -t $(NAME) . --build-arg FLAG_FILE=flag.txt

run: 
	$(eval ports := $(shell python -c "for h, c in zip('$(HPORTS)'.split(), '$(CPORTS)'.split()): print(f' -p {h}:{c}')"))
	docker $(DOCKER_GLOBAL) run $(DOCKER_RUNTIME) -d --name $(NAME)$(SUFFIX) $(ports) $(REGISTRY)$(NAME)

dist: compile-debug
	mkdir -p build/$(NAME)
	mv $(NAME) build/$(NAME)/
	cp fake-flag.txt solver-template.py Dockerfile Makefile.debug entrypoint.sh build/$(NAME)/
	cp -r lib-mips build/$(NAME)/
	tar -czf $(NAME).tar.gz -C build $(NAME)
	rm -rf build

clean:
	rm -f $(NAME).tar.gz
	docker container rm -f $(NAME)$(SUFFIX)

.PHONY: compile-prod compile-debug build run dist
