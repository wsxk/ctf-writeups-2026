#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static const unsigned char key[] = "AggiesAggiesAggies";

// Function names are changed to kinda hide what they're doing

// Anti debugger check
int tracerpid_anti_debug() {

    FILE *f = fopen("/proc/self/status", "r");
    if (!f) return 0;

    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (!strncmp(line, "TracerPid:", 10)) {
            int pid = atoi(line + 10);
            fclose(f);
            return pid != 0;
        }
    }

    fclose(f);
    return 0;
}

/* ---------- RC4 ---------- */

void perform_check(const unsigned char *key, size_t keylen,
               unsigned char *data, size_t len)
{
    unsigned char S[256];
    int i, j = 0;

    for (i = 0; i < 256; i++)
        S[i] = i;

    /* KSA */
    for (i = 0; i < 256; i++) {
        j = (j + S[i] + key[i % keylen]) & 0xff;
        unsigned char tmp = S[i];
        S[i] = S[j];
        S[j] = tmp;
    }

    /* PRGA */
    i = j = 0;
    for (size_t n = 0; n < len; n++) {
        i = (i + 1) & 0xff;
        j = (j + S[i]) & 0xff;
        unsigned char tmp = S[i];
        S[i] = S[j];
        S[j] = tmp;

        unsigned char K = S[(S[i] + S[j]) & 0xff];
        data[n] ^= K;
    }
}

/* ---------- Encrypted blobs (paste from make_encrypted_rc4.py) ---------- */

unsigned char data1[] = {
0xc1, 0x4f, 0x8d, 0xde, 0xbd, 0x20, 0x4f, 0x7d, 0x21, 0x7c, 0x03, 0x8b, 0xf0, 0xa7, 0x4a, 0x29, 0xa5, 0xf6
};

unsigned char data2[] = {
0xd3, 0x4f, 0x89, 0xc6, 0xb1, 0x67, 0x54, 0x7c, 0x26, 0x68, 0x03, 0x88, 0xeb, 0xbc, 0x56
};

unsigned char data3[] = {
0xd9, 0x58, 0x89, 0x96, 0xe6, 0x65, 0x1b, 0x61, 0x20, 0x6a, 0x51, 0x8f, 0xb9, 0xb0, 0x5b, 0x7d, 0xf3
};

unsigned char DAT_00104110[] = {
0xff, 0x43, 0x8b, 0xd3, 0xfc, 0x7b, 0x48, 0x7d, 0x78, 0x7a, 0x4f, 0x8e, 0xc6, 0xa1, 0x0a, 0x7f, 0xff, 0xdd, 0x98, 0x98, 0x70, 0xe1, 0x64, 0xd5, 0xa8, 0x1b, 0x7f, 0x45, 0x2a, 0xa6, 0x3e, 0xe2, 0x4a, 0x96, 0x36, 0xd5, 0x22, 0xc2, 0xc2, 0xb7, 0xb0, 0xa4, 0x80, 0xc4, 0x09, 0x8c, 0x50, 0xdc, 0xb5, 0x64, 0x71, 0x53
};

// Decoy functions to decrypt decoy blobs

void check1(void)
{
    perform_check(key, sizeof(key)-1,
                  data1, sizeof(data1));
}

void check2(void) {
    perform_check(key, sizeof(key)-1,
                  data2, sizeof(data2));
}

void check3(void) {
    perform_check(key, sizeof(key)-1,
                  data3, sizeof(data3));
}

/* ---------- Exported function ---------- */

__attribute__((visibility("default")))
void *run(void)
{
    static int decrypted = 0;
    static unsigned char DAT_001040e8[64];

    if (!decrypted) {
        /* Decrypt decoys first */ 

        if(tracerpid_anti_debug()) {
            for(int i = 0; i < sizeof(key); i++) {
                ((unsigned char *)key)[i] ^= 0x13;
            }
        }
        
        check1(); 
        check2();
        check3();

        /* Decrypt the flag itself */
        memcpy(DAT_001040e8, DAT_00104110, sizeof(DAT_00104110));
        perform_check(key, sizeof(key)-1,
                  DAT_001040e8, sizeof(DAT_00104110));

        if(tracerpid_anti_debug()) {
            for(int i = 0; i < sizeof(DAT_001040e8); i++) {
                ((unsigned char *)DAT_001040e8)[i] ^= 0x21;
            }
        }

        decrypted = 1;
    }

    // Will remove this return later, just here for testing
    //return (char *)DAT_001040e8;
}
