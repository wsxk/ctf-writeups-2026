#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#define CHAL_IOC_MAGIC ('d')
#define CHAL_FLAG_LEN 64

#define CHAL_GET_SEED _IOR(CHAL_IOC_MAGIC, 0x80, uint32_t)
#define CHAL_GET_X _IOR(CHAL_IOC_MAGIC, 0x81, uint32_t)
#define CHAL_GET_Y _IOR(CHAL_IOC_MAGIC, 0x82, uint32_t)
#define CHAL_GET_Z _IOR(CHAL_IOC_MAGIC, 0x83, uint32_t)
#define CHAL_GET_STEPS _IOR(CHAL_IOC_MAGIC, 0x84, uint32_t)
#define CHAL_GET_STATE _IOR(CHAL_IOC_MAGIC, 0x85, uint32_t)
#define CHAL_GET_EXITS _IOR(CHAL_IOC_MAGIC, 0x86, uint32_t)
#define CHAL_GET_FLAG _IOR(CHAL_IOC_MAGIC, 0x87, char[CHAL_FLAG_LEN])
#define CHAL_MOVE _IOW(CHAL_IOC_MAGIC, 0x88, uint32_t)
#define CHAL_RESET _IO(CHAL_IOC_MAGIC, 0x89)

enum {
    STATE_PLAYING = 0,
    STATE_WON = 1,
    STATE_LOST = 2,
};

enum {
    DIR_NORTH = 0,
    DIR_EAST = 1,
    DIR_SOUTH = 2,
    DIR_WEST = 3,
    DIR_UP = 4,
    DIR_DOWN = 5,
};

enum {
    CELL_UNKNOWN = 0,
    CELL_SAFE = 1,
    CELL_SPIKE = 2,
};

typedef struct {
    uint8_t kind;
    uint8_t exits_known;
    uint8_t exits; // bit0=N bit1=E bit2=S bit3=W bit4=U bit5=D
} cell_t;

static size_t g_sx, g_sy, g_sz;
static cell_t *g_map;

static int cur_x, cur_y, cur_z;

static const int DX[6] = {0, 1, 0, -1, 0, 0};
static const int DY[6] = {-1, 0, 1, 0, 0, 0};
static const int DZ[6] = {0, 0, 0, 0, 1, -1};

static inline size_t idx_of(int x, int y, int z) {
    return ((size_t)z * g_sy + (size_t)y) * g_sx + (size_t)x;
}

static inline bool in_bounds(int x, int y, int z) {
    return x >= 0 && y >= 0 && z >= 0 && (size_t)x < g_sx && (size_t)y < g_sy && (size_t)z < g_sz;
}

static int get_u32(int fd, unsigned long req, uint32_t *out) {
    if (ioctl(fd, req, out) < 0) {
        return -1;
    }
    return 0;
}

static int get_state(int fd, uint32_t *state) {
    return get_u32(fd, CHAL_GET_STATE, state);
}

static int opp_dir(int d) {
    switch (d) {
    case DIR_NORTH:
        return DIR_SOUTH;
    case DIR_SOUTH:
        return DIR_NORTH;
    case DIR_EAST:
        return DIR_WEST;
    case DIR_WEST:
        return DIR_EAST;
    case DIR_UP:
        return DIR_DOWN;
    case DIR_DOWN:
        return DIR_UP;
    default:
        return DIR_NORTH;
    }
}

static int query_and_store_exits(int fd, int x, int y, int z) {
    uint32_t exits = 0;
    if (get_u32(fd, CHAL_GET_EXITS, &exits) < 0) {
        return -1;
    }

    size_t cur = idx_of(x, y, z);
    g_map[cur].kind = CELL_SAFE;
    g_map[cur].exits_known = 1;
    g_map[cur].exits = (uint8_t)(exits & 0x3F);

    for (int d = 0; d < 6; d++) {
        if (!(g_map[cur].exits & (1u << d))) {
            continue;
        }
        int nx = x + DX[d], ny = y + DY[d], nz = z + DZ[d];
        if (!in_bounds(nx, ny, nz)) {
            continue;
        }
        size_t ni = idx_of(nx, ny, nz);
        if (g_map[ni].kind == CELL_SAFE && g_map[ni].exits_known) {
            g_map[ni].exits |= (1u << opp_dir(d));
        }
    }

    return 0;
}

