NAME=wromwarp

all: ${NAME}

${NAME}: ${NAME}.c
	gcc -o ${NAME} -O0 -Wall -Wextra ${NAME}.c -lncurses -ltinfo

clean:
	rm -f *.o ${NAME}
