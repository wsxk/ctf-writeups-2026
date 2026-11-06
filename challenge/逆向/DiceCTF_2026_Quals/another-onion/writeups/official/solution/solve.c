#define _GNU_SOURCE
#include <assert.h>
#include <fcntl.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/ucontext.h>
#include <sys/user.h>
#include <unistd.h>
#include <wait.h>

#include "generated_config.h"

#define DEBUG 0

unsigned char read_code[] = {0x52, 0x51, 0x48, 0xc7, 0xc2, 0x0,  0x0,  0x0,
                             0x10, 0x48, 0x8b, 0xa,  0x88, 0xe,  0x48, 0xc1,
                             0xe9, 0x8,  0x48, 0x89, 0xa,  0x48, 0xc7, 0xc0,
                             0x1,  0x0,  0x0,  0x0,  0x59, 0x5a, 0xc3};
typedef void (*run_func_t)(void *);

#define MAX_BACKUP_PAGES 64
#define SHARED_CONTEXT_SIZE 0x1000
#define PAGE_BACKUP_SIZE ((uint64_t)MAX_BACKUP_PAGES * 0x1000)

struct BackupPage {
  void *original_page;
  void *backup_page;
};

struct SharedContext {
  uint64_t next_read;
  uint64_t backup_page_count;
  uint64_t next_code_start;
  uint64_t attempt_active;
  uint64_t attempt_failed;
  int next_code_breakpoint_original;
  mcontext_t stored_target_context;
  struct _libc_fpstate stored_target_fpregs __attribute__((aligned(16)));
  mcontext_t stored_driver_context;
  struct _libc_fpstate stored_driver_fpregs __attribute__((aligned(16)));
  mcontext_t stored_target_context_attempt;
  struct _libc_fpstate stored_target_context_attempt_fpregs
      __attribute__((aligned(16)));
  struct BackupPage backup_pages[MAX_BACKUP_PAGES];
};
_Static_assert(sizeof(struct SharedContext) <= SHARED_CONTEXT_SIZE,
               "SharedContext must fit within SHARED_CONTEXT_SIZE");

struct AttemptResult {
  int disass;
  uint16_t input;
};

struct SharedContext *const SHARED_CONTEXT = (struct SharedContext *)0x10000000;
uint8_t *const PAGE_BACKUP_ADDR = (uint8_t *)0x20000000;
uint8_t *const CUSTOM_CODE_ADDR = (uint8_t *)0x30000000;
uint8_t *const TARGET_STACK_ADDR = (uint8_t *)0x40000000;
uint8_t *const TARGET_STACK_BACKUP_ADDR = (uint8_t *)0x50000000;
uint64_t const TARGET_STACK_SIZE = 0x100000;
void *const TRAMPOLINE_PAGE = (void *)0x60000000;
uint64_t *const TRAMPOLINE_TO_TARGET_HELPER = (uint64_t *)0x60000000;
uint64_t *const TRAMPOLINE_TO_SETUP_INITIAL_CONTEXT_HELPER =
    (uint64_t *)0x60000008;
struct AttemptResult *const ATTEMPT_RESULT = (struct AttemptResult *)0x70000000;
uint8_t const ILLCODE_READ_TRAP = 0xc4;
uint8_t const ILLCODE_START_OF_NEXT_SECTION = 0xd4;
uint64_t const READ_PLT_ADDR = READ_PLT_ADDR_VALUE;
uint64_t const MMAP_PLT_ADDR = MMAP_PLT_ADDR_VALUE;
uint64_t const PUTCHAR_PLT_ADDR = PUTCHAR_PLT_ADDR_VALUE;
uint64_t const TARGET_START_CODE_ADDR = TARGET_START_CODE_ADDR_VALUE;
int const NSEGMENTS = NSEGMENTS_VALUE;

