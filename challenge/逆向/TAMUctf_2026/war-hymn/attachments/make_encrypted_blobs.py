
og_key = "Hullabaloo, Caneck! Caneck! Hullabaloo, Caneck! Caneck! All hail to dear old Texas A&M Rally around Maroon and White Good luck to dear old Texas Aggies They are the boys who show the real old fight That good old Aggie spirit thrills us And makes us yell and yell and yell So let's fight for dear old Texas A&M We're going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! Texas A&M! Good-bye to texas university So long to the orange and the white Good luck to dear old Texas Aggies They are the boys that show the real old fight 'The eyes of Texas are upon you . . .' That is the song they sing so well So good-bye to texas university We're going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! Texas A&M!"
key = og_key[8:]

def encrypt(blob, key):
    encrypted = bytearray()
    for i, b in enumerate(blob):
        encrypted_char = b ^ ((ord(key[i % len(key)]) + 21) & 0xff)
        encrypted.append(encrypted_char)

    return bytes(encrypted)


first = "those_who_know"

enc = encrypt(first.encode(), key)

print("unsigned char encrypted[] = {")
print(", ".join(f"0x{b:02x}" for b in enc))
print("};")
print(f"size_t encrypted_len = {len(enc)};")