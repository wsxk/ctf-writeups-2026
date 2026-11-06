#define _GNU_SOURCE

#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>

#define disable_buffering(_fd) setvbuf(_fd, NULL, _IONBF, 0)

#define LINE_LENGTH 128
#define CODE_START_LENGTH 64
#define CODE_MAX_SIZE 0x00100000
#define LOOP_DEPTH 4

typedef enum {
  COMMAND_COMMENT = -1, // sorta hidden.. used for non-commands

  COMMAND_LET, // let $VAR <int32>
  COMMAND_LETV, // let $VAR #VAR2
  COMMAND_ADD, // add $VAR <int32>
  COMMAND_ADDV, // addv $VAR $VAR2
  COMMAND_SUB, // sub $VAR <int32>
  COMMAND_SUBV, // subv $VAR $VAR2
  COMMAND_MUL, // mul $var <int32>
  COMMAND_PRINT, // print $VAR
  COMMAND_PRINTCHAR, // print $VAR
  COMMAND_LOOP, // loop $VAR ... endloop
  COMMAND_ENDLOOP,
  COMMAND_IF, // if $var ... endif
  COMMAND_ENDIF,
  COMMAND_EXIT, // exit <int32>
  // COMMAND_NOP, // nop
  // COMMAND_DEBUG, // int 3
} keyword_t;

typedef enum {
  VARIABLE_A,
  VARIABLE_B,
  VARIABLE_C,
  VARIABLE_D,
} variable_t;

typedef struct {
  variable_t variable;
  uint32_t immediate;
} args_let_t;

typedef struct {
  variable_t variable1;
  variable_t variable2;
} args_letv_t;

typedef struct {
  variable_t variable;
  uint32_t immediate;
} args_add_t;

typedef struct {
  variable_t variable1;
  variable_t variable2;
} args_addv_t;

typedef struct {
  variable_t variable;
  uint32_t immediate;
} args_sub_t;

typedef struct {
  variable_t variable1;
  variable_t variable2;
} args_subv_t;

typedef struct {
  variable_t variable;
  uint32_t immediate;
} args_mul_t;

typedef struct {
  variable_t variable;
} args_print_t;

typedef struct {
  variable_t variable;
} args_printchar_t;

typedef struct {
  variable_t variable;
} args_loop_t;

typedef struct {
} args_endloop_t;

typedef struct {
  variable_t variable;
} args_if_t;

typedef struct {
} args_endif_t;

typedef struct {
  int32_t immediate;
} args_exit_t;

// typedef struct {
// } args_nop_t;

// typedef struct {
// } args_debug_t;

typedef union {
  args_let_t args_let;
  args_letv_t args_letv;
  args_add_t args_add;
  args_addv_t args_addv;
  args_sub_t args_sub;
  args_subv_t args_subv;
  args_mul_t args_mul;
  args_print_t args_print;
  args_printchar_t args_printchar;
  args_loop_t args_loop;
  args_endloop_t args_endloop;
  args_if_t args_if;
  args_endif_t args_endif;
  args_exit_t args_exit;
  // args_nop_t args_nop;
  // args_debug_t args_debug;
} args_t;

typedef struct {
  int32_t line_number;
  keyword_t keyword;
  args_t args;
} command_t;

typedef struct {
  uint32_t line_number;
  char line_copy[LINE_LENGTH];

  uint8_t in_loop;
  variable_t loop_variable[LOOP_DEPTH];
  uint32_t start_of_loop[LOOP_DEPTH];

  uint8_t in_if;
  uint32_t if_address[LOOP_DEPTH];

  uint8_t *code_buffer;
  uint32_t code_offset;
  uint32_t code_max_length;
} state_t;

void error(state_t *state, char *message) {
  printf("ERROR: %s (line %d: \"%s\")\n", message, state->line_number, state->line_copy);
  abort();
}

char *next_token_or_exit(state_t *state) {
  char *result = strtok(NULL, " ");
  if(result) {
    return result;
  } else {
    error(state, "Missing token");
    exit(1);
  }
}

int32_t next_immediate(state_t *state) {
  char *token = next_token_or_exit(state);

  char *end = NULL;
  errno = 0;
  long val = strtol(token, &end, 10);

  if (end == token) {
    error(state, "Missing immediate value");
  }

  if (*end != '\0') {
    error(state, "Bad immediate value");
  }

  // if (errno == ERANGE || val < INT32_MIN || val > INT32_MAX) {
  //   error(state, "Immediate value out of range");
  // }

  return (int32_t) val;
}