void *const CODE_START = (void *)CODE_START_VALUE;
uint64_t const CODE_START_FILE_OFFSET = CODE_START_FILE_OFFSET_VALUE;
uint64_t const CODE_FILE_SIZE = CODE_FILE_SIZE_VALUE;
uint64_t const CODE_MEM_SIZE = CODE_MEM_SIZE_VALUE;

void *const RODATA_START = (void *)RODATA_START_VALUE;
uint64_t const RODATA_START_FILE_OFFSET = RODATA_START_FILE_OFFSET_VALUE;
uint64_t const RODATA_FILE_SIZE = RODATA_FILE_SIZE_VALUE;
uint64_t const RODATA_MEM_SIZE = RODATA_MEM_SIZE_VALUE;

void *const DATA_START = (void *)DATA_START_VALUE;
uint64_t const DATA_START_FILE_OFFSET = DATA_START_FILE_OFFSET_VALUE;
uint64_t const DATA_FILE_SIZE = DATA_FILE_SIZE_VALUE;
uint64_t const DATA_MEM_SIZE = DATA_MEM_SIZE_VALUE;

void *const CODE_START_PAGE = (void *)((uint64_t)CODE_START & ~0xfff);
uint64_t const CODE_SECTION_PAGE_SIZE =
    (((uint64_t)CODE_START + CODE_MEM_SIZE + 0xfff) & ~0xfff) -
    (uint64_t)CODE_START_PAGE;
void *const RODATA_START_PAGE = (void *)((uint64_t)RODATA_START & ~0xfff);
uint64_t const RODATA_SECTION_PAGE_SIZE =
    (((uint64_t)RODATA_START + RODATA_MEM_SIZE + 0xfff) & ~0xfff) -
    (uint64_t)RODATA_START_PAGE;
void *const DATA_START_PAGE = (void *)((uint64_t)DATA_START & ~0xfff);
uint64_t const DATA_SECTION_PAGE_SIZE =
    (((uint64_t)DATA_START + DATA_MEM_SIZE + 0xfff) & ~0xfff) -
    (uint64_t)DATA_START_PAGE;

uint64_t const FAKE_ADDRS_PTR =
    (uint64_t)TARGET_STACK_ADDR + TARGET_STACK_SIZE - 0x2000;

bool is_code_addr(uint64_t addr) {
  return addr >= (uint64_t)CODE_START &&
         addr < (uint64_t)CODE_START + CODE_MEM_SIZE;
}

bool is_data_addr(uint64_t addr) {
  return addr >= (uint64_t)DATA_START &&
         addr < (uint64_t)DATA_START + DATA_MEM_SIZE;
}

int write_prot_for_addr(uint64_t addr) {
  if (is_code_addr(addr)) {
    return PROT_READ | PROT_WRITE | PROT_EXEC;
  }
  if (is_data_addr(addr)) {
    return PROT_READ | PROT_WRITE;
  }
  return PROT_READ | PROT_WRITE;
}

int restore_prot_for_addr(uint64_t addr) {
  if (is_code_addr(addr)) {
    return PROT_READ | PROT_EXEC;
  }
  if (is_data_addr(addr)) {
    return PROT_READ;
  }
  return PROT_READ;
}

void install_fake_addrs_pointer(void) {
  struct SharedContext *ctx = SHARED_CONTEXT;
  uint64_t rsp = ctx->stored_target_context.gregs[REG_RSP];
  uint64_t slot = rsp + 0x10;
  uint64_t stack_lo = (uint64_t)TARGET_STACK_ADDR;
  uint64_t stack_hi = stack_lo + TARGET_STACK_SIZE;
  if (slot < stack_lo || slot + sizeof(uint64_t) > stack_hi) {
    return;
  }

  *(uint64_t *)slot = FAKE_ADDRS_PTR;
  uint64_t slot_offset = slot - stack_lo;
  *(uint64_t *)(TARGET_STACK_BACKUP_ADDR + slot_offset) = FAKE_ADDRS_PTR;
}

