void decrypt(char *in, int in_len, char *out, char *key, int key_len) {
    unsigned char ks = 0x67;   

    for (int i = 0; i < in_len; i++) {
        unsigned char k = (unsigned char)key[i % key_len];
        ks = (unsigned char)((ks + k + i) & 0xff);
        out[i] = (char)((unsigned char)in[i] ^ ks);
    }
}
