#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>


#if defined(__aarch64__)
#define SC_AUDIT_ARCH AUDIT_ARCH_AARCH64
#elif defined(__x86_64__)
#define SC_AUDIT_ARCH AUDIT_ARCH_X86_64
#else
#error Unsupported architecture for seccomp filter
#endif

#ifndef SECCOMP_RET_KILL_PROCESS
#define SECCOMP_RET_KILL_PROCESS SECCOMP_RET_KILL
#endif

#define SLOT_COUNT 2
#define LABEL_SIZE 32
#define MIN_DRAFT 0x40
#define MAX_DRAFT 0x80
#define AUTH_MAGIC 0x434f4d44U
#define CLEARANCE_MAGIC 7U

typedef struct {
    int open;
    size_t draft_size;
    char *draft;
    char label[LABEL_SIZE];
} Channel;

typedef struct __attribute__((aligned(16))) {
    char operator[32];
    uint32_t verified;
    uint32_t clearance;
    char mission[16];
    char padding[72];
} AuthBlock;

typedef struct {
    void (*status_hook)(size_t slot, const Channel *channel);
} OpsTable;

_Static_assert(sizeof(AuthBlock) == 0x80, "Auth block must match the 0x80 tcache bin");

Channel g_channels[SLOT_COUNT];
AuthBlock g_auth;
OpsTable g_ops;

static void install_seccomp(void);
static int seccomp_mode(void);
static int apply_seccomp_filter(const struct sock_fprog *program);
static void banner(void);
static void initialize_state(void);
static void menu_loop(void);
static void open_channel(void);
static void queue_message(void);
static void edit_draft(void);
static void close_channel(void);
static void view_status(void);
static void transmit_report(void);
void render_status(size_t slot, const Channel *channel);

static void die(const char *message) {
    perror(message);
    _exit(1);
}

static void read_exact(void *buffer, size_t length) {
    size_t offset = 0;

    while (offset < length) {
        ssize_t count = read(STDIN_FILENO, (char *)buffer + offset, length - offset);

        if (count <= 0) {
            _exit(0);
        }

        offset += (size_t)count;
    }
}

static size_t read_line(char *buffer, size_t length) {
    size_t used = 0;

    if (length == 0) {
        return 0;
    }

    while (used + 1 < length) {
        char byte = '\0';
        ssize_t count = read(STDIN_FILENO, &byte, 1);

        if (count <= 0) {
            _exit(0);
        }

        if (byte == '\n') {
            break;
        }

        buffer[used++] = byte;
    }

    buffer[used] = '\0';
    return used;
}

static unsigned long read_ulong_prompt(const char *prompt) {
    char line[64];
    char *end = NULL;
    unsigned long value = 0;

    printf("%s", prompt);
    read_line(line, sizeof(line));

    errno = 0;
    value = strtoul(line, &end, 0);

    if (errno != 0 || end == line || *end != '\0') {
        puts("[PATRIOT-7] Invalid numeric input.");
        return (unsigned long)-1;
    }

    return value;
}

static size_t read_slot(void) {
    unsigned long slot = read_ulong_prompt("Slot: ");

    if (slot >= SLOT_COUNT) {
        puts("[PATRIOT-7] No such channel slot.");
        return (size_t)-1;
    }

    return (size_t)slot;
}

static void banner(void) {
    puts("╔══════════════════════════════════════════════════════════════╗");
    puts("║     TEXAS A&M UNIVERSITY — DEFENSE RESEARCH LABORATORY     ║");
    puts("║          ADVANCED WEAPONS SYSTEMS DIVISION (AWSD)          ║");
    puts("║                                                             ║");
    puts("║  SYSTEM: PATRIOT-7 Secure Research Terminal v5.0           ║");
    puts("║  MODE: DRAFT QUEUE / CHANNEL CONTROL                       ║");
    puts("╚══════════════════════════════════════════════════════════════╝");
    puts("");
    puts("[PATRIOT-7] Secure relay online.");
    puts("[PATRIOT-7] Operator shell disabled. Flag vault is relay-only.");
    puts("");
}

