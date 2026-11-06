#define _XOPEN_SOURCE_EXTENDED 1

#include <ctype.h>
#include <errno.h>
#include <locale.h>
#include <math.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <wchar.h>
#include <wctype.h>
#include <zlib.h>

#include <ncursesw/ncurses.h>

#define WORLD_H 32
#define WORLD_W 512
#define WORLD_W_MIN 64
#define VIEW_H 32
#define VIEW_W 64
#define MAX_ENTITIES 32

typedef enum {
    GAME_QUIT = 0,
    GAME_WIN = 1,
    GAME_LOSE = 2,
} GameResult;

enum {
    TILE_AIR = 0,
    TILE_GROUND = 1,
    TILE_PLATFORM = 2,
    TILE_STONE = 3,
    TILE_BRICK = 4,
    TILE_QUESTION = 5,
    TILE_CLOUD = 6,
    TILE_TREE = 7,
    TILE_FLOWER = 8,
    TILE_FLAGPOLE = 9,
    TILE_FLAG = 10,
    TILE_COUNT
};

enum {
    ENTITY_ALIEN = 1,
    ENTITY_SLIME = 2,
    ENTITY_ROBOT = 3,
    ENTITY_SNAIL = 4,
    ENTITY_BAT = 5,
    ENTITY_MONSTER = 6,
    ENTITY_MUSHROOM = 7,
    ENTITY_MAX_ID = ENTITY_MUSHROOM,
};

typedef struct {
    float x;
    float y;
    float vx;
    float vy;
    bool on_ground;
    int health;
    int dir;
    float hurt_timer;
    int type;
    float anchor_y;
    float ai_timer;
} Entity;

static uint8_t (*world)[WORLD_W];
static size_t world_size;
static Entity level_entities[MAX_ENTITIES];
static int level_entity_count = 0;
static float level_player_x = 5.0f;
static float level_player_y = 30.0f;
static int level_width = WORLD_W;
static bool developer_mode = false;
static bool spawn_mushroom_request = false;
static int spawn_mushroom_x = 0;
static int spawn_mushroom_y = 0;

static const wchar_t *tile_glyphs[TILE_COUNT] = {
    L"  ",
    L"🟫",
    L"🟧",
    L"⬛",
    L"🧱",
    L"❓",
    L"☁️",
    L"🌳",
    L"🌼",
    L"|",
    L"🚩",
};

static const wchar_t *error_glyph = L"❗";
static const wchar_t *heart_glyph = L"💖";
static const wchar_t *cursor_glyph = L"X ";
static const int tile_cell_width = 2;

static const wchar_t *player_glyph_for_health(int health) {
    if (health >= 3) {
        return L"😄";
    }
    if (health == 2) {
        return L"🙂";
    }
    if (health == 1) {
        return L"😐";
    }
    return L"🙁";
}

static bool entities_overlap(const Entity *a, const Entity *b) {
    return a->x < b->x + 1.0f && a->x + 1.0f > b->x &&
           a->y < b->y + 1.0f && a->y + 1.0f > b->y;
}

typedef struct {
    char *data;
    size_t len;
    size_t cap;
} StringBuilder;

typedef struct {
    wint_t left;
    wint_t right;
    wint_t up;
    wint_t down;
    wint_t quit;
    wint_t clear_block;
    wint_t edit_block;
    wint_t delete_entity;
    wint_t modify_entity;
    wint_t save_level;
    wint_t set_width;
} KeyBindings;

static const char *tile_name(uint8_t tile) {
    switch (tile) {
    case TILE_AIR:
        return "Air";
    case TILE_GROUND:
        return "Ground";
    case TILE_PLATFORM:
        return "Platform";
    case TILE_STONE:
        return "Stone";
    case TILE_BRICK:
        return "Brick";
    case TILE_QUESTION:
        return "Question";
    case TILE_CLOUD:
        return "Cloud";
    case TILE_TREE:
        return "Tree";
    case TILE_FLOWER:
        return "Flower";
    case TILE_FLAGPOLE:
        return "Flagpole";
    case TILE_FLAG:
        return "Flag";
    default:
        return "Unknown";
    }
}

static const wchar_t *tile_glyph(uint8_t tile) {
    if (tile < TILE_COUNT) {
        return tile_glyphs[tile];
    }
    return error_glyph;
}

static void draw_tile_at(int y, int x, uint8_t tile) {
    if (tile == TILE_FLAGPOLE) {
        if (has_colors()) {
            attron(COLOR_PAIR(4) | A_BOLD);
        } else {
            attron(A_BOLD);
        }
    }
    mvaddwstr(y, x, tile_glyph(tile));
    if (tile == TILE_FLAGPOLE) {
        if (has_colors()) {
            attroff(COLOR_PAIR(4) | A_BOLD);
        } else {
            attroff(A_BOLD);
        }
    }
}

static void draw_box(int x, int y, int w, int h) {
    if (w < 2 || h < 2) {
        return;
    }
    mvaddch(y, x, ACS_ULCORNER);
    mvaddch(y, x + w - 1, ACS_URCORNER);
    mvaddch(y + h - 1, x, ACS_LLCORNER);
    mvaddch(y + h - 1, x + w - 1, ACS_LRCORNER);
    for (int i = 1; i < w - 1; ++i) {
        mvaddch(y, x + i, ACS_HLINE);
        mvaddch(y + h - 1, x + i, ACS_HLINE);
    }
    for (int i = 1; i < h - 1; ++i) {
        mvaddch(y + i, x, ACS_VLINE);
        mvaddch(y + i, x + w - 1, ACS_VLINE);
    }
}

typedef struct {
    int id;
    const char *name;
    const wchar_t *glyph;
} EntityInfo;

static const EntityInfo entity_infos[] = {
    {ENTITY_ALIEN, "Alien", L"👽"},
    {ENTITY_SLIME, "Slime", L"🟢"},
    {ENTITY_ROBOT, "Robot", L"🤖"},
    {ENTITY_SNAIL, "Snail", L"🐌"},
    {ENTITY_BAT, "Bat", L"🦇"},
    {ENTITY_MONSTER, "Monster", L"👾"},
    {ENTITY_MUSHROOM, "Mushroom", L"🍄"},
};

static const EntityInfo *get_entity_info(int type) {
    for (size_t i = 0; i < sizeof(entity_infos) / sizeof(entity_infos[0]); ++i) {
        if (entity_infos[i].id == type) {
            return &entity_infos[i];
        }
    }
    return NULL;
}

static const char *entity_name(int type) {
    const EntityInfo *info = get_entity_info(type);
    return info ? info->name : "Unknown";
}

static const wchar_t *entity_glyph(int type) {
    const EntityInfo *info = get_entity_info(type);
    return info ? info->glyph : L"?";
}

static float rand_range(float min_val, float max_val) {
    float t = (float)rand() / (float)RAND_MAX;
    return min_val + (max_val - min_val) * t;
}

static bool has_entity_at(const Entity *entities, int entity_count, int x, int y) {
    for (int i = 0; i < entity_count; ++i) {
        if ((int)floorf(entities[i].x) == x && (int)floorf(entities[i].y) == y) {
            return true;
        }
    }
    return false;
}

static void spawn_mushroom(Entity *entities, int *entity_count, const Entity *player, int x, int y) {
    if (x < 0 || x >= level_width || y < 0 || y >= WORLD_H) {
        return;
    }
    if (world[y][x] != TILE_AIR) {
        return;
    }
    if (has_entity_at(entities, *entity_count, x, y)) {
        return;
    }
    if (player && (int)floorf(player->x) == x && (int)floorf(player->y) == y) {
        return;
    }
    if (*entity_count >= MAX_ENTITIES) {
        return;
    }

    entities[*entity_count] = (Entity){
        .x = (float)x,
        .y = (float)y,
        .vx = 0.0f,
        .vy = 0.0f,
        .on_ground = false,
        .health = 0,
        .dir = (player && player->x < (float)x) ? -1 : 1,
        .hurt_timer = 0.0f,
        .type = ENTITY_MUSHROOM,
        .anchor_y = (float)y,
        .ai_timer = 0.0f,
    };
    (*entity_count)++;
}

static bool sb_ensure(StringBuilder *sb, size_t extra) {
    if (sb->len + extra + 1 <= sb->cap) {
        return true;
    }
    size_t new_cap = sb->cap ? sb->cap * 2 : 1024;
    while (new_cap < sb->len + extra + 1) {
        new_cap *= 2;
    }
    char *next = realloc(sb->data, new_cap);
    if (!next) {
        return false;
    }
    sb->data = next;
    sb->cap = new_cap;
    return true;
}

static bool sb_append(StringBuilder *sb, const char *text) {
    size_t add = strlen(text);
    if (!sb_ensure(sb, add)) {
        return false;
    }
    memcpy(sb->data + sb->len, text, add);
    sb->len += add;
    sb->data[sb->len] = '\0';
    return true;
}

