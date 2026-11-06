#include <stddef.h>
#include <stdint.h>

#include "inner_expected.h"
#include "loader_abi.h"

static uint32_t rotl32(uint32_t x, uint32_t r) {
    return (x << (r & 31u)) | (x >> ((32u - r) & 31u));
}

static uint32_t rotr32(uint32_t x, uint32_t r) {
    return (x >> (r & 31u)) | (x << ((32u - r) & 31u));
}

static uint32_t is_body_char(uint8_t c) {
    uint32_t az = (uint32_t)(c >= 'a' && c <= 'z');
    uint32_t num = (uint32_t)(c >= '0' && c <= '9');
    uint32_t us = (uint32_t)(c == '_');
    return az | num | us;
}

static uint8_t expected_body_byte(size_t idx) {
    uint64_t w;
    size_t off;

    if (idx >= INNER_BODY_LEN) {
        return 0u;
    }

    if (idx < 8u) {
        w = INNER_EXPECT_WORD_0;
        off = idx;
    } else if (idx < 16u) {
        w = INNER_EXPECT_WORD_1;
        off = idx - 8u;
    } else if (idx < 24u) {
        w = INNER_EXPECT_WORD_2;
        off = idx - 16u;
    } else if (idx < 32u) {
        w = INNER_EXPECT_WORD_3;
        off = idx - 24u;
    } else {
        w = INNER_EXPECT_WORD_4;
        off = idx - 32u;
    }

    return (uint8_t)((w >> (off * 8u)) & 0xffu);
}

int inner_entry(const uint8_t* input, size_t len, uint32_t stage_token, void* out_ctx) {
    inner_result_t* out = (inner_result_t*)out_ctx;
    uint32_t bad = 0u;
    uint32_t score = 0u;
    uint32_t state;
    uint32_t acc;
    size_t i;

    if (!input || !out) {
        return 0;
    }

    /* gigem{this_will_be_the_flag_for_challenge_7} => 44 total bytes */
    {
        const size_t expected_len = 44u;
        bad |= (uint32_t)(len != expected_len);

        if (len >= expected_len) {
            bad |= (uint32_t)(input[0] != 'g');
            bad |= (uint32_t)(input[1] != 'i');
            bad |= (uint32_t)(input[2] != 'g');
            bad |= (uint32_t)(input[3] != 'e');
            bad |= (uint32_t)(input[4] != 'm');
            bad |= (uint32_t)(input[5] != '{');
            bad |= (uint32_t)(input[expected_len - 1u] != '}');
        }
    }

    state = stage_token ^ 0xC0DEF00Du;
    acc = 0x31415926u;

    for (i = 0u; i < INNER_BODY_LEN && (6u + i) < len; i++) {
        uint8_t ch = input[6u + i];
        uint32_t ok = is_body_char(ch);
        uint32_t key;
        uint32_t add;
        uint32_t t;

        bad |= (ok ^ 1u);
        score += ok;

        state = state + 0x9E3779B9u + (uint32_t)i * 0x045D9F3Bu;
        state = rotl32(state, 5u) ^ rotr32(state, 3u);
        key = (state ^ (state >> 8u) ^ ((uint32_t)i * 17u)) & 0xffu;
        add = ((state >> 16u) + (uint32_t)i * 11u) & 0xffu;
        t = (((uint32_t)ch ^ key) + add) & 0xffu;

        bad |= (t ^ (uint32_t)expected_body_byte(i));
        acc = rotl32(acc ^ t ^ (uint32_t)i, 3u) + 0x01020304u + (t * 13u);
    }

    bad |= (acc ^ INNER_EXPECT_ACC);

    out->digest[0] = state ^ 0x13579BDFu;
    out->digest[1] = acc ^ 0x2468ACE0u;
    out->digest[2] = rotl32(state, 7u) ^ rotr32(acc, 5u);
    out->digest[3] = rotr32(state, 11u) + rotl32(acc, 3u);
    out->next_token = (out->digest[0] ^ rotl32(out->digest[1], 5u) ^ rotr32(out->digest[2], 9u) ^ out->digest[3]) + 0x9E3779B9u + score;
    out->score = score;

    return (bad == 0u) ? 1 : 0;
}
