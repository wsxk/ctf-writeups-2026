# military-system

Author: `mike.exe`

Break into PATRIOT-7, recover the report, and extract the flag.

## Dev Notes

ARM64 Heap Challenge:

1. Leak a heap pointer and a PIE pointer from `View status`
2. Abuse the stale draft pointer after `Close channel`
3. Poison a tcache entry via the editor truncation bug
4. Reallocate a draft over the auth block and use `Transmit report`

Build and Run:

- `make build` rebuilds the ARM64 binary and the runtime image
- `make compile-native` builds a native Linux binary for the current host architecture
- `docker rm -f military-system && make run` starts the service on port `9001`

Also:

- On native `aarch64`, the entrypoint runs `./military-system` directly so seccomp works
- On non-ARM hosts, it falls back to `qemu-aarch64-static`

Debugging: use `make -f Makefile.debug build` and `make -f Makefile.debug run`. 
On non-ARM hosts, this starts QEMU with a gdbstub on port `1234`. Attach from the host with `gdb -q -nx ./military-system` and then `target remote 127.0.0.1:1234`.

## Solution

See `solve.py`.

flag:
`gigem{st4le_dr4ft_tcache_auth_bypass}`
