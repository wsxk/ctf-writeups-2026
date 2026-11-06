#ifndef LOADER_ABI_H
#define LOADER_ABI_H

#include <stddef.h>
#include <stdint.h>

typedef enum {
	ACTION_PREPEND = 0,
	ACTION_APPEND = 1,
	ACTION_REPLACE = 2,
	ACTION_REMOVE = 3,
	ACTION_EXECUTE = 4,
	ACTION_TERMINAL = 5
} loader_action_t;

typedef struct {
	uint8_t hash[32];
	uint8_t action_type;
	uint8_t reserved0;
	uint16_t reserved1;
	uint32_t arg0;
	uint32_t arg1;
	uint32_t arg2;
	uint32_t chunk_id;
} loader_rule_t;

typedef struct {
	uint32_t expect_stage_id;
	uint32_t expect_token;
	uint32_t expect_io0;
	uint32_t expect_io1;
	uint32_t expect_active_len;
	uint8_t expect_active_sha256[32];
} loader_terminal_t;

typedef struct {
	uint32_t digest[4];
	uint32_t next_token;
	uint32_t score;
} inner_result_t;

typedef int (*stage_fn_t)(const uint8_t*, size_t, uint32_t, void*);

#endif