static bool cell_has_unknown_exit_idx(size_t i) {
    if (g_map[i].kind != CELL_SAFE || !g_map[i].exits_known) {
        return false;
    }

    int x = (int)(i % g_sx);
    int y = (int)((i / g_sx) % g_sy);
    int z = (int)(i / (g_sx * g_sy));

    for (int d = 0; d < 6; d++) {
        if (!(g_map[i].exits & (1u << d))) {
            continue;
        }
        int nx = x + DX[d], ny = y + DY[d], nz = z + DZ[d];
        if (!in_bounds(nx, ny, nz)) {
            continue;
        }
        if (g_map[idx_of(nx, ny, nz)].kind == CELL_UNKNOWN) {
            return true;
        }
    }

    return false;
}

static int choose_unknown_edge_dir(int x, int y, int z, int *out_dir) {
    size_t i = idx_of(x, y, z);
    if (!g_map[i].exits_known) {
        return -1;
    }

    for (int d = 0; d < 6; d++) {
        if (!(g_map[i].exits & (1u << d))) {
            continue;
        }
        int nx = x + DX[d], ny = y + DY[d], nz = z + DZ[d];
        if (!in_bounds(nx, ny, nz)) {
            continue;
        }
        if (g_map[idx_of(nx, ny, nz)].kind == CELL_UNKNOWN) {
            *out_dir = d;
            return 0;
        }
    }

    return -1;
}

static int bfs_next_dir(int sx, int sy, int sz, bool to_frontier, int *out_dir) {
    size_t n = g_sx * g_sy * g_sz;
    int *parent = malloc(n * sizeof(int));
    int *pdir = malloc(n * sizeof(int));
    uint8_t *vis = calloc(n, 1);
    int *queue = malloc(n * sizeof(int));

    if (!parent || !pdir || !vis || !queue) {
        free(parent);
        free(pdir);
        free(vis);
        free(queue);
        return -1;
    }

    for (size_t i = 0; i < n; i++) {
        parent[i] = -1;
        pdir[i] = -1;
    }

    int start = (int)idx_of(sx, sy, sz);
    size_t goal = idx_of((int)g_sx - 1, (int)g_sy - 1, (int)g_sz - 1);

    int head = 0, tail = 0;
    queue[tail++] = start;
    vis[start] = 1;

    int target = -1;

    while (head < tail) {
        int cur = queue[head++];

        if (to_frontier && cell_has_unknown_exit_idx((size_t)cur)) {
            target = cur;
            break;
        }

        if (!to_frontier && (size_t)cur == goal && g_map[cur].kind == CELL_SAFE) {
            target = cur;
            break;
        }

        if (!g_map[cur].exits_known) {
            continue;
        }

        int x = (int)((size_t)cur % g_sx);
        int y = (int)(((size_t)cur / g_sx) % g_sy);
        int z = (int)((size_t)cur / (g_sx * g_sy));

        for (int d = 0; d < 6; d++) {
            if (!(g_map[cur].exits & (1u << d))) {
                continue;
            }
            int nx = x + DX[d], ny = y + DY[d], nz = z + DZ[d];
            if (!in_bounds(nx, ny, nz)) {
                continue;
            }
            int ni = (int)idx_of(nx, ny, nz);
            if (vis[ni] || g_map[ni].kind != CELL_SAFE) {
                continue;
            }
            vis[ni] = 1;
            parent[ni] = cur;
            pdir[ni] = d;
            queue[tail++] = ni;
        }
    }

    int rc = -1;
    if (target >= 0) {
        int cur = target;
        while (cur != start) {
            int p = parent[cur];
            if (p < 0) {
                rc = -1;
                break;
            }
            if (p == start) {
                *out_dir = pdir[cur];
                rc = 0;
                break;
            }
            cur = p;
        }
    }

    free(parent);
    free(pdir);
    free(vis);
    free(queue);
    return rc;
}

static int do_move(int fd, uint32_t dir) {
    if (ioctl(fd, CHAL_MOVE, &dir) < 0) {
        if (errno == EAGAIN) {
            return 1; // edge vanished/unusable from current node
        }
        return -1;
    }
    return 0;
}

