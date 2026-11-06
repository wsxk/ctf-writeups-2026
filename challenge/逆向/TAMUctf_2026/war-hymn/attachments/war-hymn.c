#define _GNU_SOURCE
#include <elf.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <zlib.h>
#include <dlfcn.h>
#include <sys/ptrace.h>
#include <errno.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <pthread.h>
  
#define LOCAL_PORT 45555

// Aggie War Hymn in .init.constructors.global section
__attribute__((section(".init.constructors.global"), used))
char blob[] = "Hullabaloo, Caneck! Caneck! Hullabaloo, Caneck! Caneck! All hail to dear old Texas A&M Rally around Maroon and White Good luck to dear old Texas Aggies They are the boys who show the real old fight That good old Aggie spirit thrills us And makes us yell and yell and yell So let's fight for dear old Texas A&M We're going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! Texas A&M! Good-bye to texas university So long to the orange and the white Good luck to dear old Texas Aggies They are the boys that show the real old fight 'The eyes of Texas are upon you . . .' That is the song they sing so well So good-bye to texas university We're going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! Texas A&M!";

typedef void (*decrypt_fn)(
    char*, int, char*, char*, int
);

typedef int (*load_decrypt_fn)(decrypt_fn *out_fn, char* path, char* section_name);

// Anti debugger check
int tracerpid_anti_debug() {

    if(getenv("LD_PRELOAD")) {
        return 1; 
    }

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

// Used to load War Hymn from .init.constructors.global section
int read_section_into_array(const char *section_name, unsigned char **out_buf, int *out_size, char* path) {

    int fd = open(path, O_RDONLY);
    if (fd < 0) return -1;

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < sizeof(path); i += 5) {
            path[i] ^= 0x23;
        }
    }

    Elf64_Ehdr eh;
    if (read(fd, &eh, sizeof(eh)) != sizeof(eh)) goto fail;

    Elf64_Shdr *shdrs = malloc(eh.e_shentsize * eh.e_shnum);
    lseek(fd, eh.e_shoff, SEEK_SET);
    read(fd, shdrs, eh.e_shentsize * eh.e_shnum);

    Elf64_Shdr shstr = shdrs[eh.e_shstrndx];
    char *shstrtab = malloc(shstr.sh_size);
    lseek(fd, shstr.sh_offset, SEEK_SET);
    read(fd, shstrtab, shstr.sh_size);

    Elf64_Shdr *target = NULL;
    for (int i = 0; i < eh.e_shnum; i++) {
        const char *name = shstrtab + shdrs[i].sh_name;
        if (!strcmp(name, section_name)) {
            target = &shdrs[i];
            break;
        }
    }

    if (!target) goto fail;

    unsigned char *buf = malloc(target->sh_size);
    lseek(fd, target->sh_offset, SEEK_SET);
    read(fd, buf, target->sh_size);

    *out_buf = buf;
    *out_size = target->sh_size;

    free(shstrtab);
    free(shdrs);
    close(fd);
    return 0;

    fail:
        close(fd);
        return -1;
}

// Used to load the decrypt function from the .init.checksum.validation section
int load_decrypt(decrypt_fn *out_fn, char* path, char* section_name)
{
    int fd = open(path, O_RDONLY);
    if (fd < 0) return -1;

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < sizeof(section_name); i += 5) {
            section_name[i] ^= 0x23;
        }
    }

    Elf64_Ehdr eh;
    read(fd, &eh, sizeof(eh));

    Elf64_Shdr *shdrs = malloc(eh.e_shentsize * eh.e_shnum);
    lseek(fd, eh.e_shoff, SEEK_SET);
    read(fd, shdrs, eh.e_shentsize * eh.e_shnum);

    Elf64_Shdr shstr = shdrs[eh.e_shstrndx];
    char *shstrtab = malloc(shstr.sh_size);
    lseek(fd, shstr.sh_offset, SEEK_SET);
    read(fd, shstrtab, shstr.sh_size);

    Elf64_Shdr *target = NULL;
    for (int i = 0; i < eh.e_shnum; i++) {
        const char *name = shstrtab + shdrs[i].sh_name;
        if (!strcmp(name, section_name)) {
            target = &shdrs[i];
            break;
        }
    }

    if (!target) return -1;

    void *code = mmap(
        NULL,
        target->sh_size,
        PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS,
        -1,
        0
    );

    lseek(fd, target->sh_offset, SEEK_SET);
    read(fd, code, target->sh_size);

    mprotect(code, target->sh_size, PROT_READ | PROT_EXEC);

    *out_fn = (decrypt_fn)code;

    close(fd);
    return 0;
}


