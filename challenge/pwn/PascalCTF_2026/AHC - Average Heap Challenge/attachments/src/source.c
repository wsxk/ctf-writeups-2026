// gcc -o average source.c -fstack-protector-all -Wl,-z,relro,-z,now -pie -fPIE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Player {
  char name[32];
  char message[40];
};

int player_count = 0;
struct Player *players[5];
int extra_lengths[5];
long *target;

void setup_chall() {
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stdin, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);

  for (int i = 0; i < 5; i++) {
    players[i] = malloc(sizeof(struct Player));
  }

  for (int i = 4; i >= 0; i--) {
    free(players[i]);
    players[i] = NULL;
  }

  target = (long *)malloc(0x8);
  *target = (long)0xbabebabebabebabe;
}

int read_int(int min, int max) {
  int num;
  scanf("%d", &num);

  if (num > max || num < min) {
    puts("Invalid number!");
    exit(1);
  }

  return num;
}

int read_name(char *name_buffer, int extra_len) {
  printf("Enter name: ");
  char fmt[16];
  snprintf(fmt, sizeof(fmt), "%%%ds", 39 + extra_len);
  scanf(fmt, name_buffer);
  return strlen(name_buffer) + 1;
}

int read_message(char *message_buffer) {
  printf("Enter message: ");
  scanf("%39s", message_buffer);
  return strlen(message_buffer) + 1;
}

void create_player() {
  if (player_count >= 5) {
    puts("Player limit reached!");
    return;
  }

  printf("Choose an index (0-4) to create the player at: ");
  int idx = read_int(0, 4);
  if (players[idx] != NULL) {
    puts("Player already exists at this index!");
    return;
  }

  printf(
      "The default name length is 32 characters, how many more do you need? ");
  int extra_name_len = read_int(0, 32);
  struct Player *new_player =
      (struct Player *)malloc(sizeof(struct Player) + extra_name_len);

  int name_length = read_name(new_player->name, extra_name_len);
  if (name_length < 32 + extra_name_len)
    name_length = 32 + extra_name_len;
  int message_length = read_message(new_player->name + name_length);

  players[idx] = new_player;
  extra_lengths[idx] = name_length - 32;
  player_count++;

  printf("Created player at index %d\n", idx);
}

void delete_player() {
  if (player_count == 0) {
    puts("No players to delete!");
    return;
  }

  printf("Choose an index (0-4) to delete the player from: ");
  int idx = read_int(0, 4);
  if (players[idx] == NULL) {
    puts("No player exists at this index!");
    return;
  }

  free(players[idx]);
  players[idx] = NULL;
  player_count--;

  printf("Deleted player at index %d\n", idx);
}

void print_players() {
  for (int i = 0; i < 5; i++) {
    if (players[i] != NULL) {
      printf("Player %d: Name: %s, Message: %s\n", i, players[i]->name,
             players[i]->message + extra_lengths[i]);
    } else {
      printf("Player %d: <empty>\n", i);
    }
  }
}

void check_target() {
  if (*target == (long)0xdeadbeefcafebabe) {
    puts("I see you know your way around this stuff, here's a flag!");
    if (getenv("FLAG"))
      puts(getenv("FLAG"));
    else
      puts("Something went enormously wrong...");

  } else {
    puts("Target value not matched. Retry.");
  }
}

void print_menu() {
  puts("1. Create Player");
  puts("2. Delete Player");
  puts("3. Print Players");
  puts("4. Exit");
  printf("> ");
}

int main() {
  setup_chall();

  while (1) {
    print_menu();
    int choice = read_int(1, 5);

    switch (choice) {
    case 1:
      create_player();
      break;
    case 2:
      delete_player();
      break;
    case 3:
      print_players();
      break;
    case 4:
      puts("Exiting...");
      exit(0);
    case 5:
      check_target();
      break;
    default:
      puts("Invalid choice!");
      break;
    }
  }
  return 0;
}
