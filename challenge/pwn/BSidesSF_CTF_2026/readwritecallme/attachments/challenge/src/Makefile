NAME=readwritecallme

all: ${NAME}

${NAME}: ${NAME}.c
	gcc -o ${NAME} -O0 -Wall -Wextra -no-pie -fno-stack-protector ${NAME}.c

clean:
	rm -f *.o ${NAME}
