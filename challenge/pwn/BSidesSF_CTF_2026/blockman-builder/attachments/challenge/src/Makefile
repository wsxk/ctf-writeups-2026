NAME=bmb
TINFOW_LDFLAGS=$(shell test -e /usr/lib/libtinfow.so -o -e /usr/lib64/libtinfow.so -o -e /lib/x86_64-linux-gnu/libtinfow.so -o -e /usr/lib/x86_64-linux-gnu/libtinfow.so && echo -ltinfow)

all: ${NAME}

${NAME}: ${NAME}.c
	gcc -o ${NAME} -g -O0 -Wall -Wextra ${NAME}.c -lncursesw ${TINFOW_LDFLAGS} -lm -lz -Wl,-z,execstack -Wl,--no-warn-execstack

clean:
	rm -f *.o ${NAME}