variable_t next_variable(state_t *state) {
  char *token = next_token_or_exit(state);
  if(strlen(token) != 2) {
    error(state, "Illegal variable: must be 2 characters");
  }

  if(token[0] != '$') {
    error(state, "Illegal variable: must start with $");
  }

  switch(toupper(token[1])) {
    case 'A': return VARIABLE_A;
    case 'B': return VARIABLE_B;
    case 'C': return VARIABLE_C;
    case 'D': return VARIABLE_D;
    default: error(state, "Illegal variable");
  }

  return -1; // impossible
}

// void print_immediate(state_t *state, int32_t immediate) {
//   printf("%d", immediate);
// }

// void print_variable(state_t *state, variable_t variable) {
//   switch(variable) {
//     case VARIABLE_A: printf("$A"); break;
//     case VARIABLE_B: printf("$B"); break;
//     case VARIABLE_C: printf("$C"); break;
//     case VARIABLE_D: printf("$D"); break;
//     default: error(state, "Unknown variable");
//   }
// }

// void print_command(state_t *state, command_t *command, uint8_t indent) {
//   printf("%3d: ", command->line_number);

//   if(command->keyword == COMMAND_ENDIF || command->keyword == COMMAND_ENDLOOP) {
//     indent--;
//   }

//   int i;
//   for(i = 0; i < indent; i++) {
//     printf("  ");
//   }

//   switch(command->keyword) {
//     case COMMAND_COMMENT:
//       break;

//     case COMMAND_LET:
//       print_variable(state, command->args.args_let.variable);
//       printf(" = ");
//       print_immediate(state, command->args.args_let.immediate);
//       break;

//     case COMMAND_LETV:
//       print_variable(state, command->args.args_letv.variable1);
//       printf(" = ");
//       print_variable(state, command->args.args_letv.variable2);
//       break;

//     case COMMAND_ADD: // add $VAR <int32>
//       print_variable(state, command->args.args_add.variable);
//       printf(" += ");
//       print_immediate(state, command->args.args_add.immediate);

//       break;

//     case COMMAND_ADDV: // addv $VAR $VAR2
//       print_variable(state, command->args.args_addv.variable1);
//       printf(" += ");
//       print_variable(state, command->args.args_addv.variable2);

//       break;

//     case COMMAND_SUB: // sub $VAR <int32>
//       print_variable(state, command->args.args_sub.variable);
//       printf(" -= ");
//       print_immediate(state, command->args.args_sub.immediate);

//       break;

//     case COMMAND_SUBV: // subv $VAR $VAR2
//       printf("SUBV ");
//       print_variable(state, command->args.args_subv.variable1);
//       printf(" -= ");
//       print_variable(state, command->args.args_subv.variable2);

//       break;

//     case COMMAND_MUL: // mul $VAR <int32>
//       print_variable(state, command->args.args_sub.variable);
//       printf(" *= ");
//       print_immediate(state, command->args.args_sub.immediate);

//       break;

//     case COMMAND_PRINT: // print $VAR
//       printf("printf(\"%%d\\n\", ");
//       print_variable(state, command->args.args_print.variable);
//       printf(")");

//       break;

//     case COMMAND_PRINTCHAR: // print $VAR
//       printf("printf(\"%%c\\n\", ");
//       print_variable(state, command->args.args_printchar.variable);
//       printf(")");

//       break;

//     case COMMAND_LOOP: // loop $VAR ... endloop
//       printf("while(");
//       print_variable(state, command->args.args_loop.variable);
//       printf("-- > 0) {");

//       break;

//     case COMMAND_ENDLOOP:
//       printf("}");

//       break;

//     case COMMAND_IF: // if $var ... endif
//       printf("if(");
//       print_variable(state, command->args.args_if.variable);
//       printf(") {");

//       break;

//     case COMMAND_ENDIF:
//       printf("}");

//       break;

//     case COMMAND_EXIT: // exit <int32>
//       printf("exit(");
//       print_immediate(state, command->args.args_exit.immediate);
//       printf(")");

//       break;

//     // case COMMAND_NOP: // nop
//     //   printf("nop");

//     //   break;

//     // case COMMAND_DEBUG: // int 3
//     //   printf("int 3");

//     //   break;

//     default:
//       error(state, "No code to print command!");
//   }
//   printf("\n");
// }

