#include "../main.h"

int repo_init(void)
{
    if (dir_exists(REPO_DIR))
    {
        printf("Repository already initialized.\n");
        return 0;
    }

    dir_create(REPO_DIR);
    dir_create(OBJECTS_DIR);
    dir_create(REFS_DIR);
    dir_create(HEADS_DIR);
    dir_create(COMMITS_DIR);

    repo_write_head("refs/heads/main");
    file_write(INDEX_FILE, "", 0);

    char main_ref[PATH_LEN];
    snprintf(main_ref, sizeof(main_ref), "%s/main", HEADS_DIR);
    file_write(main_ref, "", 0);

    printf("Initialized empty repository in %s/\n", REPO_DIR);
    return 0;
}

int repo_find_root(char *root, size_t size)
{
    char cwd[PATH_LEN];
    if (getcwd(cwd, sizeof(cwd)) == NULL)
        return -1;

    char check[PATH_LEN];
    while (1)
    {
        snprintf(check, sizeof(check), "%s/%s", cwd, REPO_DIR);
        if (dir_exists(check))
        {
            strncpy(root, cwd, size);
            return 0;
        }
        char *slash = strrchr(cwd, '/');
        if (!slash || slash == cwd)
            break;
        *slash = '\0';
    }
    return -1;
}

int repo_read_head(char *ref, size_t size)
{
    char *content;
    size_t len;
    if (file_read(HEAD_FILE, &content, &len) != 0)
        return -1;

    while (len > 0 && (content[len - 1] == '\n' || content[len - 1] == '\r'))
        content[--len] = '\0';

    strncpy(ref, content, size);
    free(content);
    return 0;
}

int repo_write_head(const char *ref)
{
    char content[PATH_LEN];
    snprintf(content, sizeof(content), "%s\n", ref);
    return file_write(HEAD_FILE, content, strlen(content));
}

char *repo_current_branch(void)
{
    static char branch[PATH_LEN];
    if (repo_read_head(branch, sizeof(branch)) != 0)
        return NULL;
    char *name = strrchr(branch, '/');
    return name ? name + 1 : branch;
}
