GCC := gcc
COMPOSE := docker compose
PWD := $(shell pwd)

up: compile
	$(COMPOSE) up --build -d
	rm -rf notetaker

down:
	$(COMPOSE) down

compile:
	docker run --rm -v $(PWD):/app -w /app ubuntu:xenial \
		/bin/bash -c "apt-get update && apt-get install -y gcc && \
		gcc main.c -o notetaker \
		-L./libs \
		-Wl,--rpath=./libs/ \
		-Wl,--dynamic-linker=./libs/ld-2.23.so \
		-no-pie -Wl,-z,relro,-z,now -fstack-protector-all"

chall: compile
	mkdir -p challenge
	cp -r libs challenge/
	cp notetaker challenge/
	zip -r notetaker.zip challenge/
	mv notetaker.zip $(PWD)/../attachments/notetaker.zip
	rm -rf challenge

clean: down
	rm -rf build