# Writeup: Inheritance

**Category:** Pwn
**Difficulty:** 3/5
**Author:** mrdebator

## Challenge Overview
The `inheritance` challenge explores a common misconfiguration in Linux systems programming combined with command injection evasion.

The provided service reads a secret "configuration" (the flag) into a temporary, anonymous memory file using `memfd_create()`. It then prompts the user for a command and executes it using `system()`. To prevent trivial reads, the application implements a strict filter blocking shell redirection characters (`<`, `>`) and specific keywords (`flag`, `proc`, `fd`).

## The Vulnerability: File Descriptor Leaks
When a C program calls `system()`, the operating system uses `fork()` to clone the current process, and then `execve()` to replace the clone with a `/bin/sh` shell.

By default in Linux, all open file descriptors (FDs) are inherited by the child process unless they are explicitly created with the `O_CLOEXEC` (Close-on-Exec) flag. Because the developer used `memfd_create("secret_config", 0)` instead of `memfd_create("secret_config", MFD_CLOEXEC)`, the newly spawned shell secretly inherits full read access to the memory file containing the flag!

## The Exploit: Bypassing the Filter
1. **Identify the Leaked FD:** The program conveniently prints the File Descriptor number it was assigned (e.g., `FD 4` or `FD 5`).
2. **Understand the Restrictions:** We know the file is accessible via the Linux procfs at `/proc/self/fd/X` (where X is our FD number). However, the program blocks `<` and `>`, preventing standard shell redirection like `cat <&4`. It also blocks the strings `proc` and `fd`, preventing us from simply typing `cat /proc/self/fd/4`.
3. **Bash Evasion:** Because `system()` passes our input to a `/bin/sh` interpreter, we can use standard Bash parsing tricks to evade the string filter. By wrapping parts of the blacklisted words in single quotes, we break the C-level `strstr` check, but Bash seamlessly reassembles them before execution!

**Intended Payload:** ```bash
cat /p'r'oc/self/f'd'/4
