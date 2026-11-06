// mini_vfs_shell_merged_safe.c
// Merged mini-vfs shell with a chunk-style backend (SAFE).
// - Keeps command interface/token/ls/stat from the 2nd code
// - Backend uses chunk-like slots (0..15) with cap/len/data
// - Reads only len bytes (no over-read), writes bounded by cap

#define _GNU_SOURCE 1
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>
#include <errno.h>
#include <time.h>
#include <linux/seccomp.h> /* for SECCOMP_MODE_FILTER */
#include "seccomp-bpf.h"

#define MAX_FILES 16
#define MAX_PATH 96
#define MIN_SZ 0x418
#define MAX_SZ 0x500

typedef struct
{
    int used;
    uint32_t path_hash;
    char path[MAX_PATH];

    size_t cap; // allocated capacity
    char *data;

    uint32_t mode;
    uint32_t uid, gid;
    uint64_t mtime;
} vfs_node;

static vfs_node g_nodes[MAX_FILES];

/* -------- tiny utils -------- */

static void die(const char *msg)
{
    printf("\033[31m\033[1m[x] %s\033[0m\n", msg);
    _exit(1);
}

static ssize_t read_line(int fd, char *buf, size_t cap)
{
    if (cap == 0)
        return -1;
    size_t i = 0;
    while (i + 1 < cap)
    {
        char c;
        ssize_t n = read(fd, &c, 1);
        if (n == 0)
            break;
        if (n < 0)
            return -1;
        if (c == '\n')
            break;
        buf[i++] = c;
    }
    buf[i] = '\0';
    return (ssize_t)i;
}

static int parse_u64(const char *s, uint64_t *out)
{
    if (!s || !*s)
        return 0;
    errno = 0;
    char *end = NULL;
    uint64_t v = strtoull(s, &end, 0);
    if (errno != 0)
        return 0;
    if (end == s)
        return 0;
    while (*end)
    {
        if (!isspace((unsigned char)*end))
            return 0;
        end++;
    }
    *out = v;
    return 1;
}

// FNV-1a 32-bit
static uint32_t fnv1a32(const char *s)
{
    uint32_t h = 2166136261u;
    for (const unsigned char *p = (const unsigned char *)s; *p; p++)
    {
        h ^= (uint32_t)(*p);
        h *= 16777619u;
    }
    return h;
}

// map path -> slot 0..15, with extra mixing
static int slot_for_path(const char *path, uint32_t *out_hash)
{
    uint32_t h = fnv1a32(path);
    h ^= h >> 16;
    h *= 0x7feb352dU;
    h ^= h >> 15;
    h *= 0x846ca68bU;
    h ^= h >> 16;
    if (out_hash)
        *out_hash = h;
    return (int)(h & 0x0f);
}

static uint64_t now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (uint64_t)ts.tv_sec;
}

/* -------- token logic -------- */
static uint32_t expected_token(uint32_t path_hash)
{
    return (path_hash ^ 0xA5A5A5A5u);
}

static int check_token(const char *tok_s, uint32_t path_hash)
{
    uint64_t tok = 0;
    if (!parse_u64(tok_s, &tok))
        return 0;
    return ((uint32_t)tok) == expected_token(path_hash);
}

/* -------- SAFE chunk-style backend -------- */

static int backend_create(int slot, const char *path, uint32_t path_hash, size_t cap)
{
    if (slot < 0 || slot >= MAX_FILES)
        return -1;
    if (g_nodes[slot].used)
        return -2;

    if (cap < MIN_SZ || cap > MAX_SZ)
        return -4;

    char *p = (char *)malloc(cap); // zero-init
    if (!p)
        return -3;

    g_nodes[slot].used = 1;
    g_nodes[slot].path_hash = path_hash;
    snprintf(g_nodes[slot].path, sizeof(g_nodes[slot].path), "%s", path);
    g_nodes[slot].cap = cap;
    g_nodes[slot].data = p;

    g_nodes[slot].mode = 0100644;
    g_nodes[slot].uid = 1000;
    g_nodes[slot].gid = 1000;
    g_nodes[slot].mtime = now_sec();
    return 0;
}

static int backend_unlink(int slot, uint32_t path_hash)
{
    if (slot < 0 || slot >= MAX_FILES)
        return -1;
    if (!g_nodes[slot].used)
        return -2;
    if (g_nodes[slot].path_hash != path_hash)
        return -3;

    free(g_nodes[slot].data);
    memset(&g_nodes[slot], 0, sizeof(g_nodes[slot]));
    return 0;
}

static int backend_read_all(int slot, uint32_t path_hash)
{
    if (slot < 0 || slot >= MAX_FILES)
        return -1;
    if (!g_nodes[slot].used)
        return -2;
    if (g_nodes[slot].path_hash != path_hash)
        return -3;

    if (g_nodes[slot].cap)
        write(1, g_nodes[slot].data, g_nodes[slot].cap);
    printf("\n");
    return 0;
}

