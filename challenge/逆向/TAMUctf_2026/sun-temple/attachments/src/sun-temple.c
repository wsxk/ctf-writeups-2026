#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "generated_chamber.h"

#define SCALE 1000u
#define MIN_FACTOR 180u
#define MAX_RITES 12u

#define TYPE_FOCUS 1u
#define TYPE_INVOKE 2u
#define TYPE_DRAW 3u
#define TYPE_CARVE 4u
#define TYPE_MERGE 5u
#define TYPE_BLESS 6u
#define TYPE_GATE 7u
#define TYPE_SPARK 8u

typedef struct {
    uint8_t rites[MAX_RITES];
    uint8_t len;
    uint8_t pos[16];
} Pipeline;

typedef struct {
    uint8_t primary;
    uint8_t secondary;
    uint16_t p_mask;
    uint16_t s_mask;
} RiteDef;

static const uint16_t k_base_cost[9] = {
    0u, 12u, 10u, 8u, 7u, 5u, 4u, 3u, 2u,
};

static const uint16_t k_variant_weight[16] = {
    860u, 900u, 940u, 980u, 1010u, 1040u, 1070u, 1100u,
    930u, 970u, 1000u, 1030u, 1060u, 1090u, 1120u, 1160u,
};

static const uint16_t k_operand_weight[16] = {
    72u, 84u, 96u, 108u, 66u, 78u, 90u, 102u,
    114u, 126u, 138u, 150u, 70u, 82u, 94u, 106u,
};

static const int8_t k_primary_bias[16] = {
    -12, -8, 10, 6, 3, -2, -4, 9, -7, 4, 11, -3, 2, -5, 5, -1,
};

static const int8_t k_secondary_bias[16] = {
    -7, 5, 4, -3, 2, 1, -4, 6, -2, 3, 8, -1, 0, -5, 7, -6,
};

static const uint16_t k_primary_reduction[16] = {
    248u, 180u, 240u, 170u, 130u, 200u, 172u, 120u,
    142u, 212u, 162u, 166u, 152u, 111u, 220u, 176u,
};

static const uint16_t k_secondary_reduction[16] = {
    82u, 110u, 0u, 102u, 72u, 86u, 121u, 92u,
    94u, 0u, 131u, 84u, 100u, 106u, 151u, 116u,
};

static const RiteDef k_rites[16] = {
    {TYPE_FOCUS,  TYPE_SPARK, 0x04A4u, 0x9081u},
    {TYPE_DRAW,   TYPE_MERGE, 0x120Cu, 0x0222u},
    {TYPE_INVOKE, 0u,         0x2082u, 0x0000u},
    {TYPE_CARVE,  TYPE_BLESS, 0x4408u, 0x8140u},
    {TYPE_GATE,   TYPE_MERGE, 0x9006u, 0x0188u},
    {TYPE_FOCUS,  TYPE_BLESS, 0x0484u, 0x4220u},
    {TYPE_INVOKE, TYPE_DRAW,  0x0428u, 0x1840u},
    {TYPE_MERGE,  TYPE_SPARK, 0x8100u, 0x2090u},
    {TYPE_CARVE,  TYPE_GATE,  0x5010u, 0x1024u},
    {TYPE_BLESS,  0u,         0x2440u, 0x0000u},
    {TYPE_DRAW,   TYPE_FOCUS, 0x0C80u, 0x8811u},
    {TYPE_INVOKE, TYPE_GATE,  0x4009u, 0x2003u},
    {TYPE_MERGE,  TYPE_BLESS, 0x0242u, 0x1280u},
    {TYPE_SPARK,  TYPE_CARVE, 0x9410u, 0x2048u},
    {TYPE_FOCUS,  TYPE_INVOKE,0x08A0u, 0x0441u},
    {TYPE_DRAW,   TYPE_MERGE, 0x4210u, 0x4012u},
};

static uint64_t g_target = 3415150u;

__attribute__((noinline)) static uint8_t from_hex_char(char c) {
    if (c >= '0' && c <= '9') {
        return (uint8_t)(c - '0');
    }
    if (c >= 'a' && c <= 'f') {
        return (uint8_t)(10 + (c - 'a'));
    }
    if (c >= 'A' && c <= 'F') {
        return (uint8_t)(10 + (c - 'A'));
    }
    return 0xffu;
}