static void copy_mcontext_with_fpregs(mcontext_t *dst,
                                      struct _libc_fpstate *dst_fpregs,
                                      const mcontext_t *src) {
  *dst = *src;
  if (src->fpregs != NULL) {
    memcpy(dst_fpregs, src->fpregs, sizeof(*dst_fpregs));
  } else {
    memset(dst_fpregs, 0, sizeof(*dst_fpregs));
  }
  dst->fpregs = dst_fpregs;
}

void set_read_code() { *CUSTOM_CODE_ADDR = read_code[0]; }

void set_read_trap() { *CUSTOM_CODE_ADDR = ILLCODE_READ_TRAP; }

void trampoline_to_target() {
  mprotect(TRAMPOLINE_PAGE, 0x1000, PROT_READ);
  *TRAMPOLINE_TO_TARGET_HELPER = 1;
}

void trampoline_to_setup_initial_context() {
  mprotect(TRAMPOLINE_PAGE, 0x1000, PROT_READ);
  *TRAMPOLINE_TO_SETUP_INITIAL_CONTEXT_HELPER = 1;
}

void capture_read_context() {
  printf("Capturing read context\n");
  struct SharedContext *ctx = SHARED_CONTEXT;
  mprotect(DATA_START_PAGE, DATA_SECTION_PAGE_SIZE, PROT_READ | PROT_WRITE);
  set_read_trap();

  ctx->next_read = 0;
  ctx->backup_page_count = 0;
  ctx->next_code_start = 0;
  ctx->attempt_active = 0;
  ctx->attempt_failed = 0;
  ctx->next_code_breakpoint_original = -1;

  trampoline_to_target();
  uint64_t rsp = ctx->stored_target_context.gregs[REG_RSP];
  uint64_t ret = *(uint64_t *)(rsp);
  printf("Captured read is at %lx\n", ret);
  memcpy(TARGET_STACK_BACKUP_ADDR, TARGET_STACK_ADDR, TARGET_STACK_SIZE);
  install_fake_addrs_pointer();
  mprotect(DATA_START_PAGE, DATA_SECTION_PAGE_SIZE, PROT_READ);
  return;
}

void setup_initial_context() {
  uint64_t read_got_addr =
      ((uint64_t)READ_PLT_ADDR + 6 + *(int32_t *)((uint64_t)READ_PLT_ADDR + 2));
  *(void **)read_got_addr = CUSTOM_CODE_ADDR;
  if (MMAP_PLT_ADDR != 0) {
    uint64_t mmap_got_addr =
        ((uint64_t)MMAP_PLT_ADDR + 6 +
         *(int32_t *)((uint64_t)MMAP_PLT_ADDR + 2));
    *(void **)mmap_got_addr = mmap;
  }
  struct SharedContext *ctx = SHARED_CONTEXT;
  ctx->next_read = 0;
  ctx->backup_page_count = 0;
  ctx->next_code_start = 0;
  ctx->attempt_active = 0;
  ctx->attempt_failed = 0;
  ctx->next_code_breakpoint_original = -1;
  memset(&ctx->stored_target_context, 0, sizeof(ctx->stored_target_context));
  ctx->stored_target_context.gregs[REG_RIP] = TARGET_START_CODE_ADDR;
  ctx->stored_target_context.gregs[REG_RDI] = FAKE_ADDRS_PTR;
  // Entering run() via a context jump must mimic call ABI alignment.
  // SysV x86-64 expects RSP % 16 == 8 at function entry.
  ctx->stored_target_context.gregs[REG_RSP] =
      (uint64_t)TARGET_STACK_ADDR + TARGET_STACK_SIZE - 0x10000 - 8;
  trampoline_to_setup_initial_context();
}