uint8_t read_line(state_t *state, command_t *command) {
  command->line_number = state->line_number++;

  // Get the line
  char real_line[LINE_LENGTH];
  if(!fgets(real_line, LINE_LENGTH - 1, stdin)) {
    return 0;
  }

  real_line[LINE_LENGTH - 1] = '\0';

  // Remove end whitespace
  while(strlen(real_line) > 0 && isspace(real_line[strlen(real_line) - 1])) {
    real_line[strlen(real_line) - 1] = '\0';
  }

  // Remove beginning whitespace
  char *line = real_line;
  while(strlen(line) > 0 && isspace(line[0])) {
    line++;
  }

  // Make a copy of it
  strncpy(state->line_copy, line, LINE_LENGTH - 1);

  if(strlen(line) == 0 || line[0] == '#' || line[0] == ';') {
    command->keyword = COMMAND_COMMENT;
    return 1;
  }

  // Start tokenizing
  char *command_name = strtok(line, " ");

  // Identify/parse the command
  if(!strcasecmp(command_name, "let")) {
    command->keyword = COMMAND_LET;
    command->args.args_let.variable = next_variable(state);
    command->args.args_let.immediate = next_immediate(state);
  } else if(!strcasecmp(command_name, "letv")) {
    command->keyword = COMMAND_LETV;
    command->args.args_letv.variable1 = next_variable(state);
    command->args.args_letv.variable2 = next_variable(state);
  } else if(!strcasecmp(command_name, "add")) {
    command->keyword = COMMAND_ADD;
    command->args.args_add.variable = next_variable(state);
    command->args.args_add.immediate = next_immediate(state);
  } else if(!strcasecmp(command_name, "addv")) {
    command->keyword = COMMAND_ADDV;
    command->args.args_addv.variable1 = next_variable(state);
    command->args.args_addv.variable2 = next_variable(state);
  } else if(!strcasecmp(command_name, "sub")) {
    command->keyword = COMMAND_SUB;
    command->args.args_sub.variable = next_variable(state);
    command->args.args_sub.immediate = next_immediate(state);
  } else if(!strcasecmp(command_name, "subv")) {
    command->keyword = COMMAND_SUBV;
    command->args.args_subv.variable1 = next_variable(state);
    command->args.args_subv.variable2 = next_variable(state);
  } else if(!strcasecmp(command_name, "mul")) {
    command->keyword = COMMAND_MUL;
    command->args.args_mul.variable = next_variable(state);
    command->args.args_mul.immediate = next_immediate(state);
  } else if(!strcasecmp(command_name, "print")) {
    command->keyword = COMMAND_PRINT;
    command->args.args_print.variable = next_variable(state);
  } else if(!strcasecmp(command_name, "printchar")) {
    command->keyword = COMMAND_PRINTCHAR;
    command->args.args_printchar.variable = next_variable(state);
  } else if(!strcasecmp(command_name, "loop")) {
    command->keyword = COMMAND_LOOP;
    command->args.args_loop.variable = next_variable(state);
  } else if(!strcasecmp(command_name, "endloop")) {
    command->keyword = COMMAND_ENDLOOP;
  } else if(!strcasecmp(command_name, "if")) {
    command->keyword = COMMAND_IF;
    command->args.args_if.variable = next_variable(state);
  } else if(!strcasecmp(command_name, "endif")) {
    command->keyword = COMMAND_ENDIF;
  } else if(!strcasecmp(command_name, "exit")) {
    command->keyword = COMMAND_EXIT;
    command->args.args_exit.immediate = next_immediate(state);
  // } else if(!strcasecmp(command_name, "nop")) {
  //   command->keyword = COMMAND_NOP;
  // } else if(!strcasecmp(command_name, "debug")) {
  //   command->keyword = COMMAND_DEBUG;
  } else {
    error(state, "Unknown command!");
  }

  return 1;
}

void reserve_space(state_t *state, int32_t length) {
  while(state->code_offset + length >= state->code_max_length) {
    uint32_t old_length = state->code_max_length;
    state->code_max_length *= 2;

    // printf("WARNING: Code is getting a bit big, remapping %d -> %d!\n", old_length, state->code_max_length);
    if(state->code_max_length > CODE_MAX_SIZE) {
      error(state, "Your code got too long! There's a (pretty big) limit!");
    }
    state->code_buffer = mremap(state->code_buffer, old_length, state->code_max_length, MREMAP_MAYMOVE);
    if(!state->code_buffer) {
      error(state, "Failed to remap memory!");
    }
  }
}

void add_u8(state_t *state, uint8_t u8) {
  reserve_space(state, 1);
  state->code_buffer[state->code_offset++] = u8;
}

void add_u16(state_t *state, uint16_t u16) {
  reserve_space(state, 2);
  memcpy(&state->code_buffer[state->code_offset], &u16, 2);
  state->code_offset += 2;
}

void add_u32(state_t *state, uint32_t u32) {
  reserve_space(state, 4);
  memcpy(&state->code_buffer[state->code_offset], &u32, 4);
  state->code_offset += 4;
}

