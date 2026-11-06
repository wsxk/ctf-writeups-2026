#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

int main(void) {
  int offset = 0;
  char input[128];
  char password[32];
  char idv3[128];

  /* Prevent timing attacks or bruteforcing (ACTUALLY! There's a better way to
   * solve this!!) */
  fprintf(stderr, "Loading.......\n");
  srand((unsigned)time(NULL));
  useconds_t usec = 1000000 + rand() % 1000001;  // 1-2 seconds
  usleep(usec);

  /* Read the secret password */
  FILE *password_file = fopen("password.txt", "r");
  if(!password_file) {
    perror("fopen");
    exit(1);
  }
  fgets(password, 32, password_file);
  password[strcspn(password, "\n")] = '\0';

  /* Challenge the user */
  fprintf(stderr, "For SUPER SECRET ACCESS to the DRM'd media, please enter the SUPER SECRET PASSWORD!! -> ");
  fgets(input, 30, stdin);
  input[strcspn(input, "\n")] = '\0';
  // fprintf(stderr, "--\n%d:%d\n--\n", strlen(input), strlen(password));
  if(!strcmp(input, password)) {
    fprintf(stderr, "Well done! Here's your super secret media:\n");
    fprintf(stderr, "\n");

    /* "Secret" data we do NOT want to leak */
    FILE *flag = fopen("flag.txt", "r");
    if(!flag) {
      perror("fopen");
      exit(1);
    }
    fgets(input, 64, flag);
    fclose(flag);

    printf("%s\n", input);
    exit(0);
  }

  fprintf(stderr, "That password isn't correct, but that's okay! Let's tag some music instead!\n");
  fprintf(stderr, "\n");
  fprintf(stderr, "Your Super ID3 Tag Generator is READY!!!\n");
  fprintf(stderr, "\n");
  fprintf(stderr, "Let's collect some information...\n");
  fprintf(stderr, "\n");

  // Start with empty, pristine memory
  memset(idv3, '\0', sizeof(idv3));

  // Bytes 0–2: Literal "TAG" identifier.
  offset += snprintf(idv3 + offset, 4, "TAG");

  // Bytes 3–32: Title (30 bytes, ISO‑8859‑1, padded with zeros/spaces).
  fprintf(stderr, "Title? --> ");
  fgets(input, 31, stdin);
  input[strcspn(input, "\n")] = '\0';
  offset += snprintf(idv3 + offset, 31, "%-30s", input);

  // Bytes 33–62: Artist (30 bytes).
  fprintf(stderr, "Artist? --> ");
  fgets(input, 31, stdin);
  input[strcspn(input, "\n")] = '\0';
  offset += snprintf(idv3 + offset, 31, "%-30s", input);

  // Bytes 63–92: Album (30 bytes).
  fprintf(stderr, "Album? --> ");
  fgets(input, 31, stdin);
  input[strcspn(input, "\n")] = '\0';
  offset += snprintf(idv3 + offset, 31, "%-30s", input);

  // Bytes 93–96: Year (4 ASCII digits).
  fprintf(stderr, "Release year? --> ");
  int year;
  if(scanf("%d", &year) != 1) {
    fprintf(stderr, "Invalid year!\n");
    exit(1);
  }
  offset += snprintf(idv3 + offset, 5, "%04d", year);
  while(getchar() != '\n') {}  // discard rest of line

  // Bytes 97–125: Comment (28 bytes).
  fprintf(stderr, "Comment? --> ");
  fgets(input, 30, stdin);
  input[strcspn(input, "\n")] = '\0';
  offset += snprintf(idv3 + offset, 30, "%-29s", input);

  // Bytes 127-128 - unused in v1.0
  offset += 2;

  // Tell them it's done
  fprintf(stderr, "\n\nAll done! Compiling your ID3 tag....\n");

  // Get a file to attach the tag to
  fprintf(stderr, "\n\nFile to attach the ID3 tag to? --> ");
  fgets(input, 128, stdin);
  input[strcspn(input, "\n")] = '\0';

  // Let them attach to stdout to be nice
  FILE *append;
  if(!strcmp(input, "-")) {
    append = stdout;
  } else {
    append = fopen(input, "a");
    if(!append) {
      perror("fopen");
      exit(1);
    }
  }

  // Write it to the file
  fwrite(idv3, 1, offset, append);
  fclose(append);

  return 0;
}
