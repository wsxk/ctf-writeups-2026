#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

void init(char *descriptions[10]) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    descriptions[9] = getenv("FLAG");
    if (descriptions[9] == NULL) {
        puts("No flag found");
        exit(1);
    }
}   

int main(int argc, char * argv[]) {
    char *drinks[10] = {
        "Margarita",
        "Mojito",
        "Gin lemon",
        "PascalCTF26",
        "Cosmopolitan",
        "Lavander Collins",
        "Japanese slipper",
        "Blue angel",
        "Martini",
        "Flag"
    };
    char *descriptions[10] = {
        "Tequila & lime",
        "Minty & refreshing",
        "Gin with lemon",
        "Secret challenge ;)",
        "Cranberry & vodka",
        "Lavender twist",
        "Melon & citrus",
        "Blue & sweet",
        "Classic & dry",
        ""
    };
    
    const int costi[10] = {
        6, 6, 5, 6, 6, 4, 5, 6, 3, 1000000000
    };

    int saldo = 100;

    init(descriptions);

    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMW0OXMMMMMMMMMMMMMMMMMMMMMMMMMMMMXO0WMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMKolkXWMMMMMMMMMMMMMMMMMMMMMMMXkloKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:;lkXWMMMMMMMMMMMMMMMMMMWXkl;:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,;lkXWMMMMMMMMMMMMMMMXkl;,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMKl,,,;lkXWMMMMMMMMMMWXkl;,,,lKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,;lkXMMMMMMMWXkl;,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,;lkXWMMWXkl;,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMKl,,,,,,,;lkKKkl;,,,,,,,lKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,,,;;;;,,,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,,,,,,,,,,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMKl,,,,,,,,,,,,,,,,,,lKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,,,,,,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,,,,,,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMKl,,,,,,,,,,,,,,lKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("XKXNWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWKl,,,,,,,,,,lKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWNXKX");
    puts("XOoloxk0KNWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWNX0kdoloOX");
    puts("MMNkl;,;:coxk0XNWMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMWNX0kxoc:;,;lkXWM");
    puts("MMMWXkl;,,,,,;:codk0KNWMMMMMMMMMMMMMMMMMMMMMMKl,,,,,,lKMMMMMMMMMMMMMMMMMMMMMMWNK0kxoc:;,,,,,;lkXWMMM");
    puts("MMMMMWXkl;,,,,,,,,,;:codk0KNWMMMMMMMMMMMMMMMMWO:,,,,:OWMMMMMMMMMMMMMMMMWNK0kxoc:;,,,,,,,,,;lkNMMMMMM");
    puts("MMMMMMMWXkl;,,,,,,,,,,,,,;:codk0KNWMMMMMMMMMMMNd;,,;dNMMMMMMMMMMMWNX0kxoc:;,,,,,,,,,,,,,;lkNMMMMMMMM");
    puts("MMMMMMMMMWXkl;,,,,,,,,,,,,,,,,,;:coxk0XNWMMMMMMKl,,lKMMMMMMWNK0kxoc:;,,,,,,,,,,,,,,,,,;lkXMMMMMMMMMM");
    puts("MMMMMMMMMMMWXkl;,,,,,,,,,,,,,,,,,,,,,;:coxk0XNWWkllOWWNX0kxoc:;,,,,,,,,,,,,,,,,,,,,,;lkNMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMWXd;,,,,,,,,,,,,,,,,,,,,,,,,,,;:cdkOOOOkdl:;,,,,,,,,,,,,,,,,,,,,,,,,,,;dXWMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMWXkl;,,,,,,,,,,,,,,,,,,,,,,,;:coxk0KOxxOK0kxoc:;,,,,,,,,,,,,,,,,,,,,,,,;lkXWMMMMMMMMMMMM");
    puts("MMMMMMMMMMWXkl;,,,,,,,,,,,,,,,,,,,;:coxk0XNWMMMNd:;dNMMMWNK0kxoc:;,,,,,,,,,,,,,,,,,,,;lkXWMMMMMMMMMM");
    puts("MMMMMMMMMXkl;,,,,,,,,,,,,,,,;:coxk0KNWMMMMMMMMWO:,,:OWMMMMMMMMWNK0kxoc:;,,,,,,,,,,,,,,,;lkXWMMMMMMMM");
    puts("MMMMMMMXkl;,,,,,,,,,,,;:coxk0KNWMMMMMMMMMMMMMMKl,,,,lKWMMMMMMMMMMMMMWNK0kxoc:;,,,,,,,,,,,;lkXWMMMMMM");
    puts("MMMMMXkl;,,,,,,,;:coxk0XNWMMMMMMMMMMMMMMMMMMMNd;,,,,;dNMMMMMMMMMMMMMMMMMMMWNK0kxoc:;,,,,,,,;lkXMMMMM");
    puts("MMMXkl;,,,;:coxk0KNWMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMWNK0kxoc:;,,,;lkXWMM");
    puts("WXkl;:coxk0KNWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWKl,,,,,,,,lKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWNK0kdoc:;lkXW");
    puts("KOxk0KNWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWNK0kxkK");
    puts("WWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWN");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWKl,,,,,,,,,,,,lKWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,,,,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,,,,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWKl,,,,,,,,,,,,,,,,lKWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,,,,,,,,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,,,,,,,,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMKl,,,,,,,,,,,,,,,,,,,,lKWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,,,,,;lddl;,,,,,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,,,,,;lkXWWXkl;,,,,,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMKl,,,,,;lkNMMMMMMNkl;,,,,,lKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;,,,;lkXMMMMMMMMMWXkl;,,,;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO:,,;lkNMMMMMMMMMMMMMMXkl;,,:OWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMKl,;lkNMMMMMMMMMMMMMMMMMWXkl;,lKWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNd;lkXMMMMMMMMMMMMMMMMMMMMMMXkl;dNMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWOdkXWMMMMMMMMMMMMMMMMMMMMMMMMWXkdOWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");
    puts("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMN0KWWMMMMMMMMMMMMMMMMMMMMMMMMMMMWK0NMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM");

    puts("Welcome in Malta, here you're to buy some of the cheapest cocktails in the world!");
    while(1) {
        printf("Your balance is: %d €\n", saldo);

        for(int i=0; i<10; i++){
            printf("%d. Drink: %s for %d €\n", i+1, drinks[i], costi[i]);
        }
        puts("11. Exit\n");

        printf("Select a drink: ");
        int choice;
        scanf("%d", &choice);
        choice--;

        if (choice == 10) {
            puts("Bye bye!");
            break;
        }
        
        if (choice < 0 || choice > 10) {
            puts("Invalid choice");
            continue;
        }

        int amount;
        printf("How many drinks do you want? ");
        scanf("%d", &amount);

        if (amount * costi[choice] > saldo) {
            puts("You don't have enough money!");
        }
        else {
            saldo -= amount * costi[choice];
            printf("You bought %d %s for %d € and the barman told you its secret recipe: %s\n", amount, drinks[choice], amount * costi[choice], descriptions[choice]);    
        }
        sleep(2);
    }
    return 0;
}