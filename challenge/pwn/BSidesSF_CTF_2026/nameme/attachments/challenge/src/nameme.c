#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdint.h>

#include <arpa/inet.h>

#define BUFFER_SIZE 1024
#define MAX_HOSTS 128
#define MAX_HOST_ENTRY_LENGTH 128

typedef struct {
  uint8_t qr;
  uint8_t opcode;

  uint8_t aa;
  uint8_t tc;
  uint8_t rd;
  uint8_t ra;

  uint8_t z;
  uint8_t ad;
  uint8_t cd;
  uint8_t rcode;
} dns_flags_t;

typedef struct {
  uint16_t id;
  uint16_t flags;
  uint16_t qdcount;
  uint16_t ancount;
  uint16_t nscount;
  uint16_t arcount;
} dns_t;

typedef struct {
  char name[BUFFER_SIZE];
  uint16_t type;
  uint16_t class;
} dns_question_t;

typedef struct {
  uint16_t name_ptr;
  uint16_t type;
  uint16_t class;
  uint32_t address;
} dns_answer_t;

typedef struct {
  // The start of the buffer
  uint8_t *buffer;

  // Where we're currently processing
  uint8_t *read_pointer;

  // Sometimes we need to move the read_pointer to another part of the message,
  // this stores the original one
  uint8_t *stored_read_pointer;

  // The end of the buffer, to prevent overflows
  uint8_t *end;
} buffer_t;

#define disable_buffering(_fd) setvbuf(_fd, NULL, _IONBF, 0)

typedef struct {
  char hostname[MAX_HOST_ENTRY_LENGTH];
  uint32_t ip;
} host_entry_t;
host_entry_t DATABASE[MAX_HOSTS];
size_t host_entry_count;

void load_database(char *filename) {
  FILE *f = fopen(filename, "r");
  if(!f) {
    fprintf(stderr, "ERROR: Missing or unable to open the database: %s\n", filename);
    exit(1);
  }

  char buffer[MAX_HOST_ENTRY_LENGTH];
  while(fgets(buffer, MAX_HOST_ENTRY_LENGTH, f)) {
    buffer[strlen(buffer) - 1] = '\0'; // Remove the newline
    // fprintf(stderr, "Parsing line: %s\n", buffer);
    char *hostname = strtok(buffer, " ");
    strcpy(DATABASE[host_entry_count].hostname, hostname);

    char *ip = strtok(NULL, " ");
    struct in_addr addr;
    inet_pton(AF_INET, ip, &addr);
    // fprintf(stderr, "IP address: %08x\n", addr.s_addr);
    DATABASE[host_entry_count].ip = addr.s_addr;

    host_entry_count++;
  }
  // fprintf(stderr, "Loaded entry count: %ld\n", host_entry_count);
}

uint16_t read_u16(buffer_t *buffer) {
  if(buffer->read_pointer + 2 >= buffer->end) {
    // fprintf(stderr, "Overflow B!\n");
    return -1;
  }

  uint16_t ret = htons(*((uint16_t *)buffer->read_pointer));
  buffer->read_pointer += 2;

  return ret;
}

void write_u16(buffer_t *buffer, uint16_t val) {
  if(buffer->read_pointer + 2 >= buffer->end) {
    // fprintf(stderr, "Overflow E!\n");
    return;
  }

  *((uint16_t *)buffer->read_pointer) = ntohs(val);
  buffer->read_pointer += 2;
}

void write_u32(buffer_t *buffer, uint32_t val) {
  if(buffer->read_pointer + 4 >= buffer->end) {
    // fprintf(stderr, "Overflow F!\n");
    return;
  }

  *((uint32_t *)buffer->read_pointer) = ntohl(val);
  buffer->read_pointer += 4;
}

uint32_t get_answer(buffer_t *buffer) {
  dns_question_t question;
  memset(&question, 0, sizeof(dns_question_t));
  question.class = -1;
  question.type = -1;
  // fprintf(stderr, "Question.name -> %p\n", question.name);

  // The offset into the name
  register size_t question_length = 0;

  // Label is the 8-bit size of the current section
  register uint8_t label;

  buffer->stored_read_pointer = NULL;
  for(label = *buffer->read_pointer++; label; label = *buffer->read_pointer++) {
    // fprintf(stderr, "Label: 0x%02x (%d) @ %ld - %s\n", label, label, question_length, buffer->read_pointer - 1);
    // Pointer label
    if((label & 0xC0) == 0xC0) {
      uint16_t ptr = 0x3FFF & ((label << 8) | *buffer->read_pointer++);
      // fprintf(stderr, "Jumping to 0x%02x (%d)\n", ptr, ptr);

      // If this is the first pointer, keep track of where we started
      if(buffer->stored_read_pointer == NULL) {
        buffer->stored_read_pointer = buffer->read_pointer;
      }

      buffer->read_pointer = buffer->buffer + ptr;
    } else if(label > 0x7F) {
      fprintf(stderr, "Illegal label: 0x%02x\n", label);
      exit(1);
    } else {
      if((buffer->read_pointer + label) >= buffer->end) {
        return 0;
      }
      memcpy(question.name + question_length, buffer->read_pointer, label);

      buffer->read_pointer += label;
      question_length += label;

      // fprintf(stderr, "%p %ld\n", question.name, question_length);
      question.name[question_length++] = '.';
      question.name[question_length] = '\0';
    }
  }
  // fprintf(stderr, "Label: 0x%02x (%d)\n", label, label);
  // Remove the trailing '.'
  question.name[--question_length] = '\0';

  if(buffer->stored_read_pointer) {
    buffer->read_pointer = buffer->stored_read_pointer;
  }

  if((buffer->read_pointer + 4) >= buffer->end) {
    return 0;
  }
  question.type = read_u16(buffer);
  question.class = read_u16(buffer);

  fprintf(stderr, "Question received: %s\n", question.name);

  size_t i;
  for(i = 0; i < host_entry_count; i++) {
    if(!strcmp(DATABASE[i].hostname, question.name)) {
      // Found it!
      fprintf(stderr, "  Answer -> %08x!\n", DATABASE[i].ip);
      return DATABASE[i].ip;
    }
  }

  fprintf(stderr, "  Host not found!\n");

  return 0;
}