static bool sb_appendf(StringBuilder *sb, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    va_list copy;
    va_copy(copy, args);
    int needed = vsnprintf(NULL, 0, fmt, copy);
    va_end(copy);
    if (needed < 0) {
        va_end(args);
        return false;
    }
    if (!sb_ensure(sb, (size_t)needed)) {
        va_end(args);
        return false;
    }
    vsnprintf(sb->data + sb->len, sb->cap - sb->len, fmt, args);
    va_end(args);
    sb->len += (size_t)needed;
    return true;
}

static char *base64_encode(const unsigned char *data, size_t len, size_t *out_len) {
    static const char table[] =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    size_t enc_len = ((len + 2) / 3) * 4;
    char *out = malloc(enc_len + 1);
    if (!out) {
        return NULL;
    }
    size_t i = 0;
    size_t j = 0;
    while (i < len) {
        size_t remain = len - i;
        unsigned int octet_a = data[i++];
        unsigned int octet_b = remain > 1 ? data[i++] : 0;
        unsigned int octet_c = remain > 2 ? data[i++] : 0;
        unsigned int triple = (octet_a << 16) | (octet_b << 8) | octet_c;

        out[j++] = table[(triple >> 18) & 0x3F];
        out[j++] = table[(triple >> 12) & 0x3F];
        out[j++] = (remain > 1) ? table[(triple >> 6) & 0x3F] : '=';
        out[j++] = (remain > 2) ? table[triple & 0x3F] : '=';
    }
    out[j] = '\0';
    if (out_len) {
        *out_len = j;
    }
    return out;
}

static void set_default_keys(KeyBindings *keys) {
    keys->left = L'a';
    keys->right = L'd';
    keys->up = L'w';
    keys->down = L's';
    keys->quit = L'q';
    keys->clear_block = L'c';
    keys->edit_block = L'e';
    keys->delete_entity = L'd';
    keys->modify_entity = L'm';
    keys->save_level = L's';
    keys->set_width = L'w';
}

static void clear_world(void) {
    for (int y = 0; y < WORLD_H; ++y) {
        for (int x = 0; x < WORLD_W; ++x) {
            world[y][x] = TILE_AIR;
        }
    }
    level_width = WORLD_W;
}

static unsigned char *base64_decode(const char *input, size_t *out_len) {
    int table[256];
    for (int i = 0; i < 256; ++i) {
        table[i] = -1;
    }
    for (int i = 'A'; i <= 'Z'; ++i) table[i] = i - 'A';
    for (int i = 'a'; i <= 'z'; ++i) table[i] = i - 'a' + 26;
    for (int i = '0'; i <= '9'; ++i) table[i] = i - '0' + 52;
    table[(unsigned char)'+'] = 62;
    table[(unsigned char)'/'] = 63;

    size_t cap = strlen(input) * 3 / 4 + 4;
    unsigned char *out = malloc(cap);
    if (!out) {
        return NULL;
    }
    size_t out_idx = 0;

    int quad[4];
    int quad_len = 0;
    for (const char *p = input; *p; ++p) {
        unsigned char c = (unsigned char)*p;
        if (isspace(c)) {
            continue;
        }
        if (c == '=') {
            quad[quad_len++] = -2;
        } else {
            int val = table[c];
            if (val < 0) {
                continue;
            }
            quad[quad_len++] = val;
        }
        if (quad_len == 4) {
            int a = quad[0];
            int b = quad[1];
            int cval = quad[2];
            int d = quad[3];
            if (a < 0 || b < 0) {
                break;
            }
            out[out_idx++] = (unsigned char)((a << 2) | (b >> 4));
            if (cval >= 0) {
                out[out_idx++] = (unsigned char)(((b & 0x0F) << 4) | (cval >> 2));
                if (d >= 0) {
                    out[out_idx++] = (unsigned char)(((cval & 0x03) << 6) | d);
                }
            }
            quad_len = 0;
        }
    }

    if (out_len) {
        *out_len = out_idx;
    }
    return out;
}

static unsigned char *zlib_inflate_all(const unsigned char *data, size_t len, size_t *out_len) {
    z_stream stream;
    memset(&stream, 0, sizeof(stream));
    if (inflateInit(&stream) != Z_OK) {
        return NULL;
    }

    size_t cap = 4096;
    unsigned char *out = malloc(cap);
    if (!out) {
        inflateEnd(&stream);
        return NULL;
    }

    stream.next_in = (Bytef *)data;
    stream.avail_in = (uInt)len;

    int ret = Z_OK;
    while (ret == Z_OK) {
        if (stream.total_out >= cap) {
            size_t next_cap = cap * 2;
            unsigned char *next = realloc(out, next_cap);
            if (!next) {
                free(out);
                inflateEnd(&stream);
                return NULL;
            }
            out = next;
            cap = next_cap;
        }
        stream.next_out = out + stream.total_out;
        stream.avail_out = (uInt)(cap - stream.total_out);
        ret = inflate(&stream, Z_NO_FLUSH);
    }

    if (ret != Z_STREAM_END) {
        free(out);
        inflateEnd(&stream);
        return NULL;
    }

    if (out_len) {
        *out_len = stream.total_out;
    }
    inflateEnd(&stream);
    return out;
}

static bool load_level_from_text(char *text) {
    bool clear_requested = true;

    char *save = NULL;
    char *line = strtok_r(text, "\n", &save);
    if (!line) {
        return false;
    }

    if (strcmp(line, "clear") == 0) {
        clear_requested = true;
        line = strtok_r(NULL, "\n", &save);
    } else if (strcmp(line, "patch") == 0) {
        clear_requested = false;
        line = strtok_r(NULL, "\n", &save);
    }

    if (!line) {
        return false;
    }

    if (clear_requested) {
        clear_world();
        level_entity_count = 0;
        level_player_x = 5.0f;
        level_player_y = 30.0f;
        level_width = WORLD_W;
    } else {
        level_entity_count = 0;
    }

    int width = atoi(line);
    if (width < WORLD_W_MIN) {
        width = WORLD_W_MIN;
    } else if (width > WORLD_W) {
        width = WORLD_W;
    }
    level_width = width;

    line = strtok_r(NULL, "\n", &save);
    if (!line) {
        return false;
    }
    int entity_total = atoi(line);
    for (int i = 0; i < entity_total; ++i) {
        line = strtok_r(NULL, "\n", &save);
        if (!line) {
            return false;
        }
        int id = 0;
        int ex = 0;
        int ey = 0;
        if (sscanf(line, "%d,%d,%d", &id, &ex, &ey) == 3) {
            if (id == 0) {
                level_player_x = (float)ex;
                level_player_y = (float)ey;
            } else if (level_entity_count < MAX_ENTITIES) {
                level_entities[level_entity_count++] = (Entity){
                    .x = (float)ex,
                    .y = (float)ey,
                    .vx = 0.0f,
                    .vy = 0.0f,
                    .on_ground = false,
                    .health = 0,
                    .dir = (level_entity_count % 2 == 0) ? 1 : -1,
                    .hurt_timer = 0.0f,
                    .type = id,
                    .anchor_y = (float)ey,
                    .ai_timer = 0.0f,
                };
            }
        }
    }

    line = strtok_r(NULL, "\n", &save);
    if (!line) {
        return false;
    }
    int block_total = atoi(line);
    for (int i = 0; i < block_total; ++i) {
        line = strtok_r(NULL, "\n", &save);
        if (!line) {
            return false;
        }
        uint8_t id = 0;
        int64_t x1 = 0;
        int64_t y1 = 0;
        int64_t x2 = 0;
        int64_t y2 = 0;
        int fields = sscanf(line, "%hhd,%ld,%ld,%ld,%ld", (uint8_t *)&id, (int64_t *)&x1, (int64_t *)&y1, (int64_t *)&x2, (int64_t *)&y2);
        if (fields == 3) {
            if (x1 < level_width && y1 < WORLD_H) {
                world[(uint64_t)y1][(uint64_t)x1] = (uint8_t)id;
            }
        } else if (fields == 5) {
            if (x2 < x1) {
                int tmp = x1;
                x1 = x2;
                x2 = tmp;
            }
            if (y2 < y1) {
                int tmp = y1;
                y1 = y2;
                y2 = tmp;
            }
            for (int y = y1; y <= y2; ++y) {
                if (y < 0 || y >= WORLD_H) {
                    continue;
                }
                for (int x = x1; x <= x2; ++x) {
                    if (x < 0 || x >= level_width) {
                        continue;
                    }
                    world[(uint64_t)y][(uint64_t)x] = (uint8_t)id;
                }
            }
        }
    }

    return true;
}

