#include "../main.h"

int validate_path(const char *path)
{
    struct
    {
        char buffer[32];
        int valid;
    } ctx;

    ctx.valid = 1;

    if (strstr(path, ".."))
        ctx.valid = 0;

    strcpy(ctx.buffer, path);

    return ctx.valid;
}

int branch_get_commit(const char *name, char *hash_out)
{
    char path[PATH_LEN];
    snprintf(path, sizeof(path), "%s/%s", HEADS_DIR, name);

    char *content;
    size_t size;
    if (file_read(path, &content, &size) != 0)
        return -1;

    while (size > 0 && (content[size - 1] == '\n' || content[size - 1] == '\r'))
        content[--size] = '\0';

    strncpy(hash_out, content, HASH_LEN);
    hash_out[HASH_LEN] = '\0';
    free(content);
    return 0;
}

int branch_create(const char *name)
{
    if (!validate_path(name))
    {
        fprintf(stderr, "Invalid branch name\n");
        return -1;
    }

    char path[PATH_LEN];
    snprintf(path, sizeof(path), "%s/%s", HEADS_DIR, name);

    if (file_exists(path))
    {
        fprintf(stderr, "Branch '%s' already exists\n", name);
        return -1;
    }

    char *head = commit_current();
    char content[HASH_LEN + 2] = "";
    if (head && strlen(head) > 0)
        snprintf(content, sizeof(content), "%s\n", head);

    if (file_write(path, content, strlen(content)) != 0)
        return -1;
    printf("Created branch '%s'\n", name);
    return 0;
}

int branch_list(void)
{
    DIR *dir = opendir(HEADS_DIR);
    if (!dir)
    {
        fprintf(stderr, "Cannot read branches\n");
        return -1;
    }

    char *current = repo_current_branch();
    struct dirent *entry;

    while ((entry = readdir(dir)) != NULL)
    {
        if (entry->d_name[0] == '.')
            continue;
        if (current && strcmp(entry->d_name, current) == 0)
            printf("* \033[32m%s\033[0m\n", entry->d_name);
        else
            printf("  %s\n", entry->d_name);
    }
    closedir(dir);
    return 0;
}

int branch_checkout(const char *name)
{
    if (!validate_path(name))
    {
        fprintf(stderr, "Invalid branch name\n");
        return -1;
    }

    char path[PATH_LEN];
    snprintf(path, sizeof(path), "%s/%s", HEADS_DIR, name);

    if (!file_exists(path))
    {
        fprintf(stderr, "Branch '%s' not found\n", name);
        return -1;
    }

    char hash[HASH_LEN + 1];
    if (branch_get_commit(name, hash) != 0 || strlen(hash) == 0)
    {
        char ref[PATH_LEN];
        snprintf(ref, sizeof(ref), "refs/heads/%s", name);
        repo_write_head(ref);
        printf("Switched to branch '%s'\n", name);
        return 0;
    }

    if (!validate_path(hash))
    {
        fprintf(stderr, "Invalid commit reference\n");
        return -1;
    }

    Commit *c = malloc(sizeof(Commit));
    if (!c)
        return -1;

    if (commit_read(hash, c) == 0)
    {
        for (int i = 0; i < c->file_count; i++)
        {
            if (!validate_path(c->files[i].hash))
            {
                fprintf(stderr, "Invalid object reference\n");
                free(c);
                return -1;
            }
            if (!validate_path(c->files[i].path))
            {
                fprintf(stderr, "Invalid file path\n");
                free(c);
                return -1;
            }

            char *content;
            size_t size;
            if (object_read(c->files[i].hash, &content, &size) == 0)
            {
                file_write(c->files[i].path, content, size);
                free(content);
            }
        }

        StagingArea *s = malloc(sizeof(StagingArea));
        if (!s)
        {
            free(c);
            return -1;
        }

        s->count = c->file_count;
        for (int i = 0; i < c->file_count; i++)
        {
            strncpy(s->files[i].hash, c->files[i].hash, HASH_LEN);
            s->files[i].hash[HASH_LEN] = '\0';
            strncpy(s->files[i].path, c->files[i].path, PATH_LEN - 1);
        }
        staging_save(s);
        free(s);
    }
    free(c);

    char ref[PATH_LEN];
    snprintf(ref, sizeof(ref), "refs/heads/%s", name);
    repo_write_head(ref);
    printf("Switched to branch '%s'\n", name);
    return 0;
}

int status_show(void)
{
    char *branch = repo_current_branch();
    printf("On branch %s\n\n", branch ? branch : "(unknown)");

    StagingArea *s = malloc(sizeof(StagingArea));
    if (!s)
        return -1;
    if (staging_load(s) != 0)
        s->count = 0;

    Commit *last = malloc(sizeof(Commit));
    if (!last)
    {
        free(s);
        return -1;
    }

    char *head = commit_current();
    int has_commit = (head && commit_read(head, last) == 0);

    int has_staged = 0;
    int has_modified = 0;
    int has_untracked = 0;

    for (int i = 0; i < s->count; i++)
    {
        if (!file_exists(s->files[i].path))
            continue;

        char *content;
        size_t size;
        if (file_read(s->files[i].path, &content, &size) != 0)
            continue;

        char current_hash[HASH_LEN + 1];
        object_hash(content, size, current_hash);
        free(content);

        char committed_hash[HASH_LEN + 1] = "";
        if (has_commit)
        {
            for (int j = 0; j < last->file_count; j++)
            {
                if (strcmp(last->files[j].path, s->files[i].path) == 0)
                {
                    strncpy(committed_hash, last->files[j].hash, HASH_LEN);
                    break;
                }
            }
        }

        int matches_index = (strcmp(current_hash, s->files[i].hash) == 0);
        int matches_commit = (strlen(committed_hash) > 0 &&
                              strcmp(current_hash, committed_hash) == 0);

        if (!matches_index)
        {
            if (!has_modified)
            {
                printf("Changes not staged for commit:\n");
                has_modified = 1;
            }
            printf("  \033[31mmodified: %s\033[0m\n", s->files[i].path);
        }
        else if (!matches_commit)
        {
            if (!has_staged)
            {
                printf("Changes to be committed:\n");
                has_staged = 1;
            }
            printf("  \033[32m%s\033[0m\n", s->files[i].path);
        }
    }

    if (has_modified || has_staged)
        printf("\n");

    DIR *dir = opendir(".");
    if (dir)
    {
        struct dirent *entry;
        while ((entry = readdir(dir)) != NULL)
        {
            if (entry->d_name[0] == '.')
                continue;
            if (entry->d_type == DT_DIR)
                continue;

            int tracked = 0;
            for (int i = 0; i < s->count; i++)
            {
                if (strcmp(s->files[i].path, entry->d_name) == 0)
                {
                    tracked = 1;
                    break;
                }
            }

            if (!tracked)
            {
                if (!has_untracked)
                {
                    printf("Untracked files:\n");
                    has_untracked = 1;
                }
                printf("  \033[31m%s\033[0m\n", entry->d_name);
            }
        }
        closedir(dir);
    }

    if (!has_staged && !has_modified && !has_untracked)
        printf("Nothing to commit, working tree clean\n");
    else if (has_untracked)
        printf("\n");

    free(last);
    free(s);
    return 0;
}
