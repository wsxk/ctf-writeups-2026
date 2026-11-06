NAME := military-system
CHALLENGE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(CHALLENGE_DIR)/../..)
ARTIFACT_CONT := $(NAME)-artifact

REGISTRY :=
SUFFIX :=

CPORTS := 9001
HPORTS := $(CPORTS)
SERVICES := PWN

$(foreach var, \
	$(shell \
		python3 -c "for s, p in zip('$(SERVICES)'.split(), '$(CPORTS)'.split()): print(f'{s}_CPORT:={p}')" \
	), $(eval $(var)) \
)

DOCKER_CONTEXT := default
DOCKER_GLOBAL := --context $(DOCKER_CONTEXT)
DOCKER_RUNTIME := --memory=128m --cpus=0.2 --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --restart=always

.PHONY: compile compile-native build run dist clean

compile:
	docker $(DOCKER_GLOBAL) build -f $(CHALLENGE_DIR)/Dockerfile.builder -t $(NAME)-builder $(CHALLENGE_DIR)
	docker $(DOCKER_GLOBAL) container rm -f $(ARTIFACT_CONT) >/dev/null 2>&1 || true
	docker $(DOCKER_GLOBAL) create --name $(ARTIFACT_CONT) $(NAME)-builder true
	docker $(DOCKER_GLOBAL) cp $(ARTIFACT_CONT):/out/$(NAME) $(CHALLENGE_DIR)/$(NAME)
	docker $(DOCKER_GLOBAL) container rm -f $(ARTIFACT_CONT) >/dev/null

compile-native:
	gcc -O2 -g \
		-fstack-protector-all \
		-fPIE -pie \
		-Wl,-z,relro,-z,now \
		-z noexecstack \
		-o $(CHALLENGE_DIR)/$(NAME) $(CHALLENGE_DIR)/vuln.c

build: compile
	docker $(DOCKER_GLOBAL) build -f $(CHALLENGE_DIR)/Dockerfile -t $(NAME) $(REPO_ROOT) --build-arg FLAG_FILE=flag.txt

run:
	$(eval ports := $(shell python3 -c "for h, c in zip('$(HPORTS)'.split(), '$(CPORTS)'.split()): print(f' -p {h}:{c}')"))
	docker $(DOCKER_GLOBAL) run $(DOCKER_RUNTIME) -d --name $(NAME)$(SUFFIX) $(ports) $(REGISTRY)$(NAME)

dist: compile
	mkdir -p $(CHALLENGE_DIR)/build/$(NAME)
	cp $(CHALLENGE_DIR)/$(NAME) $(CHALLENGE_DIR)/build/$(NAME)/
	cp $(CHALLENGE_DIR)/fake-flag.txt $(CHALLENGE_DIR)/solver-template.py $(CHALLENGE_DIR)/Dockerfile $(CHALLENGE_DIR)/Makefile.debug $(CHALLENGE_DIR)/entrypoint.sh $(CHALLENGE_DIR)/build/$(NAME)/
	tar -czf $(CHALLENGE_DIR)/$(NAME).tar.gz -C $(CHALLENGE_DIR)/build $(NAME)
	rm -rf $(CHALLENGE_DIR)/build

clean:
	rm -f $(CHALLENGE_DIR)/$(NAME).tar.gz
	docker container rm -f $(NAME)$(SUFFIX)
