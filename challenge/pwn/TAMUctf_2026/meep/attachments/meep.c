#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>

#define PORT 9001   // The port your buffer overflow will occur on

void call_func(char *arg, int (*fn)(const char *)) {

    fn(arg);
}

void diagnostics() {
    char cmd[128];

    register char *checker asm("s0") = cmd;
    register char *checker2 asm("s1") = cmd;

    send(STDOUT_FILENO, "Enter diagnostic command:\n", 27, 0);
    recv(STDIN_FILENO, cmd, 256, 0);  // Vulnerable: buffer overflow
    send(STDOUT_FILENO, "Running command...\n", 19, 0);

    if (checker[0] == ' ') {
        send(STDOUT_FILENO, "Cannot start with a space!\n", 11, 0);
    }

    if (checker[127] == ' ') {
        send(STDOUT_FILENO, "Cannot end with a space!\n", 11, 0);
    }

    
}

void greet(int (*logger)(const char *)) {
    char name[128];

    int (*my_logger)(const char *) = logger;

    send(STDOUT_FILENO, "Enter admin name: ", 18, 0);
    recv(STDIN_FILENO, name, 256, 0);

    my_logger("\nHello:\n");
    printf(name); 
}

int main() {

    volatile int (*puts_logger)(const char *) = puts;

    setbuf(stdout, NULL);
    setbuf(stdin, NULL);

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if(sockfd < 0) { perror("socket"); exit(1); }

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(PORT);

    if(bind(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) { perror("bind"); exit(1); }
    if(listen(sockfd, 5) < 0) { perror("listen"); exit(1); }

    printf("Listening on port %d...\n", PORT);

    while(1) {
        int client = accept(sockfd, NULL, NULL);
        if(client < 0) continue;

        dup2(client, STDIN_FILENO);
        dup2(client, STDOUT_FILENO);
        dup2(client, STDERR_FILENO);

        greet(puts_logger);
        diagnostics();

        close(client);
    }

    return 0;
}