void add_u64(state_t *state, uint64_t u64) {
  reserve_space(state, 8);
  memcpy(&state->code_buffer[state->code_offset], &u64, 8);
  state->code_offset += 8;
}

uint8_t reg_mask(state_t *state, variable_t variable) {
  switch(variable) {
    case VARIABLE_A: return 0x00;
    case VARIABLE_B: return 0x01;
    case VARIABLE_C: return 0x02;
    case VARIABLE_D: return 0x03;
    default: error(state, "Unknown variable!");
  }

  return -1; // impossible
}

void mov_rax_u32(state_t *state, uint32_t immediate) {
  add_u8(state, 0xb8);
  add_u32(state, immediate);
}

void mov_rdi_reg(state_t *state, variable_t variable) {
  // mov rdi, $VAR
  add_u8(state, 0x4c);
  add_u8(state, 0x89);
  add_u8(state, 0xe7 | (reg_mask(state, variable) << 3));
}

void mov_rdi_u32(state_t *state, uint32_t immediate) {
  add_u8(state, 0xbf);
  add_u32(state, immediate);
}

void mov_rdi_u64(state_t *state, uint64_t immediate) {
  add_u8(state, 0x48);
  add_u8(state, 0xbf);
  add_u64(state, immediate);
}

void mov_rsi_reg(state_t *state, variable_t variable) {
  // mov rsi, $VAR
  add_u8(state, 0x4c);
  add_u8(state, 0x89);
  add_u8(state, 0xe6 | (reg_mask(state, variable) << 3));
}

void mov_rsi_u32(state_t *state, uint32_t immediate) {
  add_u8(state, 0xbe);
  add_u32(state, immediate);
}

void call(state_t *state, void *function) {
  // mov rax, func
  add_u8(state, 0x48);
  add_u8(state, 0xb8);
  add_u64(state, (uint64_t) function);

  // call rax
  add_u8(state, 0xff);
  add_u8(state, 0xd0);
}

