from pwn import *
context.arch = "amd64"

read_code = asm('''
                push rdx
                push rcx
                mov rdx, 0x10000000
                mov rcx, qword ptr [rdx]
                mov byte ptr [rsi], cl
                shr rcx, 8
                mov qword ptr [rdx], rcx
                mov rax, 1
                pop rcx
                pop rdx
                ret
                ''')

carray = [hex(x) for x in read_code]
carray = ', '.join(carray)
print(f'unsigned char read_code[] = {{{carray}}};')