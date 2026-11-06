#include "main.h"

void init_io(void)
{
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

void usage(void)
{
    printf("Usage: mygit <command> [args]\n\n");
    printf("Commands:\n");
    printf("  init              Initialize repository\n");
    printf("  add <file>        Stage file\n");
    printf("  commit -m <msg>   Create commit\n");
    printf("  branch [name]     List/create branches\n");
    printf("  checkout <branch> Switch branch\n");
    printf("  status            Show status\n");
    printf("  log               Show history\n");
}

int main(int argc, char *argv[])
{
    init_io();

    if (argc < 2)
    {
        usage();
        return 1;
    }

    const char *cmd = argv[1];

    if (strcmp(cmd, "init") == 0)
        return repo_init() == 0 ? 0 : 1;

    char root[PATH_LEN];
    if (repo_find_root(root, sizeof(root)) != 0)
    {
        fprintf(stderr, "Not a repository\n");
        return 1;
    }

    if (strcmp(cmd, "add") == 0)
    {
        if (argc < 3)
        {
            fprintf(stderr, "Usage: mygit add <file>\n");
            return 1;
        }
        return staging_add(argv[2]) == 0 ? 0 : 1;
    }
    if (strcmp(cmd, "commit") == 0)
    {
        if (argc < 4 || strcmp(argv[2], "-m") != 0)
        {
            fprintf(stderr, "Usage: mygit commit -m \"message\"\n");
            return 1;
        }
        return commit_create(argv[3]) == 0 ? 0 : 1;
    }
    if (strcmp(cmd, "branch") == 0)
    {
        if (argc < 3)
            return branch_list() == 0 ? 0 : 1;
        return branch_create(argv[2]) == 0 ? 0 : 1;
    }
    if (strcmp(cmd, "checkout") == 0)
    {
        if (argc < 3)
        {
            fprintf(stderr, "Usage: mygit checkout <branch>\n");
            return 1;
        }
        return branch_checkout(argv[2]) == 0 ? 0 : 1;
    }
    if (strcmp(cmd, "status") == 0)
        return status_show() == 0 ? 0 : 1;
    if (strcmp(cmd, "log") == 0)
        return commit_log() == 0 ? 0 : 1;

    fprintf(stderr, "Unknown command: %s\n", cmd);
    usage();
    return 1;
}