int scan_direct_call_targets(const uint8_t *addr, size_t size,
                             uint64_t target) {
  int calls = 0;
  if (size < 5) {
    return 0;
  }
  for (size_t i = 0; i + 5 <= size; i++) {
    if (addr[i] != 0xe8) {
      continue;
    }
    int32_t rel = *(int32_t *)(addr + i + 1);
    uint64_t call_target = (uint64_t)(addr + i + 5) + rel;
    if (call_target == target) {
      calls++;
    }
  }
  return calls;
}

int scan_direct_call_score(const uint8_t *addr, size_t size, uint64_t target) {
  int calls = 0;
  int first = -1;
  int second = -1;
  if (size < 5) {
    return 0;
  }
  for (size_t i = 0; i + 5 <= size; i++) {
    if (addr[i] != 0xe8) {
      continue;
    }
    int32_t rel = *(int32_t *)(addr + i + 1);
    uint64_t call_target = (uint64_t)(addr + i + 5) + rel;
    if (call_target != target) {
      continue;
    }
    if (first == -1) {
      first = (int)i;
    } else if (second == -1) {
      second = (int)i;
    }
    calls++;
  }
  if (calls == 0) {
    return 0;
  }
  int proximity =
      second != -1 ? (int)(size - (size_t)second) : (int)(size - (size_t)first);
  return (calls << 16) + proximity;
}

int attempt_disassembling(const uint8_t *addr, int min_read_calls,
                          int min_putchar_calls, int min_prefix_match) {
  (void)min_prefix_match;
  size_t scan_window = 0x800;
  int read_calls = scan_direct_call_targets(addr, scan_window, READ_PLT_ADDR);
  int putchar_calls =
      scan_direct_call_targets(addr, scan_window, PUTCHAR_PLT_ADDR);
  if (read_calls < min_read_calls) {
    return 0;
  }
  if (putchar_calls < min_putchar_calls) {
    return 0;
  }
  if (min_read_calls == 0 && min_putchar_calls > 0) {
    return scan_direct_call_score(addr, scan_window, PUTCHAR_PLT_ADDR);
  }
  return scan_direct_call_score(addr, scan_window, READ_PLT_ADDR);
}

int attempt_decoding(uint16_t input, bool commit, int min_read_calls,
                     int min_putchar_calls, int min_prefix_match) {
  if (commit) {
    if (DEBUG >= 1)
      printf("Committing to decode with input %x\n", input);
  } else {
    if (DEBUG >= 1)
      printf("Attempting to decode with input %x\n", input);
  }
  set_read_code();
  mprotect(DATA_START_PAGE, DATA_SECTION_PAGE_SIZE, PROT_READ);
  struct SharedContext *ctx = SHARED_CONTEXT;
  ctx->next_read = input;
  ctx->backup_page_count = 0;
  ctx->next_code_start = 0;
  ctx->attempt_active = 1;
  ctx->attempt_failed = 0;
  ctx->next_code_breakpoint_original = -1;
  trampoline_to_target();
  ctx->attempt_active = 0;
  int disass = 0;
  if (ctx->next_code_start != 0) {
    if (ctx->next_code_breakpoint_original != -1 &&
        *(uint8_t *)ctx->next_code_start == ILLCODE_START_OF_NEXT_SECTION) {
      *(uint8_t *)ctx->next_code_start =
          (uint8_t)ctx->next_code_breakpoint_original;
    }
    disass =
        attempt_disassembling((uint8_t *)ctx->next_code_start, min_read_calls,
                              min_putchar_calls, min_prefix_match);
  }
  if (DEBUG >= 1)
    printf("Disassembled %d instructions\n", disass);

  if (commit) {
    if (ctx->attempt_failed) {
      for (int i = 0; i < ctx->backup_page_count; i++) {
        struct BackupPage *bp = &ctx->backup_pages[i];
        memcpy(bp->original_page, bp->backup_page, 0x1000);
        mprotect(bp->original_page, 0x1000,
                 restore_prot_for_addr((uint64_t)bp->original_page));
      }
      memcpy(TARGET_STACK_ADDR, TARGET_STACK_BACKUP_ADDR,
             TARGET_STACK_SIZE); // restore stack
      return -1;
    }
    for (int i = 0; i < ctx->backup_page_count; i++) {
      struct BackupPage *bp = &ctx->backup_pages[i];
      mprotect(bp->original_page, 0x1000,
               restore_prot_for_addr((uint64_t)bp->original_page));
    }
    copy_mcontext_with_fpregs(&ctx->stored_target_context,
                              &ctx->stored_target_fpregs,
                              &ctx->stored_target_context_attempt);
  } else {
    // printf("Attempt has %ld backup pages\n", ctx->backup_page_count);
    for (int i = 0; i < ctx->backup_page_count; i++) {
      struct BackupPage *bp = &ctx->backup_pages[i];
      memcpy(bp->original_page, bp->backup_page, 0x1000);
      mprotect(bp->original_page, 0x1000,
               restore_prot_for_addr((uint64_t)bp->original_page));
    }
    memcpy(TARGET_STACK_ADDR, TARGET_STACK_BACKUP_ADDR,
           TARGET_STACK_SIZE); // restore stack
  }
  return disass;
}