__attribute__((noinline)) static int parse_pipeline(const char *hex, Pipeline *p) {
    uint8_t seen_rite[16] = {0};
    uint8_t seen_slot[16] = {0};
    uint8_t slot_to_rite[16] = {0};
    size_t i = 0u;
    size_t n = strlen(hex);
    int state = 0;

    memset(p, 0, sizeof(*p));
    for (i = 0u; i < 16u; ++i) {
        p->pos[i] = 0xffu;
    }

    while (1) {
        switch (state) {
            case 0:
                if (n == 0u || (n & 1u) != 0u) {
                    return 0;
                }
                i = 0u;
                state = 1;
                break;
            case 1:
                if (i >= n) {
                    state = 3;
                    break;
                }
                {
                    uint8_t hi = from_hex_char(hex[i]);
                    uint8_t lo = from_hex_char(hex[i + 1u]);
                    if (hi == 0xffu || lo == 0xffu) {
                        return 0;
                    }
                    if (!seen_rite[hi] && !seen_slot[lo] && p->len < MAX_RITES) {
                        seen_rite[hi] = 1u;
                        seen_slot[lo] = 1u;
                        slot_to_rite[lo] = hi;
                        ++p->len;
                    }
                }
                i += 2u;
                break;
            case 3:
                if (p->len == 0u) {
                    return 0;
                }
                {
                    uint8_t out = 0u;
                    for (i = 0u; i < 16u; ++i) {
                        if (seen_slot[i] != 0u) {
                            uint8_t rite = slot_to_rite[i];
                            p->rites[out] = rite;
                            p->pos[rite] = out;
                            ++out;
                        }
                    }
                }
                return 1;
            default:
                return 0;
        }
    }
}

static uint16_t rite_reduction(uint8_t rite_id, uint8_t type, uint8_t variant) {
    const RiteDef *r = &k_rites[rite_id];
    int32_t red = 0;

    if (type == r->primary) {
        red = (int32_t)k_primary_reduction[rite_id] + (int32_t)k_primary_bias[variant];
        if ((r->p_mask & (1u << variant)) != 0u) {
            red += 22;
        }
    } else if (r->secondary != 0u && type == r->secondary) {
        red = (int32_t)k_secondary_reduction[rite_id] + (int32_t)k_secondary_bias[variant];
        if ((r->s_mask & (1u << variant)) != 0u) {
            red += 16;
        }
    }

    if (red < 0) {
        red = 0;
    }
    if (red > 460) {
        red = 460;
    }
    return (uint16_t)red;
}

static uint32_t apply_interactions(const Pipeline *p, uint8_t type, uint8_t variant, uint32_t factor) {
    const uint8_t *pos = p->pos;

    if (pos[0x0u] != 0xffu && pos[0x5u] != 0xffu && pos[0x0u] < pos[0x5u] && type == TYPE_FOCUS) {
        if (variant == 2u || variant == 7u || variant == 10u) {
            factor = (factor * 860u) / SCALE;
        }
    }

    if (pos[0x1u] != 0xffu && pos[0xfu] != 0xffu && pos[0x1u] < pos[0xfu] && type == TYPE_MERGE) {
        if (variant == 1u || variant == 9u) {
            factor = (factor * 900u) / SCALE;
        }
    }

    if (pos[0x2u] != 0xffu && pos[0x6u] != 0xffu && pos[0x2u] < pos[0x6u] && type == TYPE_INVOKE) {
        factor = (factor * 1080u) / SCALE;
    }

    if (pos[0x3u] != 0xffu && pos[0x8u] != 0xffu && pos[0x3u] < pos[0x8u] && type == TYPE_CARVE) {
        factor = (factor * 1060u) / SCALE;
    }

    if (pos[0xcu] != 0xffu && pos[0x7u] != 0xffu && pos[0xcu] < pos[0x7u] && type == TYPE_MERGE) {
        if (variant == 2u || variant == 9u || variant == 11u) {
            factor = (factor * 1070u) / SCALE;
        }
    }

    if (pos[0x1u] != 0xffu && pos[0xfu] != 0xffu && pos[0xcu] != 0xffu &&
        pos[0x1u] < pos[0xfu] && pos[0xfu] < pos[0xcu] && type == TYPE_MERGE) {
        if (variant == 1u || variant == 9u) {
            factor = (factor * 780u) / SCALE;
        }
    }

    if (pos[0x0u] != 0xffu && pos[0x5u] != 0xffu && pos[0xeu] != 0xffu &&
        pos[0x0u] < pos[0x5u] && pos[0x5u] < pos[0xeu] && type == TYPE_FOCUS) {
        if (variant == 2u || variant == 7u || variant == 10u) {
            factor = (factor * 800u) / SCALE;
        }
    }

    if (pos[0x4u] != 0xffu && pos[0x7u] != 0xffu && pos[0x9u] != 0xffu &&
        pos[0x4u] < pos[0x7u] && pos[0x7u] < pos[0x9u] && type == TYPE_GATE) {
        if (variant == 3u || variant == 6u || variant == 12u) {
            factor = (factor * 710u) / SCALE;
        }
    } else if (type == TYPE_GATE) {
        if (pos[0x4u] != 0xffu && pos[0x7u] != 0xffu && pos[0x4u] < pos[0x7u] && pos[0x9u] == 0xffu) {
            factor = (factor * 1060u) / SCALE;
        }
    }

    if (factor < MIN_FACTOR) {
        factor = MIN_FACTOR;
    }
    if (factor > SCALE) {
        factor = SCALE;
    }
    return factor;
}

