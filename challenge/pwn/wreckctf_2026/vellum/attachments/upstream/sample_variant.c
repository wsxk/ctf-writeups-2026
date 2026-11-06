#include <stdio.h>
#include <stdint.h>
#include <string.h>

static char margin_pre[42];
uint32_t   seal;
static char margin_post[132];

__attribute__((noinline))
int break_seal(void) {
    if (seal == 0xec683a59u) return 1;
    return 0;
}

static void reveal_relic(void) {
    FILE *f = fopen("/app/flag.txt", "r");
    if (!f) { puts("relic not found"); return; }
    char buf[256];
    size_t n = fread(buf, 1, sizeof(buf) - 1, f);
    buf[n] = 0;
    fputs(buf, stdout);
    fclose(f);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);

    volatile uint64_t p0 = (uint64_t)(uintptr_t)(void*)&reveal_relic, p1 = 0x5dc687404815484eUL, p2 = 0x6b5952cd19bb33bUL, p3 = 0x6069bbcb7dcd9f72UL, p4 = 0x5f769effe62366e3UL;
    (void)p0; (void)p1; (void)p2; (void)p3; (void)p4;
    
    margin_pre[0] = 0; margin_post[0] = 0;

    char quill[128];
    puts("inkwell full; the abbot listens.");

    puts("folio 1/2");
    if (!fgets(quill, sizeof(quill), stdin)) return 1;
    quill[strcspn(quill, "\n")] = 0;
    printf(quill);
    putchar('\n');

    puts("folio 2/2");
    if (!fgets(quill, sizeof(quill), stdin)) return 1;
    quill[strcspn(quill, "\n")] = 0;
    printf(quill);
    putchar('\n');

    if (break_seal()) reveal_relic();
    else              puts("the seal holds");
    return 0;
}
