CC = gcc
CFLAGS = -Wall -Wextra -O0 -g -fPIE -fstack-protector-all
LDFLAGS = -lpthread

SRCS = main.c entities.c lives.c logging.c
OBJS = $(SRCS:.c=.o)
TARGET = PT2

COMPOSE := docker compose
PWD := $(shell pwd)


.PHONY: all clean

all: $(TARGET)

compile: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS) $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(OBJS)

oclean:
	rm -f $(OBJS)

up: compile
	$(COMPOSE) up --build -d
	rm PT2

down:
	$(COMPOSE) down

chall: compile
	mv PT2 $(PWD)/../attachments/PT2
	make oclean