static void initialize_state(void) {
    memset(g_channels, 0, sizeof(g_channels));
    memset(&g_auth, 0, sizeof(g_auth));

    memcpy(g_auth.operator, "GUEST", 5);
    memcpy(g_auth.mission, "PATRIOT-7", 9);
    g_auth.verified = 0;
    g_auth.clearance = 1;

    g_ops.status_hook = render_status;
}

void render_status(size_t slot, const Channel *channel) {
    printf("[STATUS] channel=%zu state=%s\n", slot, channel->open ? "OPEN" : "CLOSED");
    printf("[STATUS] callsign=%s\n", channel->label[0] ? channel->label : "<unset>");
    printf("[STATUS] draft_size=%#zx\n", channel->draft_size);

    if (!channel->open && channel->draft != NULL) {
        printf("[STATUS] last_draft=%p\n", (void *)channel->draft);
        printf("[STATUS] diagnostic_hook=%p\n", (void *)g_ops.status_hook);
        puts("[STATUS] stale metadata retained for deferred audit replay.");
    }
}

static void open_channel(void) {
    size_t slot = read_slot();
    Channel *channel = NULL;

    if (slot == (size_t)-1) {
        return;
    }

    channel = &g_channels[slot];

    if (channel->open) {
        puts("[PATRIOT-7] Channel already active.");
        return;
    }

    channel->open = 1;
    channel->draft = NULL;
    channel->draft_size = 0;
    memset(channel->label, 0, sizeof(channel->label));

    printf("Callsign: ");
    read_line(channel->label, sizeof(channel->label));
    puts("[PATRIOT-7] Channel opened.");
}

static void queue_message(void) {
    size_t slot = read_slot();
    Channel *channel = NULL;
    unsigned long requested = 0;
    size_t size = 0;

    if (slot == (size_t)-1) {
        return;
    }

    channel = &g_channels[slot];

    if (!channel->open) {
        puts("[PATRIOT-7] Open the channel first.");
        return;
    }

    if (channel->draft != NULL) {
        puts("[PATRIOT-7] Draft already queued for this channel.");
        return;
    }

    requested = read_ulong_prompt("Draft bytes (64-128): ");

    if (requested == (unsigned long)-1 || requested < MIN_DRAFT || requested > MAX_DRAFT) {
        puts("[PATRIOT-7] Draft size rejected by relay controller.");
        return;
    }

    size = (size_t)requested;
    channel->draft = malloc(size);

    if (channel->draft == NULL) {
        die("malloc");
    }

    channel->draft_size = size;
    printf("Draft payload (%zu bytes): ", size);
    read_exact(channel->draft, size);
    puts("[PATRIOT-7] Draft buffered.");
}

static void edit_draft(void) {
    size_t slot = read_slot();
    Channel *channel = NULL;
    unsigned long requested = 0;
    unsigned char approved = 0;

    if (slot == (size_t)-1) {
        return;
    }

    channel = &g_channels[slot];

    if (channel->draft == NULL || channel->draft_size == 0) {
        puts("[PATRIOT-7] No draft metadata present for that slot.");
        return;
    }

    requested = read_ulong_prompt("Editor span: ");

    if (requested == (unsigned long)-1 || requested == 0) {
        puts("[PATRIOT-7] Editor span rejected.");
        return;
    }

    approved = (unsigned char)requested;
    if ((size_t)approved > channel->draft_size) {
        puts("[PATRIOT-7] Editor span exceeds the recorded draft size.");
        return;
    }

    printf("Patch bytes (%lu): ", requested);
    read_exact(channel->draft, (size_t)requested);
    puts("[PATRIOT-7] Draft patch applied.");
}

static void close_channel(void) {
    size_t slot = read_slot();
    Channel *channel = NULL;

    if (slot == (size_t)-1) {
        return;
    }

    channel = &g_channels[slot];

    if (!channel->open) {
        puts("[PATRIOT-7] Channel already closed.");
        return;
    }

    if (channel->draft != NULL) {
        free(channel->draft);
    }

    channel->open = 0;
    puts("[PATRIOT-7] Channel parked for audit review.");
}