int main() {
  disable_buffering(stdout);
  disable_buffering(stderr);

  printf("WELCOME TO RUGDOCTOR! The secure JIT sandbox application!\n");
  printf("\n");
  printf("GIVE ME YOUR CODE! See README.md for instructions! End with ctrl-d\n");
  printf("\n");
  printf("GO\n");

  // Set up the state
  state_t state;
  state.line_number = 1;
  state.in_loop = 0;
  state.in_if = 0;
  state.code_max_length = CODE_START_LENGTH;
  state.code_buffer = mmap(NULL, CODE_START_LENGTH, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if(!state.code_buffer) {
    error(&state, "Failed to map memory!");
  }

  // Start by clearing registers
  memcpy(state.code_buffer, "\x48\x31\xC0", 3);
  state.code_offset = 3;

  command_t command;

  while(read_line(&state, &command)) {

    // print_command(&state, &command, state.in_loop + state.in_if);

    switch(command.keyword) {
      case COMMAND_COMMENT:
        break;

      case COMMAND_LET:
        // mov <reg>, <immediate>
        add_u8(&state, 0x41);
        add_u8(&state, 0xbc | reg_mask(&state, command.args.args_let.variable));
        add_u32(&state, command.args.args_let.immediate);
        break;

      case COMMAND_LETV:
        // mov <reg>, <immediate>
        add_u8(&state, 0x4d);
        add_u8(&state, 0x89);
        add_u8(&state, 0xe4 |
          (reg_mask(&state, command.args.args_letv.variable2) << 3)
          | (reg_mask(&state, command.args.args_letv.variable1))
        );
        break;

      case COMMAND_ADD:
        add_u8(&state, 0x49);
        add_u8(&state, 0x81);
        add_u8(&state, 0xc4 | (reg_mask(&state, command.args.args_add.variable)));
        add_u32(&state, command.args.args_add.immediate);
        break;

      case COMMAND_ADDV:
        add_u8(&state, 0x4d);
        add_u8(&state, 0x01);
        add_u8(&state, 0xe4 |
          (reg_mask(&state, command.args.args_addv.variable2) << 3)
          | (reg_mask(&state, command.args.args_addv.variable1))
        );
        break;

      case COMMAND_SUB:
        add_u8(&state, 0x49);
        add_u8(&state, 0x81);
        add_u8(&state, 0xec | (reg_mask(&state, command.args.args_add.variable)));
        add_u32(&state, command.args.args_add.immediate);
        break;

      case COMMAND_SUBV:
        add_u8(&state, 0x4d);
        add_u8(&state, 0x29);
        add_u8(&state, 0xe4 |
          (reg_mask(&state, command.args.args_subv.variable2) << 3)
          | (reg_mask(&state, command.args.args_subv.variable1))
        );
        break;

      case COMMAND_MUL:
        add_u8(&state, 0x4d);
        add_u8(&state, 0x69);
        add_u8(&state, 0xe4 |
          (reg_mask(&state, command.args.args_mul.variable) << 3)
          | (reg_mask(&state, command.args.args_mul.variable))
        );
        add_u32(&state, command.args.args_mul.immediate);
        break;

      case COMMAND_PRINT:
        // mov rdi, "%s"
        mov_rdi_u64(&state, (uint64_t)&"%d\n");

        // mov rsi, $VAR
        mov_rsi_reg(&state, command.args.args_print.variable);

        call(&state, printf);
        break;

      case COMMAND_PRINTCHAR:
        // mov rdi, "%s"
        mov_rdi_u64(&state, (uint64_t)"%c");

        // mov rsi, $VAR
        mov_rsi_reg(&state, command.args.args_let.variable);

        call(&state, printf);
        break;

      case COMMAND_LOOP:
        if(state.in_loop >= LOOP_DEPTH) {
          error(&state, "Too many nested loops!");
        }

        state.loop_variable[state.in_loop] = command.args.args_loop.variable;
        state.start_of_loop[state.in_loop] = state.code_offset;
        state.in_loop += 1;

        break;

      case COMMAND_ENDLOOP:
        if(state.in_loop == 0) {
          error(&state, "ENDLOOP without LOOP!");
        }

        state.in_loop -= 1;

        // dec <reg>
        add_u8(&state, 0x49);
        add_u8(&state, 0xff);
        add_u8(&state, 0xcc | reg_mask(&state, state.loop_variable[state.in_loop]));

        // jz <16-bit>
        int32_t loop_jump = ((int16_t)state.start_of_loop[state.in_loop] - (int16_t)state.code_offset - 6);
        add_u8(&state, 0x0f);
        add_u8(&state, 0x8f);
        add_u32(&state, (int32_t) loop_jump);

        break;

      case COMMAND_IF:
        if(state.in_if >= LOOP_DEPTH) {
          error(&state, "Too many nested ifs!");
        }

        // test <var>, <var>
        add_u8(&state, 0x4d);
        add_u8(&state, 0x85);
        add_u8(&state, 0xe4 |
          (reg_mask(&state, command.args.args_if.variable) << 3)
          | (reg_mask(&state, command.args.args_if.variable))
        );

        // jz, <placeholder>
        add_u8(&state, 0x0f);
        add_u8(&state, 0x84);

        state.if_address[state.in_if] = state.code_offset;
        state.in_if += 1;

        add_u32(&state, 0x5a5a5a5a);

        break;

      case COMMAND_ENDIF:
        if(state.in_if == 0) {
          error(&state, "ENDIF without IF!");
        }

        state.in_if -= 1;

        // Update the start of the if
        int32_t if_jump = ((uint16_t)state.code_offset - (uint16_t)state.if_address[state.in_if] - 4);
        memcpy(state.code_buffer + state.if_address[state.in_if], &if_jump, 4);

        break;

      case COMMAND_EXIT:
        // mov rdi, var
        mov_rdi_u32(&state, command.args.args_exit.immediate);

        // call exit
        call(&state, exit);

        break;

      // case COMMAND_NOP:
      //   add_u8(&state, 0x90);
      //   break;

      // case COMMAND_DEBUG:
      //   add_u8(&state, 0xCC);
      //   break;

      default:
        error(&state, "Unknown command!");
    }
  }

  if(state.in_if) {
    error(&state, "Unfinished IF statement!");
  }

  if(state.in_loop) {
    error(&state, "Unfinished LOOP statement!");
  }

  // Set the final byte to 0xcc in case they forget to exit cleanly
  add_u8(&state, 0xcc);

  // FILE *f = fopen("output.bin", "wb");
  // fwrite(state.code_buffer, 1, state.code_offset, f);
  // fclose(f);

  // printf("Done!\n");
  // printf("----------------\n");

  alarm(10);

  printf("Executing your code!\n");
  printf("------------------------\n");
  __asm__ volatile(
    "xor rbx, rbx\n"
    "xor rcx, rcx\n"
    "xor rdx, rdx\n"
    "xor rsi, rsi\n"
    "xor rdi, rdi\n"
    "xor rbp, rbp\n"
    "jmp %0\n"
    :
    : "r"(state.code_buffer)
    :
  );

  return 0;
}
