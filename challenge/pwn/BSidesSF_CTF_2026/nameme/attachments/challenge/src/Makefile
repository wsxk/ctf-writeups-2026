NAME=nameme

all: ${NAME}

${NAME}: ${NAME}.c
	gcc -o ${NAME} -O0 -static -Wall -Wextra -no-pie -fno-stack-protector -fomit-frame-pointer ${NAME}.c
	strip ${NAME}

clean:
	rm -f *.o ${NAME}