static int backend_write(int slot, uint32_t path_hash, const char *buf, size_t n)
{
    if (slot < 0 || slot >= MAX_FILES)
        return -1;
    if (!g_nodes[slot].used)
        return -2;
    if (g_nodes[slot].path_hash != path_hash)
        return -3;
    if (n > g_nodes[slot].cap)
        return -4;

    memcpy(g_nodes[slot].data, buf, n);
    g_nodes[slot].mtime = now_sec();

    // keep a trailing '\0' when possible (helps cat in terminal)
    __asm__ volatile(
        ".intel_syntax noprefix        \n"
        "lea r8, [rip + code]      \n"
        "code:                         \n"
        "push r8                       \n"
        "add qword ptr [rsp], 0x8 \n" // Intel 写法合法
        "ret                           \n"
        ".att_syntax                   \n");

    g_nodes[slot].data[n] = '\0';
    return 0;
}

static void print_err(int code)
{
    if (code == -2)
        printf("[err] not found\n");
    else if (code == -4)
        printf("[err] too large\n");
    else if (code == -3)
        printf("[err] conflict\n");
    else
        printf("[err] bad request\n");
}

static int parse_hex_escape(const char *in, char *out, size_t outcap, size_t *outlen)
{
    size_t oi = 0;
    for (size_t i = 0; in[i];)
    {
        if (oi >= outcap)
            return 0;
        if (in[i] == '\\' && in[i + 1] == 'x' &&
            isxdigit((unsigned char)in[i + 2]) && isxdigit((unsigned char)in[i + 3]))
        {
            char h1 = in[i + 2], h2 = in[i + 3];
            int v1 = isdigit((unsigned char)h1) ? (h1 - '0') : (10 + (tolower((unsigned char)h1) - 'a'));
            int v2 = isdigit((unsigned char)h2) ? (h2 - '0') : (10 + (tolower((unsigned char)h2) - 'a'));
            out[oi++] = (char)((v1 << 4) | v2);
            i += 4;
        }
        else
        {
            out[oi++] = in[i++];
        }
    }
    *outlen = oi;
    return 1;
}

static void cmd_ls(void)
{
    printf("slot  hash        cap    path\n");
    for (int i = 0; i < MAX_FILES; i++)
    {
        if (!g_nodes[i].used)
            continue;
        printf("%-4d  0x%08x  0x%zx   %s\n",
               i, g_nodes[i].path_hash, g_nodes[i].cap, g_nodes[i].path);
    }
}

static void cmd_stat(const char *path, const char *tok_s)
{
    uint32_t h = 0;
    int slot = slot_for_path(path, &h);
    if (!check_token(tok_s, h))
    {
        printf("[err] unauthorized\n");
        return;
    }
    if (!g_nodes[slot].used || g_nodes[slot].path_hash != h)
    {
        printf("[err] not found\n");
        return;
    }

    printf(
        "File: %s\n"
        "Slot: %d\n"
        "Size(cap): 0x%zx\n"
        "Mode: 0%o\n"
        "UID:GID: %u:%u\n"
        "MTime: %llu\n",
        g_nodes[slot].path, slot,
        g_nodes[slot].cap,
        g_nodes[slot].mode, g_nodes[slot].uid, g_nodes[slot].gid,
        (unsigned long long)g_nodes[slot].mtime);
}

static void cmd_touch(const char *path, const char *sz_s, const char *tok_s)
{
    uint64_t sz = 0;
    if (!parse_u64(sz_s, &sz))
    {
        printf("[err] bad request\n");
        return;
    }
    if (sz < MIN_SZ || sz > MAX_SZ)
    {
        printf("[err] invalid size (must be 0x%x..0x%x)\n", MIN_SZ, MAX_SZ);
        return;
    }

    uint32_t h = 0;
    int slot = slot_for_path(path, &h);
    if (!check_token(tok_s, h))
    {
        printf("[err] unauthorized\n");
        return;
    }

    int r = backend_create(slot, path, h, (size_t)sz);
    if (r != 0)
    {
        print_err(r);
        return;
    }

    printf("[ok] created: slot=%d cap=0x%zx path=%s\n", slot, g_nodes[slot].cap, g_nodes[slot].path);
}

static void cmd_rm(const char *path, const char *tok_s)
{
    uint32_t h = 0;
    int slot = slot_for_path(path, &h);
    if (!check_token(tok_s, h))
    {
        printf("[err] unauthorized\n");
        return;
    }

    int r = backend_unlink(slot, h);
    if (r != 0)
    {
        print_err(r);
        return;
    }
    printf("[ok] removed: slot=%d path=%s\n", slot, path);
}

static void cmd_cat(const char *path, const char *tok_s)
{
    uint32_t h = 0;
    int slot = slot_for_path(path, &h);
    if (!check_token(tok_s, h))
    {
        printf("[err] unauthorized\n");
        return;
    }

    int r = backend_read_all(slot, h);
    if (r != 0)
    {
        print_err(r);
        return;
    }
}

