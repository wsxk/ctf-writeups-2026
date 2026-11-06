from pwn import *

context.log_level = "debug"
io = remote("streams.tamuctf.com", 443, ssl=True, sni="hyper-neighbor")
io.interactive(prompt="")
