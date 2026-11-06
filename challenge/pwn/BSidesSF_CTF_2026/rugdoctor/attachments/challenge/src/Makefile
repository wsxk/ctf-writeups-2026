NAME=rugdoctor

all: ${NAME}

${NAME}: ${NAME}.c
	gcc -o ${NAME} -O0 -masm=intel -Wall -Wextra ${NAME}.c
	strip ${NAME}

clean:
	rm -f *.o ${NAME}
