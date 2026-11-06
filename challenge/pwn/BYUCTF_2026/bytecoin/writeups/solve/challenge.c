#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <sys/random.h>

#include <wolfssl/options.h>
#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/wolfcrypt/hash.h>
#include <wolfssl/wolfcrypt/aes.h>
#include <wolfssl/wolfcrypt/chacha.h>
#include <wolfssl/wolfcrypt/chacha20_poly1305.h>
#include <wolfssl/wolfcrypt/hmac.h>

// compile with `gcc challenge.c -lwolfssl -fstack-protector -o challenge`

byte chaChaKey[32] = {0};
byte hmacKey[32] = {0};
char flag[32] = {0};

__attribute__((constructor)) void flush_buf() {
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
}

// Prints the contents of the array result in hexadecmial format
void print_hex_array(const unsigned char result[], int len) {
    for (int i = 0; i < len; i++) {
        printf("%02x", result[i]);
    }
    printf("\n");
}

// Scans up to max_len bytes of stdin and places in the array result
// Returns the amount of bytes scanned in, up to the newline character
// Assumes the result array is initialized with zeros and length max_len
int scan_hex_array(unsigned char result[], int max_len) {
    int buf_size = 2*max_len + 2;
    char* buf = calloc(buf_size, 1);
    if (buf == NULL) {
        printf("[!] Memory allocation unsuccessful. Quitting...\n");
        exit(1);
    }

    // Read in the contents of stdin as a string + '\n' + '\0'
    // Then replace the newline with '\0'
    int n_read = 0;
    if (fgets(buf, buf_size, stdin)) {
        buf[strcspn(buf, "\n")] = 0;
        for (int i = 0; i < max_len; i++) {
            if (buf[2*i] == '\0') {
                break;
            }
            if (buf[2*i+1] == '\0') {
                printf("[!] Extra nibble detected, aborting\n");
                exit(1);
            }
            unsigned int val = 0;
            n_read++;
            if (sscanf(&buf[2*i], "%2x", &val) == 1) {
                result[i] = (unsigned char)val;
            } else {
                printf("[!] Invalid hex input detected\n");
                break;
            }
        }
    }
    free(buf);
    return n_read;
}

// Constant-time tag comparison
int crypto_memcmp(const void * in_a, const void * in_b, size_t len) {
    size_t i;
    const volatile unsigned char *a = in_a;
    const volatile unsigned char *b = in_b;
    unsigned char x = 0;

    for (i = 0; i < len; i++)
        x |= a[i] ^ b[i];

    return x;
}