void sighandler_sigsegv(int signo, siginfo_t *si, void *ucontext) {
  ucontext_t *uc = (ucontext_t *)ucontext;
  if (DEBUG >= 1)
    printf("SIGSEGV at %p, rip = %p\n", si->si_addr,
           (void *)uc->uc_mcontext.gregs[REG_RIP]);
  struct SharedContext *ctx = SHARED_CONTEXT;
  if (si->si_addr == TRAMPOLINE_TO_TARGET_HELPER) {
    // trampoline
    mprotect(TRAMPOLINE_PAGE, 0x1000, PROT_READ | PROT_WRITE);
    copy_mcontext_with_fpregs(&ctx->stored_driver_context,
                              &ctx->stored_driver_fpregs, &uc->uc_mcontext);
    uc->uc_mcontext = ctx->stored_target_context;
    if (DEBUG >= 1)
      printf("Restored target RIP is %lx, top of stack is %p\n",
             (uint64_t)uc->uc_mcontext.gregs[REG_RIP],
             *(void **)uc->uc_mcontext.gregs[REG_RSP]);
    return;
  }
  if (si->si_addr ==
      TRAMPOLINE_TO_SETUP_INITIAL_CONTEXT_HELPER) { // set up initial target
                                                    // context
    // trampoline
    mprotect(TRAMPOLINE_PAGE, 0x1000, PROT_READ | PROT_WRITE);
    uint64_t target_rip = ctx->stored_target_context.gregs[REG_RIP];
    uint64_t target_rsp = ctx->stored_target_context.gregs[REG_RSP];
    copy_mcontext_with_fpregs(&ctx->stored_target_context,
                              &ctx->stored_target_fpregs, &uc->uc_mcontext);
    ctx->stored_target_context.gregs[REG_RIP] = target_rip;
    ctx->stored_target_context.gregs[REG_RSP] = target_rsp;
    return;
  }

  void *fault_addr = si->si_addr;
  uint64_t fault_addr_int = (uint64_t)fault_addr;
  if (!(is_code_addr(fault_addr_int) || is_data_addr(fault_addr_int))) {
    if (ctx->attempt_active) {
      ctx->attempt_failed = 1;
      uc->uc_mcontext = ctx->stored_driver_context;
      return;
    }
    printf("Fault address %p is not in code/data section\n", fault_addr);
    abort();
  }

  void *fault_page_addr = (void *)(fault_addr_int & ~0xfff);
  if (ctx->next_code_start == 0 && is_code_addr(fault_addr_int)) {
    // Single-step, so that after this write, we can put in a breakpoint in the
    // next block's first instruction.
    uint64_t *eflags = (uint64_t *)(&uc->uc_mcontext.gregs[REG_EFL]);
    *eflags |= 0x0100;
    ctx->next_code_start = fault_addr_int;
  }
  if (ctx->backup_page_count >= MAX_BACKUP_PAGES) {
    if (ctx->attempt_active) {
      ctx->attempt_failed = 1;
      uc->uc_mcontext = ctx->stored_driver_context;
      return;
    }
    printf("Exceeded backup page capacity (%d)\n", MAX_BACKUP_PAGES);
    abort();
  }
  mprotect(fault_page_addr, 0x1000, write_prot_for_addr(fault_addr_int));
  struct BackupPage *bp = &ctx->backup_pages[ctx->backup_page_count];
  bp->original_page = fault_page_addr;
  bp->backup_page =
      (void *)(PAGE_BACKUP_ADDR + 0x1000 * ctx->backup_page_count);
  ctx->backup_page_count++;
  memcpy(bp->backup_page, fault_page_addr, 0x1000);
}

