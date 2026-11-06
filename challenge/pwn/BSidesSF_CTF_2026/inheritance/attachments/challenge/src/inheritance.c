#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <sys/mman.h>

void setup() {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

int main() {
    setup();
    printf("--- Secure Command Execution Service ---\r\n");

    // 1. Read the flag from the filesystem
    FILE *f = fopen("flag.txt", "r");
    if (!f) {
        perror("Error: flag.txt is missing");
        exit(1);
    }
    char flag[128] = {0};
    fgets(flag, sizeof(flag), f);
    fclose(f);

    // 2. Create an anonymous in-memory file.
    // By passing 0 instead of MFD_CLOEXEC, we intentionally leak this FD!
    int fd = memfd_create("secret_config", 0);
    if (fd < 0) {
        perror("memfd_create failed");
        exit(1);
    }

    // 3. Write the flag to our memory file and rewind the cursor to the beginning
    write(fd, flag, strlen(flag));
    lseek(fd, 0, SEEK_SET);

    printf("[*] Secret configuration securely loaded into memory (FD %d).\r\n", fd);
    printf("[*] Enter a command to run (max 32 chars): ");

    char cmd[32];
    if (fgets(cmd, sizeof(cmd), stdin) == NULL) {
        exit(1);
    }

    cmd[strcspn(cmd, "\n")] = 0;

    // Strict WAF Evasion
    // Block redirection characters to force the use of procfs
    if (strchr(cmd, '<') != NULL || strchr(cmd, '>') != NULL) {
        printf("[!] Security Violation: Shell redirection is strictly prohibited.\r\n");
        exit(1);
    }

    // Block direct references to the proc filesystem and the flag
    char *denylist[] = {"flag", "proc", "fd", "*", "grep"};
    for (int i = 0; i < 3; i++) {
        if (strstr(cmd, denylist[i]) != NULL) {
            printf("[!] Security Violation: Denylisted keyword '%s' detected.\r\n", denylist[i]);
            exit(1);
        }
    }

    printf("\n[*] Executing: %s\r\n", cmd);
    system(cmd);

    return 0;
}
