#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void init() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
}

void menu() {
    puts("1. Read note");
    puts("2. Write note");
    puts("3. Clear note");
    puts("4. Exit");
    printf("> ");
}

int main() { 
    init();
    char buffer[256];
    memset(buffer, 0, 256);
    int choice;

    do {
        menu();

        char *buff = malloc(16);
        memset(buff, 0, 16);
        fgets(buff, 16, stdin);
        sscanf(buff, "%d", &choice);
        free(buff);

        switch(choice) {
            case 1:
                printf(buffer);
                putchar('\n');
                break;
            case 2:
                printf("Enter the note: ");
                read(STDIN_FILENO, buffer, 256);
                buffer[strcspn(buffer, "\n")] = 0;
                break;
            case 3:
                memset(buffer, 0, 256);
                printf("Note cleared.\n");
                break;
            default:
                break;
        }
    } while(choice > 0 && choice < 5);
    return 0;
}