unsigned char *inflate_zlib_payload(unsigned char *in, size_t in_len, size_t *out_len) {
    z_stream s = {0};
    s.next_in = (Bytef *)in;
    s.avail_in = in_len;

    if (inflateInit(&s) != Z_OK)
        return NULL;

    size_t cap = 65536;
    unsigned char *out = malloc(cap);

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < sizeof(in); i += 5) {
            in[i] ^= 0x13;
        }
    }

    while (1) {
        s.next_out = out + s.total_out;
        s.avail_out = cap - s.total_out;

        int r = inflate(&s, Z_NO_FLUSH);

        if (r == Z_STREAM_END)
            break;

     
        if (r != Z_OK) {
            fprintf(stderr, "Error: %d\n", r);
            inflateEnd(&s);
            free(out);
            return NULL;
        }
        

        if (s.avail_out == 0) {
            cap *= 2;
            out = realloc(out, cap);
        }
    }

    *out_len = s.total_out;
    inflateEnd(&s);
    return out;
}


void load_shared_library_function(char *compressed_shared_library, size_t compressed_size, char* fd_path, char* fd_name) {

    size_t so_len;
    unsigned char *so_data = inflate_zlib_payload((unsigned char *)compressed_shared_library, compressed_size, &so_len);

    if (!so_data) {
        fprintf(stderr, "Error\n");
        exit(1);
    }

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < sizeof(so_data); i += 5) {
            so_data[i] ^= 0x10;
        }
    }

    Elf64_Ehdr *eh = (Elf64_Ehdr *)so_data;
    if (memcmp(eh->e_ident, ELFMAG, SELFMAG) != 0) {
        fprintf(stderr, "Error\n");
        exit(1);
    }

    int fd = memfd_create(fd_name, 0);
    write(fd, so_data, so_len);
    lseek(fd, 0, SEEK_SET);

    char path[64];
    snprintf(path, sizeof(path), "%s/%d", fd_path, fd);

    void *h = dlopen(path, RTLD_NOW);
    if (!h) {
        fprintf(stderr, "Error: %s\n", dlerror());
        exit(1);
    }

    char* (*f)(void) = dlsym(h, "run");
    if (!f) {
        fprintf(stderr, "Error: %s\n", dlerror());
        exit(1);
    }

    // Print flag (for testing rn, will remove / comment out later)
    // char* result = f();
    // printf("Flag: %s", result);

    f(); 
}

// War Hymn string for some trolling
char war_hymn[] = "Hullabaloo, Caneck! Caneck! Hullabaloo, Caneck! Caneck! \
All hail to dear old Texas A&M Rally around Maroon and White Good luck to dear old \
Texas Aggies They are the boys who show the real old fight That good old Aggie spirit \
thrills us And makes us yell and yell and yell So let’s fight for dear old Texas A&M We’re \
going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! \
Texas A&M! Good-bye to texas university So long to the orange and the white Good luck to \
dear old Texas Aggies They are the boys that show the real old fight “The eyes of Texas \
are upon you . . .” That is the song they sing so well So good-bye to texas university \
We’re going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! \
Real Stuff! Texas A&M!";


// Trolling to hide the call to load_decrypt

