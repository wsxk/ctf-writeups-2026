GCC := gcc
COMPOSE := docker compose
PWD := $(shell pwd)

up: compile
	$(COMPOSE) up --build -d
	rm malta

down:
	$(COMPOSE) down

compile:
	$(GCC) malta.c -o malta

chall: compile
	zip -r malta.zip malta
	mv malta.zip $(PWD)/../attachments/malta.zip
	rm malta

clean: down
	rm malta