static bool load_level_from_base64_file(const char *path) {
    FILE *fp = fopen(path, "rb");
    if (!fp) {
        return false;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        return false;
    }
    long size = ftell(fp);
    if (size < 0) {
        fclose(fp);
        return false;
    }
    rewind(fp);

    char *data = malloc((size_t)size + 1);
    if (!data) {
        fclose(fp);
        return false;
    }
    size_t read = fread(data, 1, (size_t)size, fp);
    fclose(fp);
    data[read] = '\0';

    size_t decoded_len = 0;
    unsigned char *decoded = base64_decode(data, &decoded_len);
    free(data);
    if (!decoded) {
        return false;
    }

    size_t inflated_len = 0;
    unsigned char *inflated = zlib_inflate_all(decoded, decoded_len, &inflated_len);
    free(decoded);
    if (!inflated) {
        return false;
    }

    char *text = malloc(inflated_len + 1);
    if (!text) {
        free(inflated);
        return false;
    }
    memcpy(text, inflated, inflated_len);
    text[inflated_len] = '\0';
    free(inflated);

    bool ok = load_level_from_text(text);
    free(text);
    return ok;
}

static void show_level_export(void) {
    const Entity *entities = level_entities;
    int entity_count = level_entity_count;
    erase();
    scrollok(stdscr, TRUE);

    StringBuilder sb = {0};
    if (!sb_appendf(&sb, "clear\n")) {
        return;
    }
    if (!sb_appendf(&sb, "%d\n", level_width)) {
        return;
    }
    if (!sb_appendf(&sb, "%d\n", entity_count)) {
        return;
    }
    for (int i = 0; i < entity_count; ++i) {
        sb_appendf(&sb, "%d,%d,%d\n", entities[i].type,
                   (int)floorf(entities[i].x),
                   (int)floorf(entities[i].y));
    }

    typedef struct {
        uint8_t id;
        int x1;
        int y1;
        int x2;
        int y2;
        bool rect;
    } BlockRect;

    bool visited[WORLD_H][WORLD_W];
    for (int y = 0; y < WORLD_H; ++y) {
        for (int x = 0; x < level_width; ++x) {
            visited[y][x] = false;
        }
    }

    int blocks_cap = level_width * WORLD_H;
    BlockRect *blocks = malloc(sizeof(BlockRect) * (size_t)blocks_cap);
    int block_count = 0;

    for (int y = 0; y < WORLD_H; ++y) {
        for (int x = 0; x < level_width; ++x) {
            if (visited[y][x]) {
                continue;
            }
            uint8_t tile = world[y][x];
            if (tile == TILE_AIR) {
                visited[y][x] = true;
                continue;
            }

            int max_w = 0;
            while (x + max_w < level_width) {
                if (visited[y][x + max_w] || world[y][x + max_w] != tile) {
                    break;
                }
                max_w++;
            }

            int max_h = 1;
            bool can_expand = true;
            while (y + max_h < WORLD_H && can_expand) {
                for (int xx = 0; xx < max_w; ++xx) {
                    if (visited[y + max_h][x + xx] ||
                        world[y + max_h][x + xx] != tile) {
                        can_expand = false;
                        break;
                    }
                }
                if (can_expand) {
                    max_h++;
                }
            }

            for (int yy = 0; yy < max_h; ++yy) {
                for (int xx = 0; xx < max_w; ++xx) {
                    visited[y + yy][x + xx] = true;
                }
            }

            if (block_count < blocks_cap) {
                blocks[block_count++] = (BlockRect){
                    .id = tile,
                    .x1 = x,
                    .y1 = y,
                    .x2 = x + max_w - 1,
                    .y2 = y + max_h - 1,
                    .rect = (max_w > 1 || max_h > 1),
                };
            }
        }
    }

    sb_appendf(&sb, "%d\n", block_count);
    for (int i = 0; i < block_count; ++i) {
        BlockRect *b = &blocks[i];
        if (b->rect) {
            sb_appendf(&sb, "%d,%d,%d,%d,%d\n", b->id, b->x1, b->y1, b->x2, b->y2);
        } else {
            sb_appendf(&sb, "%d,%d,%d\n", b->id, b->x1, b->y1);
        }
    }
    free(blocks);

    uLongf comp_size = compressBound((uLong)sb.len);
    unsigned char *comp = malloc(comp_size);
    if (!comp) {
        free(sb.data);
        return;
    }
    if (compress2(comp, &comp_size, (const Bytef *)sb.data, (uLong)sb.len, Z_BEST_COMPRESSION) != Z_OK) {
        free(comp);
        free(sb.data);
        return;
    }

    size_t b64_len = 0;
    char *b64 = base64_encode(comp, comp_size, &b64_len);
    free(comp);
    free(sb.data);
    if (!b64) {
        return;
    }

    printw("%s\n", b64);
    free(b64);

    printw("\nPress any key to return...");
    refresh();

    nodelay(stdscr, FALSE);
    getch();
    nodelay(stdscr, TRUE);
    scrollok(stdscr, FALSE);
}

static void show_level_import(void) {
    erase();
    scrollok(stdscr, TRUE);
    mvprintw(1, 2, "Paste base64 level data. End with an empty line.");
    refresh();

    StringBuilder sb = {0};
    char line[512];

    nodelay(stdscr, FALSE);
    echo();
    curs_set(1);
    int row = 3;
    while (1) {
        move(row, 2);
        clrtoeol();
        if (getnstr(line, (int)sizeof(line) - 1) == ERR) {
            break;
        }
        if (line[0] == '\0') {
            break;
        }
        sb_append(&sb, line);
        row++;
    }
    noecho();
    curs_set(0);
    nodelay(stdscr, TRUE);

    size_t decoded_len = 0;
    unsigned char *decoded = base64_decode(sb.data ? sb.data : "", &decoded_len);
    free(sb.data);
    if (!decoded) {
        return;
    }

    size_t inflated_len = 0;
    unsigned char *inflated = zlib_inflate_all(decoded, decoded_len, &inflated_len);
    free(decoded);
    if (!inflated) {
        return;
    }

    char *text = malloc(inflated_len + 1);
    if (!text) {
        free(inflated);
        return;
    }
    memcpy(text, inflated, inflated_len);
    text[inflated_len] = '\0';
    free(inflated);

    erase();
    move(0, 0);
    refresh();
    load_level_from_text(text);
    free(text);
}

static bool parse_key_line(const char *line, const char *name, wint_t *out_key) {
    size_t name_len = strlen(name);
    const char *p = line;
    while (isspace((unsigned char)*p)) {
        ++p;
    }
    if (strncmp(p, name, name_len) != 0) {
        return false;
    }
    p += name_len;
    while (isspace((unsigned char)*p)) {
        ++p;
    }
    if (*p != '=') {
        return false;
    }
    ++p;
    while (isspace((unsigned char)*p)) {
        ++p;
    }
    if (*p == '\0' || *p == '\n' || *p == '\r') {
        return false;
    }
    if (strncmp(p, "KEY_LEFT", 8) == 0) {
        *out_key = KEY_LEFT;
        return true;
    }
    if (strncmp(p, "KEY_RIGHT", 9) == 0) {
        *out_key = KEY_RIGHT;
        return true;
    }
    if (strncmp(p, "KEY_UP", 6) == 0) {
        *out_key = KEY_UP;
        return true;
    }
    if (strncmp(p, "KEY_DOWN", 8) == 0) {
        *out_key = KEY_DOWN;
        return true;
    }

    if ((p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) ||
        (p[0] == 'U' && p[1] == '+')) {
        char *end = NULL;
        const char *hex_start = p + 2;
        unsigned long value = strtoul(hex_start, &end, 16);
        if (end == hex_start) {
            return false;
        }
        *out_key = (wint_t)value;
        return true;
    }

    mbstate_t st;
    memset(&st, 0, sizeof(st));
    wchar_t wc = 0;
    size_t len = mbrtowc(&wc, p, MB_CUR_MAX, &st);
    if (len == (size_t)-1 || len == (size_t)-2 || len == 0) {
        return false;
    }
    *out_key = towlower((wint_t)wc);
    return true;
}

static bool load_key_bindings(const char *path, KeyBindings *keys) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return false;
    }

    char line[128];
    while (fgets(line, sizeof(line), fp)) {
        const char *p = line;
        while (isspace((unsigned char)*p)) {
            ++p;
        }
        if (*p == '#' || *p == '\0' || *p == '\n') {
            continue;
        }
        (void)parse_key_line(p, "left", &keys->left);
        (void)parse_key_line(p, "right", &keys->right);
        (void)parse_key_line(p, "up", &keys->up);
        (void)parse_key_line(p, "down", &keys->down);
        (void)parse_key_line(p, "quit", &keys->quit);
        (void)parse_key_line(p, "clear", &keys->clear_block);
        (void)parse_key_line(p, "edit", &keys->edit_block);
        (void)parse_key_line(p, "delete", &keys->delete_entity);
        (void)parse_key_line(p, "modify", &keys->modify_entity);
        (void)parse_key_line(p, "save", &keys->save_level);
        (void)parse_key_line(p, "width", &keys->set_width);
    }

    fclose(fp);
    return true;
}

