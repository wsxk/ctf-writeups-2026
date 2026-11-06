GCC := gcc
COMPOSE := docker compose
PWD := $(shell pwd)

up: compile
	$(COMPOSE) up --build -d
	rm average

down:
	$(COMPOSE) down

compile:
	$(GCC) source.c -o average -fstack-protector-all -Wl,-z,relro,-z,now -pie -fPIE


chall: compile
	zip -r average.zip average
	mv average.zip $(PWD)/../attachments/average.zip
	rm average

clean: down
	rm average