void sighandler_sigtrap(int signo, siginfo_t *si, void *ucontext) {
  if (DEBUG >= 1)
    printf("SIGTRAP at %p\n", si->si_addr);
  ucontext_t *uc = (ucontext_t *)ucontext;
  struct SharedContext *ctx = SHARED_CONTEXT;
  if (ctx->next_code_start == 0) {
    if (ctx->attempt_active) {
      ctx->attempt_failed = 1;
      uc->uc_mcontext = ctx->stored_driver_context;
      return;
    }
    abort();
  }
  uint8_t *code = (uint8_t *)ctx->next_code_start;
  ctx->next_code_breakpoint_original = *code;
  *code = ILLCODE_START_OF_NEXT_SECTION; // illegal opcode
  uc->uc_mcontext.gregs[REG_EFL] &= ~0x0100;
}

void sighandler_sigill(int signo, siginfo_t *si, void *ucontext) {
  if (DEBUG >= 1)
    printf("SIGILL at %p\n", si->si_addr);
  ucontext_t *uc = (ucontext_t *)ucontext;
  struct SharedContext *ctx = SHARED_CONTEXT;
  if (*(uint8_t *)si->si_addr == ILLCODE_READ_TRAP) {
    uint64_t rsp = uc->uc_mcontext.gregs[REG_RSP];
    uint64_t ret = *(uint64_t *)(rsp);
    if (DEBUG >= 1)
      printf("  .. for read trap at %lx\n", ret);

    copy_mcontext_with_fpregs(&ctx->stored_target_context,
                              &ctx->stored_target_fpregs, &uc->uc_mcontext);
    uc->uc_mcontext = ctx->stored_driver_context;
    return;
  } else if (*(uint8_t *)si->si_addr == ILLCODE_START_OF_NEXT_SECTION) {
    uint8_t *code = (uint8_t *)ctx->next_code_start;
    if (si->si_addr != code) {
      printf("SIGILL at %p, but not at expected address %p\n", si->si_addr,
             code);
      exit(1);
    }
    assert(ctx->next_code_breakpoint_original != -1);
    *code = ctx->next_code_breakpoint_original;
    copy_mcontext_with_fpregs(&ctx->stored_target_context_attempt,
                              &ctx->stored_target_context_attempt_fpregs,
                              &uc->uc_mcontext);
    uc->uc_mcontext = ctx->stored_driver_context;
    return;
  } else {
    if (ctx->attempt_active) {
      ctx->attempt_failed = 1;
      uc->uc_mcontext = ctx->stored_driver_context;
      return;
    }
    if (DEBUG >= 1)
      printf("Unknown SIGILL at %p\n", si->si_addr);
    exit(1);
  }
}

void load_from_file_section(int fd, uint8_t *addr, uint64_t size,
                            uint64_t offset) {
  lseek(fd, offset, SEEK_SET);
  while (size > 0) {
    if (DEBUG >= 1) {
      printf("Reading %lx bytes from %lx to %p\n", size, offset, addr);
    }
    ssize_t n = read(fd, addr, size);
    assert(n > 0);
    addr += n;
    size -= n;
  }
}

