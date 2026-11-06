#include "../main.h"

int file_exists(const char *path)
{
    struct stat st;
    return stat(path, &st) == 0 && S_ISREG(st.st_mode);
}

int dir_exists(const char *path)
{
    struct stat st;
    return stat(path, &st) == 0 && S_ISDIR(st.st_mode);
}

int dir_create(const char *path)
{
    char tmp[PATH_LEN];
    char *p;
    size_t len;

    snprintf(tmp, sizeof(tmp), "%s", path);
    len = strlen(tmp);
    if (tmp[len - 1] == '/')
        tmp[len - 1] = 0;

    for (p = tmp + 1; *p; p++)
    {
        if (*p == '/')
        {
            *p = 0;
            if (!dir_exists(tmp)) {
                mkdir(tmp, 0700);
                chown(tmp, 0, 0);
            }
            struct stat st;
            if (stat(tmp, &st) != 0 || (st.st_mode & 0777) != 0700 || st.st_uid != 0 || st.st_gid != 0) {
                return -1;
            }
            *p = '/';
        }
    }
    if (!dir_exists(tmp)) {
        mkdir(tmp, 0700);
        chown(tmp, 0, 0);
    }
    struct stat st;
    if (stat(tmp, &st) != 0 || (st.st_mode & 0777) != 0700 || st.st_uid != 0 || st.st_gid != 0) {
        return -1;
    }
    return 0;
}

int file_read(const char *path, char **content, size_t *size)
{
    FILE *f = fopen(path, "rb");
    if (!f)
        return -1;

    fseek(f, 0, SEEK_END);
    *size = ftell(f);
    fseek(f, 0, SEEK_SET);

    *content = malloc(*size + 1);
    if (!*content)
    {
        fclose(f);
        return -1;
    }

    fread(*content, 1, *size, f);
    (*content)[*size] = '\0';
    fclose(f);
    return 0;
}

int file_write(const char *path, const char *content, size_t size)
{
    FILE *f = fopen(path, "wb");
    if (!f)
        return -1;
    fwrite(content, 1, size, f);
    fclose(f);
    return 0;
}

int file_copy(const char *src, const char *dst)
{
    char *content;
    size_t size;
    if (file_read(src, &content, &size) != 0)
        return -1;

    char dir[PATH_LEN];
    strncpy(dir, dst, PATH_LEN);
    char *slash = strrchr(dir, '/');
    if (slash)
    {
        *slash = '\0';
        dir_create(dir);
    }

    int ret = file_write(dst, content, size);
    free(content);
    return ret;
}