int main(int argc, char *argv[]) {
  disable_buffering(stdout);
  disable_buffering(stderr);
  alarm(10);

  load_database(argc > 1 ? argv[1] : "host.list");
  // fprintf(stderr, "Host entry count: %ld\n", host_entry_count);

  buffer_t *buffer = malloc(sizeof(buffer_t));
  buffer->buffer = malloc(BUFFER_SIZE);
  buffer->read_pointer = buffer->buffer;
  buffer->stored_read_pointer = 0;
  buffer->end = buffer->buffer + BUFFER_SIZE;

  ssize_t i;

  // fprintf(stderr, "Waiting for debugger...\n");
  // sleep(2);

  ssize_t size = read(fileno(stdin), buffer->buffer, BUFFER_SIZE);
  // fprintf(stderr, "Size of message: %ld\n", size);
  buffer->end = buffer->buffer + size;
  dns_t dns;

  // for(i = 0; i < size; i++) {
  //   fprintf(stderr, "%02x ", buffer->buffer[i]);
  // }
  // fprintf(stderr, "\n");

  dns.id = read_u16(buffer);
  dns.flags = read_u16(buffer);

  // Query response
  dns_flags_t parsed_flags;
  parsed_flags.qr     = (dns.flags & 0x8000) != 0;         /* bit 15 */
  if(parsed_flags.qr) {
    fprintf(stderr, "ERROR: Received a response!\n");
    exit(1);
  }

  parsed_flags.opcode = (dns.flags >> 11) & 0x0f;      /* bits 14–11 */
  if(parsed_flags.opcode) {
    fprintf(stderr, "ERROR: Unexpected opcode: %d\n", parsed_flags.opcode);
    exit(1);
  }

  parsed_flags.aa     = (dns.flags & 0x0400) != 0;         /* bit 10 */
  parsed_flags.tc     = (dns.flags & 0x0200) != 0;         /* bit 9 */
  parsed_flags.rd     = (dns.flags & 0x0100) != 0;         /* bit 8 */
  parsed_flags.ra     = (dns.flags & 0x0080) != 0;         /* bit 7 */

  parsed_flags.z      = (dns.flags & 0x0040) != 0;         /* bit 6 (should be 0) */
  parsed_flags.ad     = (dns.flags & 0x0020) != 0;         /* bit 5 */
  parsed_flags.cd     = (dns.flags & 0x0010) != 0;         /* bit 4 */

  parsed_flags.rcode = dns.flags & 0x0f;               /* bits 3–0 */
  if(parsed_flags.rcode) {
    fprintf(stderr, "ERROR: Unexpected rcode: %d\n", parsed_flags.rcode);
    exit(1);
  }

  dns.qdcount = read_u16(buffer);
  dns.ancount = read_u16(buffer);
  dns.nscount = read_u16(buffer);
  dns.arcount = read_u16(buffer);

  dns_answer_t *answers = malloc(sizeof(dns_answer_t) * dns.qdcount);
  size_t current_answer = 0;

  fprintf(stderr, "Questions: %d\n", dns.qdcount);
  uint16_t error = 0;

  for(i = 0; i < dns.qdcount; i++) {
    fprintf(stderr, "\n** Question %ld\n", i);
    size_t starting_name_ptr = buffer->read_pointer - buffer->buffer;
    uint32_t answer = get_answer(buffer);

    if(buffer->read_pointer >= buffer->end) {
      // fprintf(stderr, "Out of data!\n");
      exit(1);
    }

    if(answer) {
      answers[current_answer].name_ptr = starting_name_ptr;
      answers[current_answer].type = 1;
      answers[current_answer].class = 1;
      answers[current_answer].address = htonl(answer);
      current_answer++;
    } else {
      // Didn't find!
      error |= 0x0003;
    }
  }
  // fprintf(stderr, "\n");

  // We're gonna use this to skip over the questions (kind of an ugly trick :) )
  buffer->stored_read_pointer = buffer->read_pointer;

  // Now we're writing to the packet - go to the beginning!
  buffer->read_pointer = buffer->buffer;

  // DNS header
  write_u16(buffer, dns.id);
  write_u16(buffer, 0x8000 | error); // Response + error
  write_u16(buffer, dns.qdcount);
  write_u16(buffer, current_answer);
  write_u16(buffer, 0);
  write_u16(buffer, 0);

  // Leave the questions untouched
  buffer->read_pointer = buffer->stored_read_pointer;

  // Write the answers
  for(i = 0; i < current_answer; i++) {
    write_u16(buffer, 0xc000 | answers[i].name_ptr);

    // We only have one class/type
    write_u16(buffer, 1);
    write_u16(buffer, 1);
    write_u32(buffer, 0x00001000); // ttl
    write_u16(buffer, 4); // data length
    write_u32(buffer, answers[i].address);
  }

  write(fileno(stdout), buffer->buffer, buffer->read_pointer - buffer->buffer);

  free(buffer);

  return 0;
}