int compare_attempt_result(const void *a, const void *b) {
  return -(((struct AttemptResult *)a)->disass -
           ((struct AttemptResult *)b)->disass);
}

int count_positive_candidates(void) {
  int valid_candidates = 0;
  for (int c = 0; c < 65536; c++) {
    if (ATTEMPT_RESULT[c].disass <= 0) {
      break;
    }
    valid_candidates++;
  }
  return valid_candidates;
}

uint16_t attempt_decoding_all(int min_read_calls, int min_putchar_calls,
                              int min_prefix_match) {
  memset(ATTEMPT_RESULT, 0, 65536 * sizeof(struct AttemptResult));

  const int PARALLELISM = 16;
  fflush(stdout);

  pid_t pids[PARALLELISM];
  for (int f = 0; f < PARALLELISM; f++) {
    pid_t pid = fork();
    if (pid == 0) {
      for (int i = f; i < 65536; i += PARALLELISM) {
        int disass = attempt_decoding(i, false, min_read_calls,
                                      min_putchar_calls, min_prefix_match);
        // printf("Attempt %d done.\n", i);
        struct AttemptResult result;
        result.disass = disass;
        result.input = i;
        ATTEMPT_RESULT[i] = result;
      }
      exit(0);
    } else {
      pids[f] = pid;
    }
  }
  for (int f = 0; f < PARALLELISM; f++) {
    int status;
    waitpid(pids[f], &status, 0);
    if (WIFEXITED(status)) {
      // printf("Child %d exited with status %d\n", pids[f],
      // WEXITSTATUS(status));
    } else {
      printf("Child %d exited abnormally\n", pids[f]);
    }
  }

  qsort(ATTEMPT_RESULT, 65536, sizeof(struct AttemptResult),
        compare_attempt_result);
  // printf("Top 10 results:\n");
  // for (int i = 0; i < 10; i++) {
  //   struct AttemptResult *result = &ATTEMPT_RESULT[i];
  //   printf("  %x: %d\n", result->input, result->disass);
  // }
  return ATTEMPT_RESULT[0].input;
}

