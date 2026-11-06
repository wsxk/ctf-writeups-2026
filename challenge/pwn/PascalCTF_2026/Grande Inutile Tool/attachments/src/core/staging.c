#include "../main.h"

int staging_load(StagingArea *s)
{
    s->count = 0;
    char *content;
    size_t size;
    if (file_read(INDEX_FILE, &content, &size) != 0)
        return -1;
    if (size == 0)
    {
        free(content);
        return 0;
    }

    char *line = strtok(content, "\n");
    while (line && s->count < MAX_FILES)
    {
        char *space = strchr(line, ' ');
        if (space)
        {
            *space = '\0';
            strncpy(s->files[s->count].hash, line, HASH_LEN);
            s->files[s->count].hash[HASH_LEN] = '\0';
            strncpy(s->files[s->count].path, space + 1, PATH_LEN - 1);
            s->count++;
        }
        line = strtok(NULL, "\n");
    }
    free(content);
    return 0;
}

int staging_save(const StagingArea *s)
{
    char *content = malloc(MAX_FILES * (HASH_LEN + PATH_LEN + 2));
    if (!content)
        return -1;
    content[0] = '\0';

    for (int i = 0; i < s->count; i++)
    {
        char line[HASH_LEN + PATH_LEN + 3];
        snprintf(line, sizeof(line), "%s %s\n", s->files[i].hash, s->files[i].path);
        strcat(content, line);
    }
    int result = file_write(INDEX_FILE, content, strlen(content));
    free(content);
    return result;
}

int staging_add(const char *path)
{
    if (!file_exists(path))
    {
        fprintf(stderr, "File not found: %s\n", path);
        return -1;
    }

    char repo_root[PATH_LEN];
    if (repo_find_root(repo_root, sizeof(repo_root)) != 0)
    {
        fprintf(stderr, "Not in a repository\n");
        return -1;
    }

    char resolved_repo[PATH_LEN];
    char resolved_file[PATH_LEN];
    if (realpath(repo_root, resolved_repo) == NULL)
    {
        fprintf(stderr, "Failed to resolve repository path\n");
        return -1;
    }
    if (realpath(path, resolved_file) == NULL)
    {
        fprintf(stderr, "Failed to resolve file path\n");
        return -1;
    }

    size_t repo_len = strlen(resolved_repo);
    if (strncmp(resolved_file, resolved_repo, repo_len) != 0 ||
        (resolved_file[repo_len] != '/' && resolved_file[repo_len] != '\0'))
    {
        fprintf(stderr, "File is outside the repository: %s\n", path);
        return -1;
    }

    StagingArea *s = malloc(sizeof(StagingArea));
    if (!s)
        return -1;
    if (staging_load(s) != 0)
        s->count = 0;

    char hash[HASH_LEN + 1];
    if (object_store(path, hash) != 0)
    {
        free(s);
        return -1;
    }

    for (int i = 0; i < s->count; i++)
    {
        if (strcmp(s->files[i].path, path) == 0)
        {
            strncpy(s->files[i].hash, hash, HASH_LEN);
            int result = staging_save(s);
            free(s);
            return result;
        }
    }

    if (s->count >= MAX_FILES)
    {
        fprintf(stderr, "Index full\n");
        free(s);
        return -1;
    }

    strncpy(s->files[s->count].hash, hash, HASH_LEN);
    s->files[s->count].hash[HASH_LEN] = '\0';
    strncpy(s->files[s->count].path, path, PATH_LEN - 1);
    s->count++;

    printf("Added '%s'\n", path);
    int result = staging_save(s);
    free(s);
    return result;
}

void staging_clear(void) { file_write(INDEX_FILE, "", 0); }
