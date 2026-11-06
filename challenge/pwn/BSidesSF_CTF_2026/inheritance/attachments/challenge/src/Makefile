NAME=inheritance

all: ${NAME}

${NAME}: ${NAME}.c
	gcc -o ${NAME} -O2 -fPIE -pie -Wl,-z,relro,-z,now -Wall -Wextra ${NAME}.c

clean:
	rm -f *.o ${NAME}
