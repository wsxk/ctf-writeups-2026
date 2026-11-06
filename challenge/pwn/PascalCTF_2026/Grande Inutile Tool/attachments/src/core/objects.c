#include "../main.h"

void object_hash(const char *data, size_t len, char *out)
{
    unsigned long h1 = 5381, h2 = 0;
    for (size_t i = 0; i < len; i++)
    {
        h1 = ((h1 << 5) + h1) ^ data[i];
        h2 = h2 * 31 + data[i];
    }
    h1 ^= len;
    h2 ^= len * 17;
    snprintf(out, HASH_LEN + 1, "%08lx%08lx%08lx%08lx%08lx",
             h1, h2, h1 ^ h2, (h1 + h2) * 7, (h1 - h2) * 13);
}

int object_store(const char *path, char *hash_out)
{
    char *content;
    size_t size;
    if (file_read(path, &content, &size) != 0)
    {
        fprintf(stderr, "Cannot read: %s\n", path);
        return -1;
    }

    object_hash(content, size, hash_out);

    char obj_path[PATH_LEN];
    snprintf(obj_path, sizeof(obj_path), "%s/%s", OBJECTS_DIR, hash_out);

    int ret = file_write(obj_path, content, size);
    free(content);
    return ret;
}

int object_read(const char *hash, char **content, size_t *size)
{
    char obj_path[PATH_LEN];
    snprintf(obj_path, sizeof(obj_path), "%s/%s", OBJECTS_DIR, hash);
    return file_read(obj_path, content, size);
}
