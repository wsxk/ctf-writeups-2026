
og_key = "Hullabaloo, Caneck! Caneck! Hullabaloo, Caneck! Caneck! All hail to dear old Texas A&M Rally around Maroon and White Good luck to dear old Texas Aggies They are the boys who show the real old fight That good old Aggie spirit thrills us And makes us yell and yell and yell So let's fight for dear old Texas A&M We're going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! Texas A&M! Good-bye to texas university So long to the orange and the white Good luck to dear old Texas Aggies They are the boys that show the real old fight 'The eyes of Texas are upon you . . .' That is the song they sing so well So good-bye to texas university We're going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! Texas A&M!"
key = og_key[8:]

# Decrypt function that is called in main
def main_decrypt(buf: bytearray, key: bytes):
    for i in range(len(buf)):
        buf[i] ^= (ord(key[i]) + 0x15) & 0xff


local_14d_first = bytearray(12) 
local_14d_first[0:12] = bytes([
    0xab, 0xf4, 0x33, 0x5a, 0x3b, 0x59, 0xf0, 0x1f,  # 0x00-0x07
    0x14, 0xe6, 0x19, 0x50, 0x20, 0x13])

main_decrypt(local_14d_first, key)

print("Decrypted data at local_14d_first:", local_14d_first.decode('latin1'), "\n")

# Encrypted location of decrypt function

local_b8 = bytearray(25)
local_b8[0:25] = bytes([
    0xaa, 0xed, ord('/'), ord('\\'), ord(','), ord('X'), 0xe0, 0x12,
    0x1d, 0xe3, ord(']'), ord('F'), ord('-'), 0x1b, 0xad, 0x0c,
    0x19, 0xec, ord('_'), ord('Q'), ord('<'), 0xfe, 0xe8, 0xee, 0x18
])


main_decrypt(local_b8, key)
print("ACTUALLY IMPORTANT: Location of decrypt function:", local_b8.rstrip(b"\x00").decode())

# Encrypted location of encrypted zlib data

uStack_f8 = bytearray(19)
uStack_f8[0:19] = bytes([
    0xaa, 0xe6, ord('2'), ord('F'), ord('v'), 0x05, 0xe6, 0x19,
    0x0d, 0xf2, ord('S'), 0x1b, ord(':'), 0x03, 0xe5, 0x1c, 0x1d, 0xf2
])

main_decrypt(uStack_f8, key)
print("ACTUALLY IMPORTANT: Location of encrypted zlib data:", uStack_f8.rstrip(b"\x00").decode())


# Encrypted location of key

local_98 = bytearray(26)
local_98[0:26] = bytes([
    0xaa, 0xed, ord('/'), ord('\\'), ord(','), ord('X'), 0xe0, 0x15,
    0x16, 0xf3, ord('B'), ord('G'), ord('-'), 0x15, 0xf7, 0x15,
    ord('\n'), 0xf3, ord('\x18'), ord('R'), ord('1'), 0xe5, 0xe3, 
    0xe0, ord('\x1a')
])

main_decrypt(local_98, key)
print("ACTUALLY IMPORTANT: Location of key:", local_98.rstrip(b"\x00").decode(), "\n")

deobf1 = bytearray(14)
deobf1[0:14] = bytes([
    0xf0,  # 0
    0xec,  # 1
    0x2e,  # 2
    0x46,  # 3
    0x3d,  # 4
    0x29,  # 5
    0xf4,  # 6
    0x12,  # 7
    0x17,  # 8
    0xdf,  # 9
    0x5d,  # 10
    0x5b,  # 11
    0x37,  # 12
    0x01   # 13
])

main_decrypt(deobf1, key)
print("Deobfuscated string 1:", deobf1.decode('latin1'))

local_14d_second = bytearray(14) 
local_14d_second[0:14] = bytes([
    0xab, 0xf4, 0x33,  # 0x08-0x0f
    0x5a, 0x3b, 0x59, 0xf0, 0x1f, 0x14, 0xe6, 0x19, 0x53, 0x3c  # 0x10-0x1a
])

main_decrypt(local_14d_second, key)

print("Decrypted data at local_14d_second:", local_14d_second.decode('latin1'))