int bytecoin() {
    printf("[+] My authenticated encryption is so secure, there's no way you can steal my bytecoin flag! I even added an HMAC tag!\n");
    printf("[+] Note all hexadecimal inputs should be formatted like Python's .hex() method, e.g. 0123456789abcdef\n");

    const byte iv[12] = {'0','1','2','3','4','5','6','7','8','9','a','b'};
    const byte dummy_aad = 0;
    byte chaChaCipher[32] = {0};
    byte chaChaAuth[16] = {0};

    if (wc_ChaCha20Poly1305_Encrypt(chaChaKey, iv, &dummy_aad, 0, flag, sizeof(flag), chaChaCipher, chaChaAuth) != 0) {
        printf("[!] Encryption error\n");
        return -1;
    }

    typedef struct __attribute__((packed)) {
        byte cipher[32];
        byte authTag[16];
    } data_packet;

    byte buffer[32] = {0};

    Hmac hmac1;
    byte hmacDigest1[SHA256_DIGEST_SIZE];

    memcpy(buffer, hmacKey, 32);

    data_packet data1 = {0, 0};
    memcpy(data1.cipher, chaChaCipher, 32);
    memcpy(data1.authTag, chaChaAuth, 16);

    wc_HmacSetKey(&hmac1, SHA256, buffer, sizeof(buffer));
    wc_HmacUpdate(&hmac1, (byte*)&data1, sizeof(data1));
    wc_HmacFinal(&hmac1, hmacDigest1);

    printf("[+] Encrypted data: ");
    print_hex_array(chaChaCipher, sizeof(chaChaCipher));
    printf("[+] Poly1305 authentication tag: ");
    print_hex_array(chaChaAuth, sizeof(chaChaAuth));
    printf("[+] HMAC tag: ");
    print_hex_array(hmacDigest1, sizeof(hmacDigest1));

    byte ciphertext[32] = {0};
    byte my_iv[12] = {0};
    byte poly1305[16] = {0};
    byte hmacTag[32] = {0};

    printf(">>> Enter a ciphertext to decrypt:\n");
    int messageLen = scan_hex_array(buffer, sizeof(ciphertext));
    memcpy(ciphertext, buffer, messageLen);

    printf(">>> Enter an IV for the message:\n");
    int ivLen = scan_hex_array(buffer, sizeof(my_iv));
    memcpy(my_iv, buffer, ivLen);

    if (ivLen != sizeof(my_iv)) {
        printf("[!] Invalid IV length\n");
        return -1;
    }

    printf(">>> Enter a Poly1305 authentication tag for the message:\n");
    int authTagLen = scan_hex_array(buffer, sizeof(poly1305));
    memcpy(poly1305, buffer, authTagLen);

    if (authTagLen != sizeof(poly1305)) {
        printf("[!] Invalid Poly1305 authentication tag length\n");
        return -1;
    }

    printf(">>> Enter an HMAC tag for the message:\n");
    int hmacLen = scan_hex_array(buffer, sizeof(hmacTag));
    memcpy(hmacTag, buffer, hmacLen);

    if (hmacLen != sizeof(hmacTag)) {
        printf("[!] Invalid HMAC tag length\n");
        return -1;
    }

    printf("[+] Decrypting message ");
    print_hex_array(ciphertext, messageLen);

    memcpy(buffer, hmacKey, 32);

    data_packet data2 = {0, 0};
    memcpy(data2.cipher, ciphertext, messageLen);
    memcpy(data2.authTag, poly1305, 16);

    Hmac hmac2;
    byte hmacDigest2[SHA256_DIGEST_SIZE];

    wc_HmacSetKey(&hmac2, SHA256, buffer, sizeof(buffer));
    wc_HmacUpdate(&hmac2, (byte*)&data2, sizeof(data2));
    wc_HmacFinal(&hmac2, hmacDigest2);

    if (crypto_memcmp(hmacTag, hmacDigest2, 32) != 0) {
        printf("[!] Invalid HMAC tag!\n");
        memset(buffer, 0, sizeof(buffer));
        return -1;
    }

    byte plaintext[32] = {0};
    int result = wc_ChaCha20Poly1305_Decrypt(chaChaKey, my_iv, &dummy_aad, 0, ciphertext, messageLen, poly1305, plaintext);

    if (plaintext[0] == 'b' && plaintext[1] == 'y' && plaintext[2] == 'u') {
        printf("[!] Nope! You aren't allowed to decrypt my bytecoin flag!\n");
        return -1;
    }
    
    printf("[+] Congrats! Here's your message:\n");
    print_hex_array(plaintext, messageLen);

    return -1;
}

void generate_key(byte* buf, int buf_len) {
    int ret = getrandom(buf, buf_len, 0);
    if (ret < 0) {
        printf("[!] getrandom call failed\n");
        exit(1);
    }
}

int main() {
    // Generate keys
    generate_key(chaChaKey, sizeof(chaChaKey));
    generate_key(hmacKey, sizeof(hmacKey));

    // Open flag.txt
    FILE *file = fopen("flag.txt", "r");
    fgets(flag, sizeof(flag), file);
    fclose(file);

    for (int i = 1; i <= 33; i++) {
        bytecoin();
    }
}