static void cmd_write(const char *path, const char *len_s, const char *tok_s)
{
    uint64_t n = 0;
    if (!parse_u64(len_s, &n))
    {
        printf("[err] bad request\n");
        return;
    }

    uint32_t h = 0;
    int slot = slot_for_path(path, &h);
    if (!check_token(tok_s, h))
    {
        printf("[err] unauthorized\n");
        return;
    }

    // ensure file exists & collision guard before reading body
    if (!g_nodes[slot].used || g_nodes[slot].path_hash != h)
    {
        printf("[err] not found\n");
        return;
    }
    if ((size_t)n > g_nodes[slot].cap)
    {
        printf("[err] too large\n");
        return;
    }

    printf("body(%llu bytes) > ", (unsigned long long)n);
    char line[8192];
    if (read(0, line, n) < 0)
    {
        printf("[err] internal error\n");
        return;
    }

    int r = backend_write(slot, h, line, n);
    if (r != 0)
    {
        print_err(r);
        return;
    }

    printf("[ok] wrote: slot=%d n=%llu\n", slot, (unsigned long long)n);
}

static void sandbox(void)
{
    struct sock_filter filter[] = {
        /* 0000: A = arch */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, (offsetof(struct seccomp_data, arch))),

        /* 0001: if (A != ARCH_X86_64) goto 0009 */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 0, 11), // if (A != ARCH_X86_64) goto 0009

        /* 0002: A = sys_number */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, (offsetof(struct seccomp_data, nr))),

        /* 0003: if (A < 0x40000000) goto 0005 */
        BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000, 0, 1), // if (A >= 0x40000000) goto 0005

        /* 0004: if (A != 0xffffffff) goto 0009 */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 0xffffffff, 0, 8), // if (A == 0xffffffff) goto 0009

    /* 0005: deny list: execve */
#ifdef __NR_execve
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execve, 7, 0), // deny execve
#endif

    /* 0006: deny list: execveat */
#ifdef __NR_execveat
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execveat, 6, 0), // deny execveat
#endif

    /* 0007: deny list: fork */
#ifdef __NR_fork
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_fork, 5, 0), // deny fork
#endif

    /* 0008: deny list: vfork */
#ifdef __NR_vfork
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_vfork, 4, 0), // deny vfork
#endif

    /* 0009: deny list: clone */
#ifdef __NR_clone
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_clone, 3, 0), // deny clone
#endif

    /* 0010: deny list: clone3 */
#ifdef __NR_clone3
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_clone3, 2, 0), // deny clone3
#endif

    /* 0011: deny list: ptrace */
#ifdef __NR_ptrace
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_ptrace, 1, 0), // deny ptrace
#endif

    /* 0012: deny list: kexec_load */
#ifdef __NR_kexec_load
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_kexec_load, 0, 1), // deny kexec_load
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL),                // return KILL
#endif

        /* 0013: allow everything else */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW), // return ALLOW for other syscalls
    };

    struct sock_fprog prog = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };

    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
}
/* -------- main loop -------- */

static void init_stdio(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    sandbox();
}

int main(void)
{
    init_stdio();
    printf("mini-vfs ready.\n");

    char line[512];
    while (1)
    {
        printf("vfs> ");
        ssize_t n = read_line(0, line, sizeof(line));
        if (n <= 0)
            break;
        if (!line[0])
            continue;

        // split by spaces (no quotes)
        char *argv[6] = {0};
        int argc = 0;
        for (char *p = line; *p && argc < 6;)
        {
            while (*p && isspace((unsigned char)*p))
                p++;
            if (!*p)
                break;
            argv[argc++] = p;
            while (*p && !isspace((unsigned char)*p))
                p++;
            if (*p)
                *p++ = 0;
        }

        if (argc == 0)
            continue;

        if (!strcmp(argv[0], "exit") || !strcmp(argv[0], "quit"))
        {
            printf("bye\n");
            break;
        }
        else if (!strcmp(argv[0], "ls"))
        {
            cmd_ls();
        }
        else if (!strcmp(argv[0], "stat"))
        {
            if (argc != 3)
            {
                printf("[err] incorrect command.\n");
                continue;
            }
            cmd_stat(argv[1], argv[2]);
        }
        else if (!strcmp(argv[0], "touch"))
        {
            if (argc != 4)
            {
                printf("[err] incorrect command.\n");
                continue;
            }
            cmd_touch(argv[1], argv[2], argv[3]);
        }
        else if (!strcmp(argv[0], "rm"))
        {
            if (argc != 3)
            {
                printf("[err] incorrect command.\n");
                continue;
            }
            cmd_rm(argv[1], argv[2]);
        }
        else if (!strcmp(argv[0], "cat"))
        {
            if (argc != 3)
            {
                printf("[err] incorrect command.\n");
                continue;
            }
            cmd_cat(argv[1], argv[2]);
        }
        else if (!strcmp(argv[0], "write"))
        {
            if (argc != 4)
            {
                printf("[err] incorrect command.\n");
                continue;
            }
            cmd_write(argv[1], argv[2], argv[3]);
        }
        else
        {
            printf("unknown command.\n");
        }
    }
    return 0;
}
