#ifndef MAIN_H
#define MAIN_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>

#define REPO_DIR ".mygit"
#define OBJECTS_DIR ".mygit/objects"
#define REFS_DIR ".mygit/refs"
#define HEADS_DIR ".mygit/refs/heads"
#define COMMITS_DIR ".mygit/commits"
#define HEAD_FILE ".mygit/HEAD"
#define INDEX_FILE ".mygit/index"

#define HASH_LEN 40
#define PATH_LEN 1024
#define MSG_LEN 256
#define MAX_FILES 1000

typedef struct
{
    char hash[HASH_LEN + 1];
    char path[PATH_LEN];
} StagedFile;

typedef struct
{
    StagedFile files[MAX_FILES];
    int count;
} StagingArea;

typedef struct
{
    char hash[HASH_LEN + 1];
    char parent[HASH_LEN + 1];
    char message[MSG_LEN];
    char timestamp[64];
    int file_count;
    StagedFile files[MAX_FILES];
} Commit;

int repo_init(void);
int repo_find_root(char *root, size_t size);
int repo_read_head(char *ref, size_t size);
int repo_write_head(const char *ref);
char *repo_current_branch(void);

void object_hash(const char *data, size_t len, char *out);
int object_store(const char *path, char *hash_out);
int object_read(const char *hash, char **content, size_t *size);

int staging_load(StagingArea *s);
int staging_save(const StagingArea *s);
int staging_add(const char *path);
void staging_clear(void);

int commit_create(const char *msg);
int commit_read(const char *hash, Commit *c);
int commit_log(void);
char *commit_current(void);

int branch_create(const char *name);
int branch_list(void);
int branch_checkout(const char *name);
int branch_get_commit(const char *name, char *hash_out);

int status_show(void);

int file_exists(const char *path);
int dir_exists(const char *path);
int dir_create(const char *path);
int file_read(const char *path, char **content, size_t *size);
int file_write(const char *path, const char *content, size_t size);
int file_copy(const char *src, const char *dst);

#endif
