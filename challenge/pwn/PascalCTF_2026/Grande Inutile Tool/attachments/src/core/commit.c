#include "../main.h"

char *commit_current(void)
{
    static char hash[HASH_LEN + 1];
    char head_ref[PATH_LEN];
    if (repo_read_head(head_ref, sizeof(head_ref)) != 0)
        return NULL;

    char ref_path[PATH_LEN];
    snprintf(ref_path, sizeof(ref_path), "%s/%s", REPO_DIR, head_ref);

    char *content;
    size_t size;
    if (file_read(ref_path, &content, &size) != 0)
        return NULL;

    while (size > 0 && (content[size - 1] == '\n' || content[size - 1] == '\r'))
        content[--size] = '\0';

    if (size == 0)
    {
        free(content);
        return NULL;
    }

    strncpy(hash, content, HASH_LEN);
    hash[HASH_LEN] = '\0';
    free(content);
    return hash;
}

int commit_create(const char *msg)
{
    StagingArea *s = malloc(sizeof(StagingArea));
    if (!s)
        return -1;

    if (staging_load(s) != 0 || s->count == 0)
    {
        fprintf(stderr, "Nothing to commit\n");
        free(s);
        return -1;
    }

    char *data = malloc(MAX_FILES * (HASH_LEN + PATH_LEN + 10) + 512);
    if (!data)
    {
        free(s);
        return -1;
    }
    char *ptr = data;

    char *parent = commit_current();
    if (parent)
        ptr += sprintf(ptr, "parent %s\n", parent);

    ptr += sprintf(ptr, "timestamp %ld\n", time(NULL));
    ptr += sprintf(ptr, "message %s\n", msg);
    ptr += sprintf(ptr, "files %d\n", s->count);

    for (int i = 0; i < s->count; i++)
        ptr += sprintf(ptr, "%s %s\n", s->files[i].hash, s->files[i].path);

    char commit_hash[HASH_LEN + 1];
    object_hash(data, strlen(data), commit_hash);

    char commit_path[PATH_LEN];
    snprintf(commit_path, sizeof(commit_path), "%s/%s", COMMITS_DIR, commit_hash);
    if (file_write(commit_path, data, strlen(data)) != 0)
    {
        free(data);
        free(s);
        return -1;
    }

    char head_ref[PATH_LEN];
    if (repo_read_head(head_ref, sizeof(head_ref)) != 0)
    {
        free(data);
        free(s);
        return -1;
    }

    char ref_path[PATH_LEN];
    snprintf(ref_path, sizeof(ref_path), "%s/%s", REPO_DIR, head_ref);

    char hash_content[HASH_LEN + 2];
    snprintf(hash_content, sizeof(hash_content), "%s\n", commit_hash);
    if (file_write(ref_path, hash_content, strlen(hash_content)) != 0)
    {
        free(data);
        free(s);
        return -1;
    }

    printf("[%s %s] %s\n", repo_current_branch(), commit_hash, msg);
    printf(" %d file(s) changed\n", s->count);
    free(data);
    free(s);
    return 0;
}

int commit_read(const char *hash, Commit *c)
{
    char path[PATH_LEN];
    snprintf(path, sizeof(path), "%s/%s", COMMITS_DIR, hash);

    char *content;
    size_t size;
    if (file_read(path, &content, &size) != 0)
        return -1;

    memset(c, 0, sizeof(Commit));
    strncpy(c->hash, hash, HASH_LEN);

    char *line = strtok(content, "\n");
    int reading_files = 0, idx = 0;

    while (line)
    {
        if (reading_files && idx < c->file_count)
        {
            char *space = strchr(line, ' ');
            if (space)
            {
                *space = '\0';
                strncpy(c->files[idx].hash, line, HASH_LEN);
                strncpy(c->files[idx].path, space + 1, PATH_LEN - 1);
                idx++;
            }
        }
        else if (strncmp(line, "parent ", 7) == 0)
        {
            strncpy(c->parent, line + 7, HASH_LEN);
        }
        else if (strncmp(line, "timestamp ", 10) == 0)
        {
            strncpy(c->timestamp, line + 10, sizeof(c->timestamp) - 1);
        }
        else if (strncmp(line, "message ", 8) == 0)
        {
            strncpy(c->message, line + 8, MSG_LEN - 1);
        }
        else if (strncmp(line, "files ", 6) == 0)
        {
            c->file_count = atoi(line + 6);
            reading_files = 1;
        }
        line = strtok(NULL, "\n");
    }
    free(content);
    return 0;
}

int commit_log(void)
{
    char *head = commit_current();
    if (!head)
    {
        printf("No commits yet\n");
        return 0;
    }

    char hash[HASH_LEN + 1];
    strncpy(hash, head, HASH_LEN);
    hash[HASH_LEN] = '\0';

    Commit *c = malloc(sizeof(Commit));
    if (!c)
        return -1;

    while (strlen(hash) > 0)
    {
        if (commit_read(hash, c) != 0)
            break;

        time_t ts = atol(c->timestamp);
        char *t = ctime(&ts);
        if (t)
            t[strlen(t) - 1] = '\0';

        printf("\033[33mcommit %s\033[0m\n", c->hash);
        printf("Date:   %s\n\n    %s\n\n", t ? t : c->timestamp, c->message);

        if (strlen(c->parent) > 0)
        {
            strncpy(hash, c->parent, HASH_LEN);
            hash[HASH_LEN] = '\0';
        }
        else
        {
            break;
        }
    }
    free(c);
    return 0;
}