int main(int argc, char **argv) {
  char const *target_path = "packed_real";
  char const *recovered_path = "recovered";
  if (argc >= 2) {
    target_path = argv[1];
  }
  if (argc >= 3) {
    recovered_path = argv[2];
  }

  int fd = open(target_path, O_RDONLY);
  assert(fd != -1);
  uint8_t *code = mmap(CODE_START_PAGE, CODE_SECTION_PAGE_SIZE,
                       PROT_READ | PROT_WRITE | PROT_EXEC,
                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  assert(code != MAP_FAILED);
  load_from_file_section(fd, CODE_START, CODE_FILE_SIZE,
                         CODE_START_FILE_OFFSET);
  mprotect(CODE_START_PAGE, CODE_SECTION_PAGE_SIZE, PROT_READ | PROT_EXEC);

  uint8_t *rodata =
      mmap(RODATA_START_PAGE, RODATA_SECTION_PAGE_SIZE, PROT_READ | PROT_WRITE,
           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  assert(rodata != MAP_FAILED);
  load_from_file_section(fd, RODATA_START, RODATA_FILE_SIZE,
                         RODATA_START_FILE_OFFSET);
  mprotect(RODATA_START_PAGE, RODATA_SECTION_PAGE_SIZE, PROT_READ);

  uint8_t *data =
      mmap(DATA_START_PAGE, DATA_SECTION_PAGE_SIZE, PROT_READ | PROT_WRITE,
           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  assert(data != MAP_FAILED);
  load_from_file_section(fd, DATA_START, DATA_FILE_SIZE,
                         DATA_START_FILE_OFFSET);

  close(fd);

  uint8_t *shared =
      mmap(SHARED_CONTEXT, SHARED_CONTEXT_SIZE, PROT_READ | PROT_WRITE,
           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  assert(shared != MAP_FAILED);
  uint8_t *backup =
      mmap(PAGE_BACKUP_ADDR, PAGE_BACKUP_SIZE, PROT_READ | PROT_WRITE,
           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  assert(backup != MAP_FAILED);

  uint8_t *patches =
      mmap(CUSTOM_CODE_ADDR, 0x1000, PROT_READ | PROT_WRITE | PROT_EXEC,
           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  assert(patches != MAP_FAILED);
  memcpy(patches, read_code, sizeof(read_code));

  uint8_t *stack =
      mmap(TARGET_STACK_ADDR, TARGET_STACK_SIZE, PROT_READ | PROT_WRITE,
           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  uint8_t *stack_backup =
      mmap(TARGET_STACK_BACKUP_ADDR, TARGET_STACK_SIZE, PROT_READ | PROT_WRITE,
           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  uint8_t *trampoline_helper =
      mmap(TRAMPOLINE_TO_TARGET_HELPER, 0x1000, PROT_READ,
           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

  void *attempt_result =
      mmap(ATTEMPT_RESULT, 65536 * sizeof(struct AttemptResult),
           PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
  assert(attempt_result != MAP_FAILED);

  {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_flags = SA_ONSTACK | SA_SIGINFO;
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = sighandler_sigsegv;
    sigaction(SIGSEGV, &sa, NULL);
  }
  {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_flags = SA_ONSTACK | SA_SIGINFO;
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = sighandler_sigtrap;
    sigaction(SIGTRAP, &sa, NULL);
  }
  {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_flags = SA_ONSTACK | SA_SIGINFO;
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = sighandler_sigill;
    sigaction(SIGILL, &sa, NULL);
  }

  int correct = open(recovered_path, O_WRONLY | O_CREAT | O_TRUNC, 0666);
  assert(correct != -1);

  setup_initial_context();
  capture_read_context();

  for (int i = 0; i < NSEGMENTS; i++) {
    int min_read_calls = (i + 1 < NSEGMENTS) ? 2 : 0;
    int min_putchar_calls = (i + 1 < NSEGMENTS) ? 0 : 4;
    int min_prefix_match = (i + 1 < NSEGMENTS) ? 0 : 12;
    attempt_decoding_all(min_read_calls, min_putchar_calls, min_prefix_match);
    int valid_candidates = count_positive_candidates();
    if (valid_candidates == 0) {
      fprintf(stderr,
              "solver found no valid candidates at segment %d "
              "(min_read=%d min_putchar=%d min_prefix=%d)\n",
              i, min_read_calls, min_putchar_calls, min_prefix_match);
      return 1;
    }
    if (valid_candidates > 1) {
      int print_limit = valid_candidates < 16 ? valid_candidates : 16;
      fprintf(stderr,
              "solver ambiguity at segment %d: %d candidates satisfy scoring "
              "(min_read=%d min_putchar=%d min_prefix=%d)\n",
              i, valid_candidates, min_read_calls, min_putchar_calls,
              min_prefix_match);
      for (int c = 0; c < print_limit; c++) {
        struct AttemptResult *result = &ATTEMPT_RESULT[c];
        fprintf(stderr, "  rank %d input=0x%04x score=%d\n", c + 1,
                result->input, result->disass);
      }
      return 1;
    }

    uint16_t input = ATTEMPT_RESULT[0].input;
    write(correct, &input, sizeof(input));
    int committed = attempt_decoding(input, true, min_read_calls,
                                     min_putchar_calls, min_prefix_match);
    if (committed < 0 && i + 1 < NSEGMENTS) {
      fprintf(stderr, "solver failed committing segment %d\n", i);
      return 1;
    }
    if (i + 1 < NSEGMENTS) {
      capture_read_context();
    }
  }

  return 0;
}