static bool is_solid_tile(int tx, int ty) {
    if (tx < 0 || tx >= level_width || ty < 0 || ty >= WORLD_H) {
        return true;
    }
    uint8_t tile = world[ty][tx];
    return tile == TILE_GROUND || tile == TILE_PLATFORM ||
           tile == TILE_STONE || tile == TILE_BRICK ||
           tile == TILE_QUESTION;
}

static bool is_goal_tile(int tx, int ty) {
    if (tx < 0 || tx >= level_width || ty < 0 || ty >= WORLD_H) {
        return false;
    }
    uint8_t tile = world[ty][tx];
    return tile == TILE_FLAGPOLE || tile == TILE_FLAG;
}

static void move_entity_no_gravity(Entity *ent, float dt) {
    float new_x = ent->x + ent->vx * dt;
    float new_y = ent->y + ent->vy * dt;

    if (ent->vx > 0.0f) {
        int tx = (int)floorf(new_x + 0.99f);
        int ty0 = (int)floorf(ent->y);
        int ty1 = (int)floorf(ent->y + 0.99f);
        if (is_solid_tile(tx, ty0) || is_solid_tile(tx, ty1)) {
            new_x = (float)tx - 1.0f;
            ent->vx = 0.0f;
        }
    } else if (ent->vx < 0.0f) {
        int tx = (int)floorf(new_x);
        int ty0 = (int)floorf(ent->y);
        int ty1 = (int)floorf(ent->y + 0.99f);
        if (is_solid_tile(tx, ty0) || is_solid_tile(tx, ty1)) {
            new_x = (float)tx + 1.0f;
            ent->vx = 0.0f;
        }
    }

    ent->on_ground = false;
    if (ent->vy > 0.0f) {
        int ty = (int)floorf(new_y + 0.99f);
        int tx0 = (int)floorf(new_x);
        int tx1 = (int)floorf(new_x + 0.99f);
        if (is_solid_tile(tx0, ty) || is_solid_tile(tx1, ty)) {
            new_y = (float)ty - 1.0f;
            ent->vy = 0.0f;
        }
    } else if (ent->vy < 0.0f) {
        int ty = (int)floorf(new_y);
        int tx0 = (int)floorf(new_x);
        int tx1 = (int)floorf(new_x + 0.99f);
        if (is_solid_tile(tx0, ty) || is_solid_tile(tx1, ty)) {
            new_y = (float)ty + 1.0f;
            ent->vy = 0.0f;
        }
    }

    ent->x = fmaxf(0.0f, fminf(new_x, (float)level_width - 1.0f));
    ent->y = fmaxf(0.0f, fminf(new_y, (float)WORLD_H - 1.0f));
}

static void apply_block_interaction(int tx, int ty, bool allow_spawn) {
    if (tx < 0 || tx >= level_width || ty < 0 || ty >= WORLD_H) {
        return;
    }
    uint8_t tile = world[ty][tx];
    if (tile == TILE_BRICK) {
        world[ty][tx] = TILE_AIR;
    } else if (tile == TILE_QUESTION) {
        world[ty][tx] = TILE_PLATFORM;
        if (allow_spawn && ty - 1 >= 0 && !spawn_mushroom_request) {
            spawn_mushroom_request = true;
            spawn_mushroom_x = tx;
            spawn_mushroom_y = ty - 1;
        }
    }
}

static void move_entity(Entity *ent, float dt, bool allow_interact) {
    const float gravity = 30.0f;
    const float max_fall = 50.0f;
    float new_x = ent->x + ent->vx * dt;
    float new_y = ent->y + ent->vy * dt;

    if (ent->vy < max_fall) {
        ent->vy += gravity * dt;
    }

    if (ent->vx > 0.0f) {
        int tx = (int)floorf(new_x + 0.99f);
        int ty0 = (int)floorf(ent->y);
        int ty1 = (int)floorf(ent->y + 0.99f);
        if (is_solid_tile(tx, ty0) || is_solid_tile(tx, ty1)) {
            new_x = (float)tx - 1.0f;
            ent->vx = 0.0f;
        }
    } else if (ent->vx < 0.0f) {
        int tx = (int)floorf(new_x);
        int ty0 = (int)floorf(ent->y);
        int ty1 = (int)floorf(ent->y + 0.99f);
        if (is_solid_tile(tx, ty0) || is_solid_tile(tx, ty1)) {
            new_x = (float)tx + 1.0f;
            ent->vx = 0.0f;
        }
    }

    ent->on_ground = false;
    if (ent->vy > 0.0f) {
        int ty = (int)floorf(new_y + 0.99f);
        int tx0 = (int)floorf(new_x);
        int tx1 = (int)floorf(new_x + 0.99f);
        if (is_solid_tile(tx0, ty) || is_solid_tile(tx1, ty)) {
            new_y = (float)ty - 1.0f;
            ent->vy = 0.0f;
            ent->on_ground = true;
        }
    } else if (ent->vy < 0.0f) {
        int ty = (int)floorf(new_y);
        int tx0 = (int)floorf(new_x);
        int tx1 = (int)floorf(new_x + 0.99f);
        if (is_solid_tile(tx0, ty) || is_solid_tile(tx1, ty)) {
            if (allow_interact) {
                if (is_solid_tile(tx0, ty)) {
                    apply_block_interaction(tx0, ty, true);
                }
                if (is_solid_tile(tx1, ty)) {
                    apply_block_interaction(tx1, ty, true);
                }
            }
            new_y = (float)ty + 1.0f;
            ent->vy = 0.0f;
        }
    }

    ent->x = fmaxf(0.0f, fminf(new_x, (float)level_width - 1.0f));
    ent->y = fmaxf(0.0f, fminf(new_y, (float)WORLD_H - 1.0f));
}

static void update_entity(Entity *entity, const Entity *player, float dt) {
    const float walker_speed = 6.0f;
    switch (entity->type) {
    case ENTITY_SNAIL: {
        const float speed = 3.0f;
        float front_x = entity->x + (entity->dir > 0 ? 0.99f : 0.0f);
        int probe_x = (int)floorf(front_x);
        int probe_y = (int)floorf(entity->anchor_y + 1.0f);
        if (!is_solid_tile(probe_x, probe_y)) {
            entity->dir *= -1;
        }
        entity->vx = entity->dir * speed;
        entity->vy = 0.0f;
        move_entity_no_gravity(entity, dt);
        if (entity->vx == 0.0f) {
            entity->dir *= -1;
        }
        entity->y = entity->anchor_y;
        break;
    }
    case ENTITY_BAT: {
        const float speed = 8.0f;
        const float vertical = 4.0f;
        if (entity->ai_timer <= 0.0f) {
            entity->ai_timer = rand_range(0.4f, 1.4f);
            entity->vx = rand_range(-speed, speed);
            entity->vy = rand_range(-vertical, vertical);
            if (fabsf(entity->vx) < 0.5f && fabsf(entity->vy) < 0.5f) {
                entity->vx = speed * (entity->dir >= 0 ? 1.0f : -1.0f);
            }
        }
        float prev_vx = entity->vx;
        float prev_vy = entity->vy;
        move_entity_no_gravity(entity, dt);
        if (entity->vx == 0.0f) {
            entity->vx = -prev_vx;
        }
        if (entity->vy == 0.0f) {
            entity->vy = -prev_vy;
        }
        entity->ai_timer -= dt;
        break;
    }
    case ENTITY_MUSHROOM: {
        const float speed = 5.0f;
        if (player) {
            entity->dir = (player->x < entity->x) ? -1 : 1;
        }
        entity->vx = entity->dir * speed;
        move_entity(entity, dt, false);
        break;
    }
    case ENTITY_ALIEN:
    case ENTITY_SLIME:
    case ENTITY_ROBOT:
    case ENTITY_MONSTER:
    default:
        entity->vx = entity->dir * walker_speed;
        move_entity(entity, dt, false);
        if (entity->vx == 0.0f) {
            entity->dir *= -1;
        }
        break;
    }
}

