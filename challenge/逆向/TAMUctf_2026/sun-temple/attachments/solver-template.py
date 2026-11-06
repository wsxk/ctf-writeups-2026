from pwn import *

r = remote("streams.tamuctf.com", 443, ssl=True, sni="sun-temple")
r.interactive(prompt="")
