CC = gcc
CFLAGS = -Wall -Wextra -g
TARGET = mygit

SRCS = main.c \
       core/repository.c \
       core/objects.c \
       core/staging.c \
       core/commit.c \
       core/branch.c \
       utils/file.c

OBJS = $(SRCS:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c main.h
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET)

chall: all
	mv $(TARGET) ../attachments/git

.PHONY: all clean chall
