#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define disable_buffering(_fd) setvbuf(_fd, NULL, _IONBF, 0)
#define STR_SIZE 32


int main(int argc, char *argv[]) {
  uint8_t data[256];
  char rw[STR_SIZE];

  char offset_str[STR_SIZE];
  uint8_t *offset;

  char size_str[STR_SIZE];
  register uint32_t size;

  disable_buffering(stdout);
  disable_buffering(stderr);

  printf("Instructions:\n");
  printf("* Send 'r' (read), 'h' (read in hex), or 'w' (write), followed by a newline\n");
  printf("* Send a 64-bit offset (in hex), followed by a newline\n");
  printf("* Send a 32-bit length value (in hex), followed by a newline\n");
  printf("\n");
  printf("If reading, exactly (length) bytes will be printed (no newline or anything)\n");
  printf("If reading hex, exactly (length) bytes will be printed as hex (ending up at length*2 size)\n");
  printf("If writing, send exactly (length) binary bytes and they will be written to the offset\n");
  printf("\n");
  printf("Note: this does respect memory protections (ie, you can't write to code sections)\n");
  printf("\n");
  printf("GO\n");
  fflush(stdout);

  for(; ;) {
#ifdef DEBUG
    fprintf(stderr, "Getting command\n");
#endif
    if(!fgets(rw, STR_SIZE, stdin))
      break;

#ifdef DEBUG
    fprintf(stderr, "Command: %s", rw);
#endif

    if(rw[0] != 'r' && rw[0] != 'w' && rw[0] != 'h') {
#ifdef DEBUG
      fprintf(stderr, "Unknown command; breaking\n");
#endif
      break;
    }

    if(!fgets(offset_str, STR_SIZE, stdin))
      break;

#ifdef DEBUG
    fprintf(stderr, "Offset: %s\n", offset_str);
#endif

    if(!fgets(size_str, STR_SIZE, stdin))
      break;

#ifdef DEBUG
    fprintf(stderr, "Size: %s\n", size_str);
#endif

    offset = (uint8_t*)strtoll(offset_str, NULL, 16);
    size = (uint32_t*)strtol(size_str, NULL, 16);

    if(rw[0] == 'r') {
#ifdef DEBUG
      fprintf(stderr, "Reading %d bytes from %p\n", size, offset);
#endif
      write(fileno(stdout), offset, size);
    } else if(rw[0] == 'h') {
#ifdef DEBUG
      fprintf(stderr, "Reading %d hex from %p\n", size, offset);
#endif
      memcpy(data, offset, size);

      int i;
#ifdef DEBUG
      fprintf(stderr, "Looping through 0x%x bytes!\n", size);
#endif
      for(i = 0; i < size; i++) {
        fprintf(stdout, "%02x", data[i]);
      }
      fflush(stdout);
#ifdef DEBUG
      fprintf(stderr, "Done reading\n");
#endif
    } else if(rw[0] == 'w') {
#ifdef DEBUG
      fprintf(stderr, "Writing %d bytes to %p\n", size, offset);
#endif
      int i = 0;
      while(i < size) {
        int new_data = fread(offset + i, 1, size - i, stdin);
        if(new_data == 0) {
#ifdef DEBUG
          fprintf(stderr, "Connection closed!\n");
#endif
          exit(0);
        }
        i += new_data;
      }
    } else {
      break;
    }
  }

  // printf("DEBUG BREAKPOINT!!\n");
  // __asm__("int $3");
  printf("Good bye!\n");

  return 0;
}

// void secret_function() {
//   char buffer[128];

//   printf("\n");
//   printf("I'm not called from anywhere but I'm still very important!\n");
//   FILE *f = fopen("flag.txt", "r");
//   if(f) {
//     fgets(buffer, 128, f);
//     printf("%s\n", buffer);
//   } else {
//     printf("Couldn't find flag file! Please report: flag.txt\n");
//   }

//   exit(0);
// }
