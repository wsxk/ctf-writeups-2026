# Explorer

**Category:** Reverse Engineering | **Difficulty:** Hard | **Flag:** `dice{twisty_rusty_kernel_maze}`

## Overview
A Linux kernel module written in Rust implements a 3D maze game accessible via `/dev/challenge` ioctls. Navigate the maze, avoid decoy exits, find the real exit, and read the flag.

## Solution

### 1. Initial Recon
The challenge provides `bzImage` and `initramfs.cpio.gz` — a custom Linux kernel with a Rust kernel module. Connecting via netcat boots a QEMU VM with a shell. The kernel module creates `/dev/challenge` as a misc device.

### 2. Reverse Engineering the Kernel Module
Using GDB dynamic analysis (attaching to QEMU), I located the misc device struct in `.bss` and dumped the `file_operations` table to find the `open`, `ioctl`, and `release` handlers.

Through dynamic probing (compiling test binaries and injecting them into the initramfs), I enumerated all supported ioctl commands:

| Command | Description |
|---------|-------------|
| `0x80046481-83` | Get maze dimensions (3 axes, range 8-16 each) |
| `0x80046484` | Get step counter |
| `0x80046485` | Get status: 0=playing, 1=WIN, 2=decoy |
| `0x80046486` | Get wall bitfield for current cell (6 bits, 6 directions) |
| `0x80406487` | Get flag (64 bytes, only when status==1) |
| `0x40046488` | Move in direction (0-5) |
| `0x6489` | Reset position to start |

### 3. Understanding the Maze
The maze is 3D with 6 movement directions (opposites: 0<->2, 1<->3, 4<->5). Each cell has a wall bitfield indicating which directions have passages. The maze has **multiple decoy exits** (status=2) and **one real exit** (status=1). Hitting a decoy locks movement — you must reset and try again.

### 4. Writing the Solver
A DFS maze solver with decoy avoidance:
1. Traverse the maze using DFS, querying walls via ioctl `0x86` and moving via ioctl `0x88`
2. Check status after each move — if decoy (status=2), record that cell position as "bad"
3. Reset via ioctl `0x6489` and re-traverse, skipping known bad cells
4. Repeat until finding the real exit (status=1)
5. Read flag with ioctl `0x87`

The solver was compiled as a 13KB static binary using raw syscalls (no libc) to minimize upload size:
```
gcc -nostdlib -static -Os -fno-builtin -o solve_tiny solve_tiny.c -Wl,--gc-sections && strip solve_tiny
```

### 5. Remote Deployment
Upload the binary to the remote VM via base64 chunks over the shell, decode, and execute. The solver typically finds the flag in 5-15 attempts (resets).

See `solve_tiny.c` for the maze solver and `solve.py` for the remote upload wrapper.

## Key Takeaways
- Rust kernel modules can be reversed through dynamic analysis even when the kernel is stripped
- For kernel challenges, injecting test binaries into the initramfs is faster than static RE
- Decoy exits are a common maze anti-solve technique — track bad positions across resets
- Raw syscall binaries (no libc) keep upload size minimal for remote kernel challenges
