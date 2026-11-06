import itertools
import hashlib

FLAG = 'byuctf{j0mp1n6_thr0ugh_4ndr01d_****_styl3s_28f6}'

# haven't seen caps yet lol
characters = 'qwertyuiopasdfghjklzxcvbnm1234567890'

indices = b'r\x9c\x11\x84m\x01\x07M\x9a\xafM\x90\xf8@c\"'
# trying to quickly do every other character is weird
known = {i*2: indices[i] for i in range(len(indices))}

for opt in itertools.product(characters, repeat=4):
    test = hashlib.sha256(''.join(opt).encode()).digest()
    if all(test[i] == v for i, v in known.items()):
        print(''.join(opt))