static void view_status(void) {
    size_t slot = read_slot();

    if (slot == (size_t)-1) {
        return;
    }

    g_ops.status_hook(slot, &g_channels[slot]);
}

static void transmit_report(void) {
    size_t slot = read_slot();
    int fd = -1;
    char buffer[128];
    ssize_t count = 0;

    if (slot == (size_t)-1) {
        return;
    }

    if (!g_channels[slot].open) {
        puts("[PATRIOT-7] Bring a channel online before transmission.");
        return;
    }

    if (g_auth.verified != AUTH_MAGIC || g_auth.clearance != CLEARANCE_MAGIC) {
        puts("[PATRIOT-7] Clearance denied.");
        return;
    }

    fd = open("/flag.txt", O_RDONLY);
    if (fd < 0) {
        puts("[PATRIOT-7] Flag vault offline.");
        return;
    }

    puts("[PATRIOT-7] Transmitting sealed report:");
    while ((count = read(fd, buffer, sizeof(buffer))) > 0) {
        if (write(STDOUT_FILENO, buffer, (size_t)count) < 0) {
            close(fd);
            die("write");
        }
    }
    write(STDOUT_FILENO, "\n", 1);
    close(fd);
}

static int seccomp_mode(void) {
    FILE *status = fopen("/proc/self/status", "r");
    char line[128];

    if (status != NULL) {
        while (fgets(line, sizeof(line), status) != NULL) {
            if (strncmp(line, "Seccomp:", 8) == 0) {
                int mode = (int)strtol(line + 8, NULL, 10);

                fclose(status);
                return mode;
            }
        }

        fclose(status);
    }

    return prctl(PR_GET_SECCOMP, 0, 0, 0, 0);
}

static int apply_seccomp_filter(const struct sock_fprog *program) {
#ifdef SYS_seccomp
    if (syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, program) == 0) {
        return 0;
    }
#endif
    return prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, program);
}

#define DENY_SYSCALL(name) \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_##name, 0, 1), \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS)

static void install_seccomp(void) {
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SC_AUDIT_ARCH, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        DENY_SYSCALL(execve),
#ifdef __NR_execveat
        DENY_SYSCALL(execveat),
#endif
#ifdef __NR_clone
        DENY_SYSCALL(clone),
#endif
#ifdef __NR_clone3
        DENY_SYSCALL(clone3),
#endif
#ifdef __NR_fork
        DENY_SYSCALL(fork),
#endif
#ifdef __NR_vfork
        DENY_SYSCALL(vfork),
#endif
#ifdef __NR_ptrace
        DENY_SYSCALL(ptrace),
#endif
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog program = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        die("prctl(PR_SET_NO_NEW_PRIVS)");
    }

    if (apply_seccomp_filter(&program) != 0) {
        int saved_errno = errno;

        /* Nested sandboxes may refuse an extra filter even when seccomp is already active. */
        if ((saved_errno == EINVAL || saved_errno == EPERM) &&
            seccomp_mode() == SECCOMP_MODE_FILTER) {
            return;
        }

        errno = saved_errno;
        die("seccomp install");
    }
}

static void menu_loop(void) {
    for (;;) {
        unsigned long choice = 0;

        puts("");
        puts("1. Open channel");
        puts("2. Queue message");
        puts("3. Edit draft");
        puts("4. Close channel");
        puts("5. View status");
        puts("6. Transmit report");
        puts("7. Exit");

        choice = read_ulong_prompt("> ");

        switch (choice) {
        case 1:
            open_channel();
            break;
        case 2:
            queue_message();
            break;
        case 3:
            edit_draft();
            break;
        case 4:
            close_channel();
            break;
        case 5:
            view_status();
            break;
        case 6:
            transmit_report();
            break;
        case 7:
            puts("[PATRIOT-7] Session terminated.");
            return;
        default:
            puts("[PATRIOT-7] Unknown menu selection.");
            break;
        }
    }
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    banner();
    initialize_state();
    install_seccomp();
    menu_loop();
    return 0;
}
