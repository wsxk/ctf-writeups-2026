def rol(x, r):
    return ((x << (r & 31)) | (x >> ((32 - r) & 31))) & 0xFFFFFFFF


def ror(x, r):
    return ((x >> (r & 31)) | (x << ((32 - r) & 31))) & 0xFFFFFFFF


body_t = [
    0x40, 0x41, 0x3F, 0xD4, 0x15, 0xB5, 0x48, 0x2B, 0xF7, 0x70, 0xC2, 0x07,
    0x55, 0xB7, 0xBC, 0x35, 0xE7, 0xF1, 0xC8, 0x29, 0x9C, 0x95, 0x1E, 0x84,
    0xC2, 0x20, 0xE0, 0x9C, 0xFC, 0x68, 0x7C, 0x1E, 0xDE, 0x98, 0xD9, 0xF7,
    0xDA,
]

state = 0x1337C0DE ^ 0xC0DEF00D
acc = 0x31415926
score = 0
body = []

for i, t in enumerate(body_t):
    state = (state + 0x9E3779B9 + i * 0x045D9F3B) & 0xFFFFFFFF
    state = (rol(state, 5) ^ ror(state, 3)) & 0xFFFFFFFF
    key = (state ^ (state >> 8) ^ (i * 17)) & 0xFF
    add = ((state >> 16) + i * 11) & 0xFF
    ch = ((t - add) & 0xFF) ^ key
    body.append(ch)
    ok = (ord('a') <= ch <= ord('z')) or (ord('0') <= ch <= ord('9')) or ch == ord('_')
    score += int(ok)
    acc = (rol(acc ^ t ^ i, 3) + 0x01020304 + t * 13) & 0xFFFFFFFF

s = ''.join(chr(c) for c in body)
flag = f"gigem{{{s}}}"

digest0 = state ^ 0x13579BDF
digest1 = acc ^ 0x2468ACE0
digest2 = rol(state, 7) ^ ror(acc, 5)
digest3 = (ror(state, 11) + rol(acc, 3)) & 0xFFFFFFFF
next_token = (digest0 ^ rol(digest1, 5) ^ ror(digest2, 9) ^ digest3) + 0x9E3779B9 + score
next_token &= 0xFFFFFFFF

print(flag)
print(f"acc=0x{acc:08x}")
print(f"score={score}")
print(f"digest={[hex(x) for x in [digest0, digest1, digest2, digest3]]}")
print(f"next_token=0x{next_token:08x}")