__attribute__((noinline)) static uint64_t score_pipeline(const Pipeline *p) {
    uint64_t total = 0u;
    uint32_t idx = 0u;
    uint32_t state = 0u;

    while (1) {
        switch (state) {
            case 0u:
                idx = 0u;
                state = 1u;
                break;
            case 1u:
                if (idx >= CHAMBER_INSTRUCTIONS) {
                    return total;
                }
                {
                    uint8_t opcode = k_chamber_blob[idx * 3u];
                    uint8_t op1 = k_chamber_blob[idx * 3u + 1u];
                    uint8_t op2 = k_chamber_blob[idx * 3u + 2u];
                    uint8_t type = (uint8_t)(opcode >> 4u);
                    uint8_t var = (uint8_t)(opcode & 0x0fu);
                    uint32_t factor = SCALE;
                    uint32_t r = 0u;
                    uint32_t base_w;

                    for (r = 0u; r < p->len; ++r) {
                        uint8_t rite = p->rites[r];
                        uint16_t red = rite_reduction(rite, type, var);
                        if (red != 0u) {
                            factor = (factor * (SCALE - red)) / SCALE;
                        }
                    }

                    factor = apply_interactions(p, type, var, factor);
                    base_w = (uint32_t)(k_base_cost[type] * k_variant_weight[var]);
                    base_w += (uint32_t)k_operand_weight[(op1 ^ op2) & 0x0fu];
                    base_w += (uint32_t)(((op1 & 0x3u) + (op2 & 0x3u)) * 7u);

                    total += ((uint64_t)base_w * (uint64_t)factor) / SCALE;
                }
                ++idx;
                break;
            default:
                return total;
        }
    }
}

static uint64_t baseline_score(void) {
    Pipeline empty;
    memset(&empty, 0, sizeof(empty));
    for (size_t i = 0; i < 16; ++i) {
        empty.pos[i] = 0xffu;
    }
    return score_pipeline(&empty);
}

static int print_flag_from_file(void) {
    FILE *fp = fopen("flag.txt", "r");
    char line[256];
    size_t n;

    if (fp == NULL) {
        puts("flag missing; contact admin");
        return 1;
    }

    if (fgets(line, sizeof(line), fp) == NULL) {
        fclose(fp);
        puts("flag missing; contact admin");
        return 1;
    }

    fclose(fp);
    puts(line);
    return 0;
}

int main(void) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    Pipeline p;
    uint64_t score;
    char input[512];
    size_t n;

    printf("we await your offering> ");
    if (fgets(input, sizeof(input), stdin) == NULL) {
        puts("ritual rejected");
        return 1;
    }
    input[strcspn(input, "\r\n")] = 0;

    if (!parse_pipeline(input, &p)) {
        puts("ritual rejected");
        return 1;
    }

    score = score_pipeline(&p);

    if (score > g_target) {
        puts("the altar remains dark");
        return 1;
    }

    return print_flag_from_file();
}