int main(void) {
    int fd = open("/dev/challenge", O_RDWR);
    uint32_t seed = 0, sx = 0, sy = 0, sz = 0;

    if (fd < 0) {
        perror("open /dev/challenge");
        return 1;
    }

    if (get_u32(fd, CHAL_GET_SEED, &seed) < 0 || get_u32(fd, CHAL_GET_X, &sx) < 0 ||
        get_u32(fd, CHAL_GET_Y, &sy) < 0 || get_u32(fd, CHAL_GET_Z, &sz) < 0) {
        perror("ioctl dimension query");
        close(fd);
        return 1;
    }

    if (sx < 8 || sx > 16 || sy < 8 || sy > 16 || sz < 8 || sz > 16) {
        fprintf(stderr, "unexpected maze dimensions: %" PRIu32 "x%" PRIu32 "x%" PRIu32 "\n", sx, sy,
                sz);
        close(fd);
        return 1;
    }

    g_sx = sx;
    g_sy = sy;
    g_sz = sz;
    g_map = calloc(g_sx * g_sy * g_sz, sizeof(cell_t));
    if (!g_map) {
        perror("calloc map");
        close(fd);
        return 1;
    }

    cur_x = 0;
    cur_y = 0;
    cur_z = 0;

    printf("seed=0x%08" PRIx32 " dims=%zux%zux%zu\n", seed, g_sx, g_sy, g_sz);

    for (int iter = 0; iter < 200000; iter++) {
        uint32_t state = 0;
        if (get_state(fd, &state) < 0) {
            perror("ioctl CHAL_GET_STATE");
            free(g_map);
            close(fd);
            return 1;
        }

        if (state == STATE_WON) {
            char flag[CHAL_FLAG_LEN] = {0};
            if (ioctl(fd, CHAL_GET_FLAG, flag) < 0) {
                perror("ioctl CHAL_GET_FLAG");
                free(g_map);
                close(fd);
                return 1;
            }
            flag[CHAL_FLAG_LEN - 1] = '\0';
            printf("won: %s\n", flag);
            free(g_map);
            close(fd);
            return 0;
        }

        if (state == STATE_LOST) {
            if (in_bounds(cur_x, cur_y, cur_z)) {
                size_t i = idx_of(cur_x, cur_y, cur_z);
                g_map[i].kind = CELL_SPIKE;
                g_map[i].exits_known = 0;
                g_map[i].exits = 0;
            }

            if (ioctl(fd, CHAL_RESET) < 0) {
                perror("ioctl CHAL_RESET");
                free(g_map);
                close(fd);
                return 1;
            }

            cur_x = 0;
            cur_y = 0;
            cur_z = 0;
            continue;
        }

        if (query_and_store_exits(fd, cur_x, cur_y, cur_z) < 0) {
            perror("ioctl CHAL_GET_EXITS");
            free(g_map);
            close(fd);
            return 1;
        }

        int dir = -1;
        size_t goal = idx_of((int)g_sx - 1, (int)g_sy - 1, (int)g_sz - 1);

        int move_rc = -1;
        if (g_map[goal].kind == CELL_SAFE && bfs_next_dir(cur_x, cur_y, cur_z, false, &dir) == 0) {
            move_rc = do_move(fd, (uint32_t)dir);
            if (move_rc < 0) {
                perror("ioctl CHAL_MOVE(goal)");
                free(g_map);
                close(fd);
                return 1;
            }
        } else if (choose_unknown_edge_dir(cur_x, cur_y, cur_z, &dir) == 0) {
            move_rc = do_move(fd, (uint32_t)dir);
            if (move_rc < 0) {
                perror("ioctl CHAL_MOVE(explore)");
                free(g_map);
                close(fd);
                return 1;
            }
        } else if (bfs_next_dir(cur_x, cur_y, cur_z, true, &dir) == 0) {
            move_rc = do_move(fd, (uint32_t)dir);
            if (move_rc < 0) {
                perror("ioctl CHAL_MOVE(frontier)");
                free(g_map);
                close(fd);
                return 1;
            }
        } else {
            fprintf(stderr, "solver stuck: no frontier and goal unreachable\n");
            free(g_map);
            close(fd);
            return 2;
        }

        if (move_rc == 0 && dir >= 0 &&
            in_bounds(cur_x + DX[dir], cur_y + DY[dir], cur_z + DZ[dir])) {
            cur_x += DX[dir];
            cur_y += DY[dir];
            cur_z += DZ[dir];
        }
    }

    fprintf(stderr, "solver exceeded iteration budget\n");
    free(g_map);
    close(fd);
    return 3;
}