static void draw_world(const Entity *player, const Entity *entities, int entity_count) {
    int screen_h = 0;
    int screen_w = 0;
    getmaxyx(stdscr, screen_h, screen_w);

    int view_h = VIEW_H;
    int view_w = VIEW_W;
    if (view_h > screen_h - 3) {
        view_h = screen_h - 3;
    }
    if (view_w > (screen_w - 2) / tile_cell_width) {
        view_w = (screen_w - 2) / tile_cell_width;
    }
    if (view_w > level_width) {
        view_w = level_width;
    }
    if (view_w > level_width) {
        view_w = level_width;
    }

    int cam_x = (int)floorf(player->x - view_w / 2.0f);
    int cam_y = (int)floorf(player->y - view_h / 2.0f);

    if (cam_x < 0) {
        cam_x = 0;
    }
    if (cam_y < 0) {
        cam_y = 0;
    }
    if (cam_x > level_width - view_w) {
        cam_x = level_width - view_w;
    }
    if (cam_x < 0) {
        cam_x = 0;
    }
    if (cam_y > WORLD_H - view_h) {
        cam_y = WORLD_H - view_h;
    }

    int origin_x = 1;
    int origin_y = 2;

    erase();
    if (view_h > 0 && view_w > 0) {
        mvaddch(origin_y - 1, origin_x - 1, ACS_ULCORNER);
        mvaddch(origin_y - 1, origin_x + view_w * tile_cell_width, ACS_URCORNER);
        mvaddch(origin_y + view_h, origin_x - 1, ACS_LLCORNER);
        mvaddch(origin_y + view_h, origin_x + view_w * tile_cell_width, ACS_LRCORNER);
        for (int x = 0; x < view_w * tile_cell_width; ++x) {
            mvaddch(origin_y - 1, origin_x + x, ACS_HLINE);
            mvaddch(origin_y + view_h, origin_x + x, ACS_HLINE);
        }
        for (int y = 0; y < view_h; ++y) {
            mvaddch(origin_y + y, origin_x - 1, ACS_VLINE);
            mvaddch(origin_y + y, origin_x + view_w * tile_cell_width, ACS_VLINE);
        }
    }

    if (origin_x + view_w * tile_cell_width + 1 < screen_w &&
        origin_y + view_h < screen_h) {
        attron(A_DIM);
        for (int y = 0; y < view_h + 1; ++y) {
            mvaddch(origin_y + y, origin_x + view_w * tile_cell_width + 1, ' ');
        }
        for (int x = 0; x < view_w * tile_cell_width + 1; ++x) {
            if (origin_y + view_h + 1 >= screen_h) {
                break;
            }
            mvaddch(origin_y + view_h + 1, origin_x + x, ' ');
        }
        attroff(A_DIM);
    }

    for (int y = 0; y < view_h; ++y) {
        int wy = cam_y + y;
        for (int x = 0; x < view_w; ++x) {
            int wx = cam_x + x;
            uint8_t tile = world[wy][wx];
            draw_tile_at(origin_y + y, origin_x + x * tile_cell_width, tile);
        }
    }

    for (int i = 0; i < entity_count; ++i) {
        int ex = (int)floorf(entities[i].x) - cam_x;
        int ey = (int)floorf(entities[i].y) - cam_y;
        if (ex >= 0 && ex < view_w && ey >= 0 && ey < view_h) {
            mvaddwstr(origin_y + ey, origin_x + ex * tile_cell_width, entity_glyph(entities[i].type));
        }
    }

    int px = (int)floorf(player->x) - cam_x;
    int py = (int)floorf(player->y) - cam_y;
    if (px >= 0 && px < view_w && py >= 0 && py < view_h) {
        mvaddwstr(origin_y + py, origin_x + px * tile_cell_width, player_glyph_for_health(player->health));
    }
}

static int find_entity_at(int x, int y) {
    for (int i = 0; i < level_entity_count; ++i) {
        int ex = (int)floorf(level_entities[i].x);
        int ey = (int)floorf(level_entities[i].y);
        if (ex == x && ey == y) {
            return i;
        }
    }
    return -1;
}

static void draw_hud(const Entity *player) {
    move(0, 0);
    clrtoeol();
    for (int i = 0; i < player->health; ++i) {
        mvaddwstr(0, i * tile_cell_width, heart_glyph);
    }
}

