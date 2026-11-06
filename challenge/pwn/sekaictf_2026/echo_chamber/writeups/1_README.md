# Echo Chamber

**Category:** pwn | **Flag:** `SEKAI{the_best_time_to_write_challenges_is_always_during_the_ctf_:P_}`

## Challenge Description

A small multi-threaded HTTP server (`chal`, source in [`chal.c`](chal.c)) that accepts `GET`/`POST` requests, parses headers into a linked list, and — for `POST` — reads a body of `Content-Length` bytes and echoes it straight back. Each connection is dispatched to a worker thread. The official challenge prose was not recorded; everything below is derived from the provided source and binary.

Deployment (from [`Dockerfile`](Dockerfile) / [`run.sh`](run.sh)) runs under Ubuntu 22.04 glibc with the following tunables and a crash-restart loop:

```sh
GLIBC_TUNABLES="glibc.malloc.tcache_count=0:glibc.malloc.tcache_max=0:glibc.malloc.arena_max=8"
while true; do ./chal; done
```

## Initial Analysis

Build flags (from [`Makefile`](Makefile)): full RELRO (`-Wl,-z,now`), PIE, stack canary (`-fstack-protector-all`). Mitigations are all on, so this is a heap/thread exploitation problem, not a stack smash.

Two environment facts shape the whole exploit:

- **`arena_max=8`** — glibc caps the number of malloc arenas at 8. Once 8 threads exist, new worker threads must *reuse* an existing arena, so multiple workers end up sharing one heap.
- **`tcache_count=0` / `tcache_max=0`** — tcache is disabled at startup, removing the easy exploitation path (but not permanently, see below).

The server also calls `guard_region()` on startup and per-connection, mapping a random number of `PROT_NONE` pages to add entropy to the heap/mmap layout.

## Vulnerability / Core Concept

The `POST` body handler parses `Content-Length` with `strtoll` into a `size_t`:

```c
size_t body_len = strtoll(content_length->val, &end, 10);
body = malloc(body_len + 1);
size_t nbytes = readn(self->fd, body, body_len);
body[nbytes] = 0;
```

Sending `Content-Length: -1` makes `strtoll` return `-1`, which becomes `0xffffffffffffffff` as a `size_t`. Then `body_len + 1` wraps to `0`, so the server does `malloc(0)` (a minimal `0x20` chunk) while `readn()` still tries to read a near-infinite body into it. **Tiny chunk, unbounded read → heap overflow.**

Because workers share arenas (via `arena_max=8`), one thread's overflow corrupts chunks that other threads allocate/free from the same heap. That cross-thread interaction is the engine for the entire chain.

## Exploitation

The full solve is [`solve.py`](solve.py) — a single file that is both the exploit and a retry harness. It re-invokes itself per attempt (via a `__exploit__` sentinel argv) so pwntools/ELF globals and worker threads start clean each time, and it scans output for `SEKAI{...}`. The exploit is inherently flaky (thread scheduling, arena reuse timing, ASLR-sensitive leaks), hence the retry loop.

The chain, stage by stage:

**1. Spray threads to force arena reuse.** Open 8 connections to claim all 8 arenas (one thread each), then spray `threads_per_arena = 3` more so several workers share each arena:

```python
for i in range(8):
    p = conn(); send(p, make_post("/", str(i).encode())); arenas.insert(0, [p])
while len(arenas[0]) < threads_per_arena:
    new_thread()
```