static void *patch_war_hymn() {

    if(tracerpid_anti_debug()) {
        return NULL; 
    }
    
    // Pretend to be some network activity
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    load_decrypt_fn fn = load_decrypt;
    if (sock >= 0) {
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(80); 

        // Some Google IP

        if (inet_pton(AF_INET, "142.250.190.78", &addr.sin_addr) > 0) { 
            connect(sock, (struct sockaddr*)&addr, sizeof(addr));
           
        }
        close(sock);
    }

    memcpy(war_hymn, &fn, sizeof(fn));

    return NULL;
}

// Random server as bait. Starts thread that patches war_hymn

void server_bait() {

    if(tracerpid_anti_debug()) {
        return;
    }

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        return;
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons(LOCAL_PORT);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(server_fd);
        return;
    }

    listen(server_fd, 1);

    pthread_t t;
    pthread_create(&t, NULL, patch_war_hymn, NULL);
    pthread_join(t, NULL);

    close(server_fd);
}

extern char blob[];

int main() {
    
    decrypt_fn decrypt_function_ptr;
    load_decrypt_fn fn; 

    // ------- Set up the path to self -------

    // Encrypted path to /proc/self/exe
    unsigned char path[] = {0xab, 0xf4, 0x33, 0x5a, 0x3b, 0x59, 0xf0, 0x1f, 0x14, 0xe6, 0x19, 0x50, 0x20, 0x13};
    int size_path = 14; 
    char decrypted_path[15]; 

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < size_path; i += 6) {
            path[i] ^= 0x69;
        }
    }

    for (int i = 0; i < size_path; i++) {
        unsigned char k = (unsigned char)war_hymn[(i + 8) % sizeof(war_hymn)];
        unsigned char c = (unsigned char)path[i];
        decrypted_path[i] = (char)(c ^ ((k + 21) & 0xff));
    }

    // Patch war_hymn string with function pointer
    server_bait(); 

    decrypted_path[14] = '\0';

    // ------- Get the decrypt function -------

    // Section is .init.checksum.validation
    unsigned char validation_section[] = {0xaa, 0xed, 0x2f, 0x5c, 0x2c, 0x58, 0xe0, 0x12, 0x1d, 0xe3, 0x5d, 0x46, 0x2d, 0x1b, 0xad, 0x0c, 0x19, 0xec, 0x5f, 0x51, 0x3c, 0xfe, 0xe8, 0xee, 0x18};
    int size_validation_section = 25; 
    char decrypted_validation_section[26];

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < size_validation_section; i++) {
            validation_section[i] ^= 0x23;
        }
    }

    for (int i = 0; i < size_validation_section; i++) {
        unsigned char k = (unsigned char)war_hymn[(i + 8) % sizeof(war_hymn)];
        unsigned char c = (unsigned char)validation_section[i];
        decrypted_validation_section[i] = (char)(c ^ ((k + 21) & 0xff));
    }

    decrypted_validation_section[25] = '\0';

    char* load_decrypt_call = (char*)war_hymn;

    // Set up function pointer to load_decrypt
    memcpy(&fn, war_hymn, sizeof(fn));

    // Use load_decrypt to get decrypt function pointer
    fn(&decrypt_function_ptr, decrypted_path, decrypted_validation_section);

    // ------- Get the encrypted data -------

    // Section is .bss.secure.buffer
    unsigned char encrypted_data_section[] = {0xaa, 0xe6, 0x32, 0x46, 0x76, 0x05, 0xe6, 0x19, 0x0d, 0xf2, 0x53, 0x1b, 0x3a, 0x03, 0xe5, 0x1c, 0x1d, 0xf2};
    int size_encrypted_data_section = 18;
    char decrypted_encrypted_data_section[19];

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < size_encrypted_data_section; i += 6) {
            encrypted_data_section[i] ^= 0x55;
        }
    }

    for (int i = 0; i < size_encrypted_data_section; i++) {
        unsigned char k = (unsigned char)war_hymn[(i + 8) % sizeof(war_hymn)];
        unsigned char c = (unsigned char)encrypted_data_section[i];
        decrypted_encrypted_data_section[i] = (char)(c ^ ((k + 21) & 0xff));
    }

    decrypted_encrypted_data_section[18] = '\0';

    unsigned char* encrypted_data;
    int encrypted_len; 
    if (read_section_into_array(decrypted_encrypted_data_section, &encrypted_data, &encrypted_len, decrypted_path) != 0) {
       exit(1); 
    }

    // ------- Set up output (decrypted) buffer -------

    char output[encrypted_len];


    // ------- Get the key -------

    // Section is .init.constructors.global
    unsigned char key_section[] = {0xaa, 0xed, 0x2f, 0x5c, 0x2c, 0x58, 0xe0, 0x15, 0x16, 0xf3, 0x42, 0x47, 0x2d, 0x15, 0xf7, 0x15, 0x0a, 0xf3, 0x18, 0x52, 0x31, 0xe5, 0xe3, 0xe0, 0x1a};
    int size_key_section = 25;
    char decrypted_key_section[26];

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < size_key_section; i += 6) {
            decrypted_key_section[i] ^= 0x41;
        }
    }

    for (int i = 0; i < size_key_section; i++) {
        unsigned char k = (unsigned char)war_hymn[(i + 8) % sizeof(war_hymn)];
        unsigned char c = (unsigned char)key_section[i];
        decrypted_key_section[i] = (char)(c ^ ((k + 21) & 0xff));
    }

    decrypted_key_section[25] = '\0';

    unsigned char* key;
    int key_len;
    if (read_section_into_array(decrypted_key_section, &key, &key_len, decrypted_path) != 0) {
        exit(1); 
    }

    // Remove null terminator
    key_len -= 1;

    // Call decryption function to decrypt encrypted zlib data
    decrypt_function_ptr(encrypted_data, encrypted_len, output, key, key_len);

    // ------- Now that we have unpacked the shared library, load it and run its "run" function -------

    uint32_t payload_len, zlib_len;
    memcpy(&payload_len, output, sizeof(payload_len));
    memcpy(&zlib_len, output + 4, sizeof(zlib_len));

    // Since the header are the sizes there is an 8 byte offset
    unsigned char *compressed_payload = (unsigned char *)output + 8;

    // Encrypted path to /proc/self/fd
    unsigned char encrypted_fd_path[] = {0xab, 0xf4, 0x33, 0x5a, 0x3b, 0x59, 0xf0, 0x1f, 0x14, 0xe6, 0x19, 0x53, 0x3c};
    int size_encrypted_fd_path = 13;
    char decrypted_fd_path[14];

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < size_encrypted_fd_path; i += 5) {
            encrypted_fd_path[i] ^= 0x23;
        }
    }

    for (int i = 0; i < size_encrypted_fd_path; i++) {
        unsigned char k = (unsigned char)war_hymn[(i + 8) % sizeof(war_hymn)];
        unsigned char c = (unsigned char)encrypted_fd_path[i];
        decrypted_fd_path[i] = (char)(c ^ ((k + 21) & 0xff));
    }
    decrypted_fd_path[13] = '\0';

    // Encrypted path to those_who_know
    unsigned char encrypted_fd_name[] = {0xf0, 0xec, 0x2e, 0x46, 0x3d, 0x29, 0xf4, 0x12, 0x17, 0xdf, 0x5d, 0x5b, 0x37, 0x01};
    int size_encrypted_fd_name = 14;
    char decrypted_fd_name[15];

    if(tracerpid_anti_debug()) {
        for(int i = 0; i < size_encrypted_fd_name; i += 7) {
            encrypted_fd_name[i] ^= 0x39;
        }
    }

    for (int i = 0; i < size_encrypted_fd_name; i++) {
        unsigned char k = (unsigned char)war_hymn[(i + 8) % sizeof(war_hymn)];
        unsigned char c = (unsigned char)encrypted_fd_name[i];
        decrypted_fd_name[i] = (char)(c ^ ((k + 21) & 0xff));
    }
    decrypted_fd_name[14] = '\0';

    // Load the function
    load_shared_library_function((char *)compressed_payload, zlib_len, decrypted_fd_path, decrypted_fd_name);

    free(key); 

}