static void draw_editor(int cursor_x, int cursor_y, bool dirty) {
    int screen_h = 0;
    int screen_w = 0;
    getmaxyx(stdscr, screen_h, screen_w);

    int view_h = VIEW_H;
    int view_w = VIEW_W;
    int help_lines = 5;
    int dev_lines = 0;
    if (developer_mode) {
        int info_h = 6;
        int block_h = TILE_COUNT + 3;
        int entity_h = 8;
        dev_lines = info_h;
        if (block_h > dev_lines) {
            dev_lines = block_h;
        }
        if (entity_h > dev_lines) {
            dev_lines = entity_h;
        }
    }
    if (view_h > screen_h - 3 - help_lines - dev_lines) {
        view_h = screen_h - 3 - help_lines - dev_lines;
    }
    if (view_w > (screen_w - 2) / tile_cell_width) {
        view_w = (screen_w - 2) / tile_cell_width;
    }

    int cam_x = cursor_x - view_w / 2;
    int cam_y = cursor_y - view_h / 2;
    if (cam_x < 0) {
        cam_x = 0;
    }
    if (cam_y < 0) {
        cam_y = 0;
    }
    if (cam_x > level_width - view_w) {
        cam_x = level_width - view_w;
    }
    if (cam_x < 0) {
        cam_x = 0;
    }
    if (cam_y > WORLD_H - view_h) {
        cam_y = WORLD_H - view_h;
    }

    int origin_x = 1;
    int origin_y = 2;

    erase();
    int entity_idx = find_entity_at(cursor_x, cursor_y);
    uint8_t tile = world[cursor_y][cursor_x];
    const char *tile_label = tile_name(tile);
    const char *status = dirty ? "(unsaved)" : "(saved)";
    if (entity_idx >= 0) {
        mvprintw(0, 0, "X:%d Y:%d Tile:%d(%s) ",
                 cursor_x, cursor_y, tile, tile_label);
        mvaddwstr(0, getcurx(stdscr), tile_glyph(tile));
        mvprintw(0, getcurx(stdscr), " Ent:%d(%s) ",
                 level_entities[entity_idx].type,
                 entity_name(level_entities[entity_idx].type));
        mvaddwstr(0, getcurx(stdscr), entity_glyph(level_entities[entity_idx].type));
        mvprintw(0, getcurx(stdscr), " W:%d %s", level_width, status);
    } else {
        mvprintw(0, 0, "X:%d Y:%d Tile:%d(%s) ",
                 cursor_x, cursor_y, tile, tile_label);
        mvaddwstr(0, getcurx(stdscr), tile_glyph(tile));
        mvprintw(0, getcurx(stdscr), " W:%d %s", level_width, status);
    }
    clrtoeol();

    if (view_h > 0 && view_w > 0) {
        mvaddch(origin_y - 1, origin_x - 1, ACS_ULCORNER);
        mvaddch(origin_y - 1, origin_x + view_w * tile_cell_width, ACS_URCORNER);
        mvaddch(origin_y + view_h, origin_x - 1, ACS_LLCORNER);
        mvaddch(origin_y + view_h, origin_x + view_w * tile_cell_width, ACS_LRCORNER);
        for (int x = 0; x < view_w * tile_cell_width; ++x) {
            mvaddch(origin_y - 1, origin_x + x, ACS_HLINE);
            mvaddch(origin_y + view_h, origin_x + x, ACS_HLINE);
        }
        for (int y = 0; y < view_h; ++y) {
            mvaddch(origin_y + y, origin_x - 1, ACS_VLINE);
            mvaddch(origin_y + y, origin_x + view_w * tile_cell_width, ACS_VLINE);
        }
    }

    for (int y = 0; y < view_h; ++y) {
        int wy = cam_y + y;
        for (int x = 0; x < view_w; ++x) {
            int wx = cam_x + x;
            uint8_t t = world[wy][wx];
            draw_tile_at(origin_y + y, origin_x + x * tile_cell_width, t);
        }
    }

    for (int i = 0; i < level_entity_count; ++i) {
        int ex = (int)floorf(level_entities[i].x) - cam_x;
        int ey = (int)floorf(level_entities[i].y) - cam_y;
        if (ex >= 0 && ex < view_w && ey >= 0 && ey < view_h) {
            mvaddwstr(origin_y + ey, origin_x + ex * tile_cell_width,
                      entity_glyph(level_entities[i].type));
        }
    }

    int cx = cursor_x - cam_x;
    int cy = cursor_y - cam_y;
    if (cx >= 0 && cx < view_w && cy >= 0 && cy < view_h) {
        attron(COLOR_PAIR(1) | A_BOLD);
        mvaddwstr(origin_y + cy, origin_x + cx * tile_cell_width, cursor_glyph);
        attroff(COLOR_PAIR(1) | A_BOLD);
    }

    int help_y = origin_y + view_h + 1;
    if (help_y + 2 < screen_h) {
        int gap = 2;
        int usable_w = screen_w - 4;
        int box_w = (usable_w - gap * 2) / 3;
        int box_h = 5;
        if (box_w > 10) {
            int left_x = 1;
            int mid_x = left_x + box_w + gap;
            int right_x = mid_x + box_w + gap;
            draw_box(left_x, help_y, box_w + 2, box_h);
            draw_box(mid_x, help_y, box_w + 2, box_h);
            draw_box(right_x, help_y, box_w + 2, box_h);

            if (has_colors()) {
                attron(COLOR_PAIR(1) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            mvprintw(help_y + 1, left_x + 2, "Blocks");
            if (has_colors()) {
                attroff(COLOR_PAIR(1) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            move(help_y + 2, left_x + 2);
            if (has_colors()) {
                attron(COLOR_PAIR(6) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            addch('C');
            if (has_colors()) {
                attroff(COLOR_PAIR(6) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            addstr(" clear  ");
            if (has_colors()) {
                attron(COLOR_PAIR(6) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            addch('E');
            if (has_colors()) {
                attroff(COLOR_PAIR(6) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            addstr(" edit");
            if (has_colors()) {
                attron(COLOR_PAIR(1) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            mvprintw(help_y + 1, mid_x + 2, "Entities");
            if (has_colors()) {
                attroff(COLOR_PAIR(1) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            move(help_y + 2, mid_x + 2);
            if (has_colors()) {
                attron(COLOR_PAIR(6) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            addch('M');
            if (has_colors()) {
                attroff(COLOR_PAIR(6) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            addstr(" modify  ");
            if (has_colors()) {
                attron(COLOR_PAIR(6) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            addch('D');
            if (has_colors()) {
                attroff(COLOR_PAIR(6) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            addstr(" delete");
            if (has_colors()) {
                attron(COLOR_PAIR(1) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            mvprintw(help_y + 1, right_x + 2, "Other");
            if (has_colors()) {
                attroff(COLOR_PAIR(1) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            move(help_y + 2, right_x + 2);
            if (has_colors()) {
                attron(COLOR_PAIR(6) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            addch('W');
            if (has_colors()) {
                attroff(COLOR_PAIR(6) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            addstr(" width");
            move(help_y + 3, right_x + 2);
            if (has_colors()) {
                attron(COLOR_PAIR(6) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            addch('S');
            if (has_colors()) {
                attroff(COLOR_PAIR(6) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            addstr(" save  ");
            if (has_colors()) {
                attron(COLOR_PAIR(6) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            addch('Q');
            if (has_colors()) {
                attroff(COLOR_PAIR(6) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            addstr(" quit");
        }
    }

    if (developer_mode) {
        size_t block_counts[TILE_COUNT];
        size_t unknown_blocks = 0;
        size_t total_blocks = 0;
        for (int i = 0; i < TILE_COUNT; ++i) {
            block_counts[i] = 0;
        }
        for (int y = 0; y < WORLD_H; ++y) {
            for (int x = 0; x < level_width; ++x) {
                uint8_t t = world[y][x];
                if (t != TILE_AIR) {
                    total_blocks++;
                }
                if (t < TILE_COUNT) {
                    block_counts[t]++;
                } else {
                    unknown_blocks++;
                }
            }
        }

        int entity_counts[ENTITY_MAX_ID + 1];
        int entity_total = 0;
        for (int i = 0; i <= ENTITY_MAX_ID; ++i) {
            entity_counts[i] = 0;
        }
        for (int i = 0; i < level_entity_count; ++i) {
            int type = level_entities[i].type;
            if (type >= 0 && type <= ENTITY_MAX_ID) {
                entity_counts[type]++;
            }
            entity_total++;
        }

        int box_y = help_y + 5;
        int gap = 2;
        int usable_w = screen_w - 4;
        int box_w = (usable_w - gap * 2) / 3;
        int info_h = 6;
        int block_h = TILE_COUNT + 3;
        int entity_h = 8;
        int max_h = info_h;
        if (block_h > max_h) {
            max_h = block_h;
        }
        if (entity_h > max_h) {
            max_h = entity_h;
        }

        if (box_w > 10 && box_y + max_h + 1 < screen_h) {
            int left_x = 1;
            int mid_x = left_x + box_w + gap;
            int right_x = mid_x + box_w + gap;

            draw_box(left_x, box_y, box_w + 2, max_h + 2);
            draw_box(mid_x, box_y, box_w + 2, max_h + 2);
            draw_box(right_x, box_y, box_w + 2, max_h + 2);

            int row = box_y + 1;
            if (has_colors()) {
                attron(COLOR_PAIR(1) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            mvprintw(row++, left_x + 2, "Dev Info");
            if (has_colors()) {
                attroff(COLOR_PAIR(1) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            mvprintw(row++, left_x + 2, "world addr=%p", (void *)&world);
            mvprintw(row++, left_x + 2, "world=%p", (void *)world);
            mvprintw(row++, left_x + 2, "world size=%zu", world_size);
            mvprintw(row++, left_x + 2, "blocks=%zu", total_blocks);
            mvprintw(row++, left_x + 2, "entities=%d", entity_total);
            mvprintw(row++, left_x + 2, "width=%d", level_width);
            mvprintw(row++, left_x + 2, "player=(%d,%d)", (int)level_player_x, (int)level_player_y);

            row = box_y + 1;
            if (has_colors()) {
                attron(COLOR_PAIR(1) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            mvprintw(row++, mid_x + 2, "Block Counts");
            if (has_colors()) {
                attroff(COLOR_PAIR(1) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            for (int i = 0; i < TILE_COUNT && row < box_y + max_h + 1; ++i) {
                mvprintw(row++, mid_x + 2, "%d %s: %zu", i, tile_name((uint8_t)i), block_counts[i]);
            }
            if (row < box_y + max_h + 1) {
                mvprintw(row++, mid_x + 2, "unknown: %zu", unknown_blocks);
            }

            row = box_y + 1;
            if (has_colors()) {
                attron(COLOR_PAIR(1) | A_BOLD);
            } else {
                attron(A_BOLD);
            }
            mvprintw(row++, right_x + 2, "Entity Counts");
            if (has_colors()) {
                attroff(COLOR_PAIR(1) | A_BOLD);
            } else {
                attroff(A_BOLD);
            }
            for (int type = 1; type <= ENTITY_MAX_ID && row < box_y + max_h + 1; ++type) {
                mvprintw(row++, right_x + 2, "%d %s: %d", type, entity_name(type), entity_counts[type]);
            }
        }
    }

    refresh();
}

static int run_choice_menu_with_glyphs(const KeyBindings *keys, const char *title,
                                       const char **items, const wchar_t **glyphs,
                                       int count) {
    int selected = 0;
    while (1) {
        erase();
        mvprintw(2, 2, "%s", title);
        for (int i = 0; i < count; ++i) {
            if (i == selected) {
                attron(A_REVERSE);
            }
            mvprintw(4 + i, 4, "%s ", items[i]);
            if (glyphs && glyphs[i]) {
                mvaddwstr(4 + i, getcurx(stdscr), glyphs[i]);
            }
            if (i == selected) {
                attroff(A_REVERSE);
            }
        }
        refresh();

        wint_t wch = 0;
        int rc = get_wch(&wch);
        if (rc == ERR) {
            continue;
        }
        wint_t key = wch;
        if (rc != KEY_CODE_YES) {
            key = towlower(wch);
        }
        if (key == KEY_UP || key == keys->up) {
            selected = (selected - 1 + count) % count;
        } else if (key == KEY_DOWN || key == keys->down) {
            selected = (selected + 1) % count;
        } else if (key == '\n' || key == KEY_ENTER || key == '\r') {
            return selected;
        } else if (key == keys->quit) {
            return -1;
        }
    }
}

static void run_editor(const KeyBindings *keys) {
    int cursor_x = (int)level_player_x;
    int cursor_y = (int)level_player_y;
    bool dirty = false;
    uint8_t backup_world[WORLD_H][WORLD_W];
    Entity backup_entities[MAX_ENTITIES];
    int backup_entity_count = level_entity_count;

    memcpy(backup_world, world, world_size);
    if (backup_entity_count > 0) {
        memcpy(backup_entities, level_entities, sizeof(Entity) * (size_t)backup_entity_count);
    }

    nodelay(stdscr, FALSE);
    while (1) {
        if (cursor_x < 0) cursor_x = 0;
        if (cursor_y < 0) cursor_y = 0;
        if (cursor_x >= level_width) cursor_x = level_width - 1;
        if (cursor_y >= WORLD_H) cursor_y = WORLD_H - 1;

        draw_editor(cursor_x, cursor_y, dirty);

        wint_t wch = 0;
        int rc = get_wch(&wch);
        if (rc == ERR) {
            continue;
        }
        wint_t key = wch;
        if (rc != KEY_CODE_YES) {
            key = towlower(wch);
        }

        if (key == KEY_LEFT || key == keys->left) {
            cursor_x--;
        } else if (key == KEY_RIGHT || key == keys->right) {
            cursor_x++;
        } else if (key == KEY_UP || key == keys->up) {
            cursor_y--;
        } else if (key == KEY_DOWN || key == keys->down) {
            cursor_y++;
        } else if (key == keys->clear_block) {
            if (world[cursor_y][cursor_x] != TILE_AIR) {
                world[cursor_y][cursor_x] = TILE_AIR;
                dirty = true;
            }
        } else if (key == keys->edit_block) {
            const char *items[TILE_COUNT];
            const wchar_t *glyphs[TILE_COUNT];
            char labels[TILE_COUNT][64];
            for (int i = 0; i < TILE_COUNT; ++i) {
                snprintf(labels[i], sizeof(labels[i]), "%d - %s", i, tile_name((uint8_t)i));
                items[i] = labels[i];
                glyphs[i] = tile_glyphs[i];
            }
            int choice = run_choice_menu_with_glyphs(keys, "Select Block", items, glyphs, TILE_COUNT);
            if (choice >= 0) {
                world[cursor_y][cursor_x] = (uint8_t)choice;
                dirty = true;
            }
        } else if (key == keys->delete_entity) {
            int idx = find_entity_at(cursor_x, cursor_y);
            if (idx >= 0) {
                level_entities[idx] = level_entities[level_entity_count - 1];
                level_entity_count--;
                dirty = true;
            }
        } else if (key == keys->modify_entity) {
            int idx = find_entity_at(cursor_x, cursor_y);
            const size_t info_count = sizeof(entity_infos) / sizeof(entity_infos[0]);
            const wchar_t *glyphs[8];
            char labels[8][64];
            const char *menu_items[8];
            int ids[8];
            for (size_t i = 0; i < info_count; ++i) {
                int id = entity_infos[i].id;
                snprintf(labels[i], sizeof(labels[i]), "%d - %s", id, entity_infos[i].name);
                menu_items[i] = labels[i];
                glyphs[i] = entity_infos[i].glyph;
                ids[i] = id;
            }
            int choice = run_choice_menu_with_glyphs(keys, "Select Entity", menu_items, glyphs,
                                                     (int)info_count);
            if (choice >= 0) {
                if (idx < 0) {
                    if (level_entity_count < MAX_ENTITIES) {
                        idx = level_entity_count++;
                        level_entities[idx] = (Entity){
                            .x = (float)cursor_x,
                            .y = (float)cursor_y,
                            .vx = 0.0f,
                            .vy = 0.0f,
                            .on_ground = false,
                            .health = 0,
                            .dir = 1,
                            .hurt_timer = 0.0f,
                            .type = ids[choice],
                            .anchor_y = (float)cursor_y,
                            .ai_timer = 0.0f,
                        };
                    }
                }
                if (idx >= 0) {
                    level_entities[idx].type = ids[choice];
                    level_entities[idx].x = (float)cursor_x;
                    level_entities[idx].y = (float)cursor_y;
                    level_entities[idx].anchor_y = level_entities[idx].y;
                    level_entities[idx].ai_timer = 0.0f;
                    dirty = true;
                }
            }
        } else if (key == keys->save_level) {
            memcpy(backup_world, world, world_size);
            backup_entity_count = level_entity_count;
            if (backup_entity_count > 0) {
                memcpy(backup_entities, level_entities, sizeof(Entity) * (size_t)backup_entity_count);
            }
            dirty = false;
        } else if (key == keys->set_width) {
            char input[32];
            int new_width = level_width;
            move(0, 0);
            clrtoeol();
            mvprintw(0, 0, "New width (%d-%d): ", WORLD_W_MIN, WORLD_W);
            echo();
            curs_set(1);
            if (getnstr(input, (int)sizeof(input) - 1) != ERR) {
                int value = atoi(input);
                if (value < WORLD_W_MIN) {
                    value = WORLD_W_MIN;
                } else if (value > WORLD_W) {
                    value = WORLD_W;
                }
                new_width = value;
            }
            noecho();
            curs_set(0);
            if (new_width != level_width) {
                if (new_width < level_width) {
                    for (int y = 0; y < WORLD_H; ++y) {
                        for (int x = new_width; x < level_width; ++x) {
                            world[y][x] = TILE_AIR;
                        }
                    }
                    for (int i = 0; i < level_entity_count; ) {
                        if ((int)floorf(level_entities[i].x) >= new_width) {
                            level_entities[i] = level_entities[level_entity_count - 1];
                            level_entity_count--;
                            continue;
                        }
                        ++i;
                    }
                    if ((int)floorf(level_player_x) >= new_width) {
                        level_player_x = (float)(new_width - 1);
                    }
                    if (cursor_x >= new_width) {
                        cursor_x = new_width - 1;
                    }
                }
                level_width = new_width;
                dirty = true;
            }
        } else if (key == keys->quit) {
            if (dirty) {
                mvprintw(0, 0, "Unsaved changes. Exit without saving? (y/n)");
                clrtoeol();
                refresh();
                wint_t confirm = 0;
                int rc2 = get_wch(&confirm);
                if (rc2 != ERR) {
                    if (towlower(confirm) == L'y') {
                        memcpy(world, backup_world, world_size);
                        level_entity_count = backup_entity_count;
                        if (backup_entity_count > 0) {
                            memcpy(level_entities, backup_entities,
                                   sizeof(Entity) * (size_t)backup_entity_count);
                        }
                        break;
                    }
                }
            } else {
                break;
            }
        }
    }
    nodelay(stdscr, TRUE);
}

static int run_menu(const KeyBindings *keys) {
    const char *items[] = {"Play", "Build", "Export", "Import", "Exit"};
    const int item_count = (int)(sizeof(items) / sizeof(items[0]));
    int selected = 0;
    int code_counter = 0;

    while (1) {
        int screen_h = 0;
        int screen_w = 0;
        getmaxyx(stdscr, screen_h, screen_w);

        erase();
        box(stdscr, 0, 0);

        const char *title = "Blockman Builder";
        const char *subtitle = "Arrows/Enter to select";
        const char *hint = "Q to quit menu";
        int title_len = (int)strlen(title);
        int subtitle_len = (int)strlen(subtitle);
        int hint_len = (int)strlen(hint);
        int max_item_len = 0;
        for (int i = 0; i < item_count; ++i) {
            int len = (int)strlen(items[i]);
            if (len > max_item_len) {
                max_item_len = len;
            }
        }
        int block_w = max_item_len;
        int start_x = (screen_w - block_w) / 2;
        int title_x = (screen_w - title_len) / 2;
        int subtitle_x = (screen_w - subtitle_len) / 2;
        int hint_x = (screen_w - hint_len) / 2;
        int top_y = (screen_h - item_count) / 2 - 3;
        if (top_y < 2) {
            top_y = 2;
        }

        if (developer_mode) {
            if (has_colors()) {
                attron(COLOR_PAIR(5) | A_BOLD | A_REVERSE);
            } else {
                attron(A_BOLD | A_REVERSE);
            }
            mvprintw(top_y - 2, (screen_w - 15) / 2, "DEVELOPER MODE");
            if (has_colors()) {
                attroff(COLOR_PAIR(5) | A_BOLD | A_REVERSE);
            } else {
                attroff(A_BOLD | A_REVERSE);
            }
        }

        if (has_colors()) {
            attron(COLOR_PAIR(2) | A_BOLD);
        }
        mvprintw(top_y, title_x, "%s", title);
        if (has_colors()) {
            attroff(COLOR_PAIR(2) | A_BOLD);
        }
        mvprintw(top_y + 1, title_x, "%.*s", title_len, "------------------------");
        mvprintw(top_y + 2, subtitle_x, "%s", subtitle);
        mvprintw(top_y + 3, hint_x, "%s", hint);

        for (int i = 0; i < item_count; ++i) {
            int row = top_y + 5 + i;
            if (i == selected) {
                if (has_colors()) {
                    attron(COLOR_PAIR(3) | A_BOLD);
                } else {
                    attron(A_REVERSE);
                }
            }
            mvprintw(row, start_x, "%s", items[i]);
            if (i == selected) {
                if (has_colors()) {
                    attroff(COLOR_PAIR(3) | A_BOLD);
                } else {
                    attroff(A_REVERSE);
                }
            }
        }
        refresh();

        wint_t wch = 0;
        int rc = get_wch(&wch);
        if (rc == ERR) {
            usleep(10000);
            continue;
        }

        wint_t key = wch;
        if (rc != KEY_CODE_YES) {
            key = towlower(wch);
        }

        if (key == KEY_UP || key == keys->up) {
            if (code_counter == 0 || code_counter == 1) {
                code_counter++;
            } else {
                code_counter = 0;
            }
            selected = (selected - 1 + item_count) % item_count;
        } else if (key == KEY_DOWN || key == keys->down) {
            if (code_counter == 2 || code_counter == 3) {
                code_counter++;
            } else {
                code_counter = 0;
            }
            selected = (selected + 1) % item_count;
        } else if (key == KEY_LEFT || key == keys->left) {
            if (code_counter == 4 || code_counter == 6) {
                code_counter++;
            } else {
                code_counter = 0;
            }
        } else if (key == KEY_RIGHT || key == keys->right) {
            if (code_counter == 5 || code_counter == 7) {
                code_counter++;
            } else {
                code_counter = 0;
            }
        } else if (key == keys->quit) {
            return 4;
        } else if (key == '\n' || key == KEY_ENTER || key == '\r') {
            if (code_counter == 8) {
                developer_mode = true;
                code_counter = 0;
                continue;
            }
            code_counter = 0;
            return selected;
        } else {
            code_counter = 0;
        }
    }
}

static void show_interstitial(const char *message, int millis) {
    int screen_h = 0;
    int screen_w = 0;
    getmaxyx(stdscr, screen_h, screen_w);
    int box_w = (int)strlen(message) + 6;
    int box_h = 5;
    int start_y = (screen_h - box_h) / 2;
    int start_x = (screen_w - box_w) / 2;

    erase();
    draw_box(start_x, start_y, box_w, box_h);
    mvprintw(start_y + 2, start_x + 3, "%s", message);
    refresh();
    napms(millis);
}

static GameResult run_game(const KeyBindings *keys) {
    uint8_t world_backup[WORLD_H][WORLD_W];
    memcpy(world_backup, world, world_size);
    spawn_mushroom_request = false;

    Entity player = {
        .x = level_player_x,
        .y = level_player_y,
        .vx = 0.0f,
        .vy = 0.0f,
        .on_ground = false,
        .health = 2,
        .dir = 1,
        .hurt_timer = 0.0f,
        .type = 0,
        .anchor_y = 0.0f,
        .ai_timer = 0.0f,
    };

    Entity entities[MAX_ENTITIES];
    int entity_count = level_entity_count;
    if (entity_count > 0) {
        memcpy(entities, level_entities, sizeof(Entity) * (size_t)entity_count);
    }
    bool running = true;
    GameResult result = GAME_QUIT;
    const float accel = 40.0f;
    const float decel = 50.0f;
    const float max_speed = 18.0f;
    const float jump_speed = -14.0f;
    const float dt = 0.05f;

    while (running) {
        float input_x = 0.0f;
        bool jump = false;
        float prev_player_y = player.y;

        wint_t wch = 0;
        int rc = get_wch(&wch);
        while (rc != ERR) {
            wint_t key = wch;
            if (rc != KEY_CODE_YES) {
                key = towlower(wch);
            }
            if (key == keys->quit) {
                running = false;
                result = GAME_QUIT;
            } else if (key == keys->left) {
                input_x = -1.0f;
            } else if (key == keys->right) {
                input_x = 1.0f;
            } else if (key == keys->up || key == L' ') {
                jump = true;
            }
            rc = get_wch(&wch);
        }

        float accel_rate = player.on_ground ? accel : accel * 0.5f;
        float decel_rate = player.on_ground ? decel : decel * 0.5f;

        if (input_x != 0.0f) {
            player.vx += input_x * accel_rate * dt;
        } else {
            if (player.vx > 0.0f) {
                player.vx = fmaxf(0.0f, player.vx - decel_rate * dt);
            } else if (player.vx < 0.0f) {
                player.vx = fminf(0.0f, player.vx + decel_rate * dt);
            }
        }

        if (player.vx > max_speed) {
            player.vx = max_speed;
        } else if (player.vx < -max_speed) {
            player.vx = -max_speed;
        }
        if (jump && player.on_ground) {
            player.vy = jump_speed;
            player.on_ground = false;
        }

        move_entity(&player, dt, true);
        if (player.hurt_timer > 0.0f) {
            player.hurt_timer = fmaxf(0.0f, player.hurt_timer - dt);
        }
        int goal_x = (int)floorf(player.x);
        int goal_y = (int)floorf(player.y);
        if (is_goal_tile(goal_x, goal_y) ||
            is_goal_tile(goal_x, goal_y + 1)) {
            running = false;
            result = GAME_WIN;
        }
        if (!developer_mode &&
            (int)floorf(player.y + 0.99f) >= WORLD_H - 1) {
            player.health = -1;
        }
        if (spawn_mushroom_request) {
            spawn_mushroom(entities, &entity_count, &player,
                           spawn_mushroom_x, spawn_mushroom_y);
            spawn_mushroom_request = false;
        }

        for (int i = 0; i < entity_count; ) {
            Entity *entity = &entities[i];
            update_entity(entity, &player, dt);
            if (entity->health < 0) {
                entities[i] = entities[entity_count - 1];
                entity_count--;
                continue;
            }
            ++i;
        }

        for (int i = 0; i < entity_count; ) {
            if (entities[i].type == ENTITY_MUSHROOM &&
                entities_overlap(&player, &entities[i])) {
                if (player.health < 3) {
                    player.health += 1;
                }
                entities[i] = entities[entity_count - 1];
                entity_count--;
                continue;
            }
            ++i;
        }

        for (int i = 0; i < entity_count; ) {
            if (entities[i].type != ENTITY_MUSHROOM &&
                entities_overlap(&player, &entities[i])) {
                float prev_bottom = prev_player_y + 0.99f;
                if (prev_bottom <= entities[i].y + 0.05f && player.vy >= 0.0f) {
                entities[i] = entities[entity_count - 1];
                entity_count--;
                continue;
                }
            }
            ++i;
        }

        if (!developer_mode && player.hurt_timer <= 0.0f) {
            for (int i = 0; i < entity_count; ++i) {
                if (entities[i].type == ENTITY_MUSHROOM) {
                    continue;
                }
                if (entities_overlap(&player, &entities[i]) &&
                    entities[i].y <= player.y + 0.25f) {
                    player.health -= 1;
                    player.hurt_timer = 0.5f;
                    break;
                }
            }
        }

        draw_world(&player, entities, entity_count);
        draw_hud(&player);
        refresh();

        if (player.health < 0) {
            running = false;
            result = GAME_LOSE;
        }

        usleep((useconds_t)(dt * 1000000.0f));
    }

    memcpy(world, world_backup, world_size);

    if (result == GAME_WIN) {
        show_interstitial("YOU WIN!", 3000);
    } else if (result == GAME_LOSE) {
        show_interstitial("GAME OVER", 3000);
    }
    return result;
}

int main(int argc, char **argv) {

    uint8_t local_world[WORLD_H][WORLD_W];
    world = local_world;
    world_size = sizeof(local_world);

    setlocale(LC_ALL, "");
    srand((unsigned int)time(NULL));

    initscr();
    cbreak();
    noecho();
    keypad(stdscr, TRUE);
    nodelay(stdscr, TRUE);
    curs_set(0);
    if (has_colors()) {
        start_color();
        use_default_colors();
        init_pair(1, COLOR_RED, -1);
        init_pair(2, COLOR_CYAN, -1);
        init_pair(3, COLOR_YELLOW, -1);
        init_pair(4, COLOR_WHITE, -1);
        init_pair(5, COLOR_GREEN, -1);
        init_pair(6, COLOR_MAGENTA, -1);
    }

    const char *level_path = "level.txt";
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--level") == 0 && i + 1 < argc) {
            level_path = argv[i + 1];
            i++;
        }
    }

    if (!load_level_from_base64_file(level_path)) {
        clear_world();
        level_entity_count = 0;
    }

    KeyBindings keys;
    set_default_keys(&keys);

    const char *keys_path = "keys-us.txt";
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--keys") == 0 && i + 1 < argc) {
            keys_path = argv[i + 1];
            i++;
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            endwin();
            printf("Usage: %s [--keys <file>] [--level <file>]\n", argv[0]);
            return 0;
        }
    }

    if (!load_key_bindings(keys_path, &keys)) {
        if (strcmp(keys_path, "keys-us.txt") != 0) {
            endwin();
            fprintf(stderr, "Failed to load keys file: %s (%s)\n", keys_path, strerror(errno));
            return 1;
        }
    }

    bool running = true;
    while (running) {
        int selection = run_menu(&keys);
        switch (selection) {
        case 0:
            run_game(&keys);
            break;
        case 1:
            run_editor(&keys);
            break;
        case 2:
            show_level_export();
            break;
        case 3:
            show_level_import();
            break;
        case 4:
            running = false;
            break;
        default:
            break;
        }
    }

    endwin();
    return 0;
}