**2. Leak heap / libc / TLS.** A large `0x800` body allocation is held open in one thread (request left unfinished). Other threads in the same arena use the `-1` overflow to forge chunk metadata so allocator/thread objects (a new worker's `Worker` struct and its `dtv`) land *inside* that body buffer. Completing the request echoes the body back, leaking:

- a heap pointer,
- a libc/`main_arena` pointer (`libc.address = libc_leak - (main_arena + 8)`),
- the new thread's `dtv`/TLS pointer, from which the worker's stack `buf` is at a fixed offset (`addrof_buf = target_tls - 0x2800`).

The worker's own fd is also leaked so the shell fd is derived rather than hard-coded (remote wrappers shift fd numbering):

```python
target_fd = u32(worker_leak[0x70:0x74])
shell_fd  = target_fd - pre_leak_conn_count
```

The harness validates the libc leak is page-aligned and in the expected range before continuing, aborting the attempt otherwise.

**3. Re-enable tcache globally.** Even with `tcache_count=0`, `mp_.tcache_max_bytes` is `0x21`, so `0x20` still counts as a tcache bin. The exploit builds a fake `tcache_perthread_struct` on a worker's stack pointing `tcache[0x20]` at `mp_ + 112`, then overwrites the thread's `tcache` pointer (in TLS) to reference it. A controlled allocation through that bin writes into the global `mp_`, restoring `tcache_count`/`tcache_max` so freshly-created threads initialize a real tcache:

```python
tcache = TcachePerthreadStruct()
tcache.set(0x20, libc.sym.mp_ + 112)   # the only "available" bin
...
send(p, make_post("/", p64(0x40) + p64(0x411) + p32(0x10))[:-1])  # patch mp_
```

The "arbitrary" free needed here is built by corrupting a `Header->next` pointer (headers are freed at request end) so `free()` is called on a fake `0x20` chunk placed on the target thread's stack — the `arb_free()` helper drives this via a keep-alive header overflow.

**4. Hijack a worker's return address.** With tcache live, a new worker's tcache is poisoned so a controlled allocation lands on that worker's saved return address (`addrof_rop = target_tls - 0x2960`). A ROP chain is built from the leaked libc.

**5. Get the flag.** In `AUTO` mode (used for remote), instead of a single interactive `dup2` shell — brittle because the client socket fd varies remotely — the ROP runs `system()` with a command that broadcasts the flag to every plausible fd, and the harness reads all open tubes:

```python
inner_cmd = args.CMD or "cat /app/flag.txt; cat flag.txt"
cmd = ("for i in " + " ".join(map(str, range(4, 64))) +
       f";do ({inner_cmd}) 2>/dev/null >&$i; done").encode() + b"\x00"
rop_builder = ROP(libc, base=addrof_rop)
rop_builder.raw(ROP(libc).find_gadget(["ret"])[0])  # system() stack alignment
rop_builder.system(addrof_rop + cmd_off)
```

Because failed attempts leave dirty arenas and stuck threads behind, the harness first uses the same `-1` bug to crash `chal` (the `run.sh` loop restarts it) for a fresh process before each real attempt (`RESET` mode).

Run it (SSL on by default; the instancer fronts the service with TLS):

```bash
./solve.py <INSTANCE_HOST> <PORT>
# or a pasted ncat line:
./solve.py ncat --ssl <INSTANCE_HOST> <PORT>
# local plaintext test:
./solve.py --no-ssl 127.0.0.1 9999
```

## Flag

```text
SEKAI{the_best_time_to_write_challenges_is_always_during_the_ctf_:P_}
```

## Key Takeaways

- `strtoll` into an unsigned `size_t` plus a `+1` turns `Content-Length: -1` into `malloc(0)` with an unbounded read — a signedness/wraparound heap overflow.
- `arena_max=8` makes worker threads share arenas, converting one thread's overflow into a cross-thread heap-corruption primitive.
- Disabled tcache is not permanent: with `tcache_max_bytes` still non-zero, corrupting the global `mp_` re-enables tcache for newly spawned threads.
- Leaking a thread's `dtv`/TLS gives a deterministic path from ASLR'd TLS to that thread's stack buffer and saved return address.
- Real heap exploits are probabilistic: the solve is written as a reset-try-validate-retry harness, and remote-friendly output uses fd broadcasting instead of assuming a fixed shell fd.
