from pwn import *
import hashlib
from Crypto.Hash import HMAC, SHA256
import time

# set up the Docker container before running
IP = "127.0.0.1"
PORT = 7777
p = remote(IP, PORT)

def solve(debug=False):
    key = [b""]*32
    
    # Use the scan_hex_array exploit to recover the HMAC key one byte at a time
    for i in range(1, 33):
        p.recvuntil(b"0123456789abcdef\n")
        
        data = p.recvline().strip().split(b": ")[1]
        polytag = p.recvline().strip().split(b": ")[1]
        hmactag = p.recvline().strip().split(b": ")[1]
        
        my_ciphertext = b"00"*(32-i) + b".."
        my_iv = b"00"*12
        my_poly1305 = b"00"*16
        my_hmac = b"00"*32
        
        p.recvuntil(b">>> Enter a ciphertext to decrypt:\n")
        p.sendline(my_ciphertext)
        p.recvuntil(b">>> Enter an IV for the message:\n")
        p.sendline(my_iv)
        p.recvuntil(b">>> Enter a Poly1305 authentication tag for the message:\n")
        p.sendline(my_poly1305)
        p.recvuntil(b">>> Enter an HMAC tag for the message:\n")
        p.sendline(my_hmac)
        
        line = p.recvline().strip()
        message = line.split(b"[+] Decrypting message ")[1]
        key[-i] = message[-2:]
    
    # Reconstruct the HMAC key
    hmac_key = b"".join(key)
    hmac_key = bytes.fromhex(hmac_key.decode('ascii'))
    
    # Test the HMAC validation against the given message
    if debug:
        polytag_debug = bytes.fromhex(polytag.decode('ascii'))
        data_debug = bytes.fromhex(data.decode('ascii'))
        
        h = HMAC.new(hmac_key, msg=data_debug+polytag_debug, digestmod=SHA256)
        print("Computed digest:", h.hexdigest())
        print("Provided digest: ", hmactag)
    
    # Now forge an HMAC for a new ciphertext with a tweaked ciphertext
    # and whatever Poly1305 tag we want (the code fails to do Poly1305 verification)
    p.recvuntil(b"0123456789abcdef\n")
    
    my_ciphertext = b"000000" + data[6:]
    my_iv = b"0123456789ab".hex().encode('ascii')
    my_poly1305 = b"00"*16
    
    polytag = bytes.fromhex(my_poly1305.decode('ascii'))
    ct = bytes.fromhex(my_ciphertext.decode('ascii'))
    
    h = HMAC.new(hmac_key, msg=ct+polytag, digestmod=SHA256)
    my_hmac = h.hexdigest().encode('ascii')
    
    if debug:
        print("Sending ciphertext: ", my_ciphertext)
        print("Sending IV: ", my_iv)
        print("Sending poly1305 tag:", my_poly1305)
        print("Sending HMAC: ", my_hmac)
    
    p.recvuntil(b">>> Enter a ciphertext to decrypt:\n")
    p.sendline(my_ciphertext)
    p.recvuntil(b">>> Enter an IV for the message:\n")
    p.sendline(my_iv)
    p.recvuntil(b">>> Enter a Poly1305 authentication tag for the message:\n")
    p.sendline(my_poly1305)
    p.recvuntil(b">>> Enter an HMAC tag for the message:\n")
    p.sendline(my_hmac)
    
    # Extract the flag
    p.recvuntil(b"Congrats! Here's your message:\n")
    flag = p.recvline()
    flag = bytes.fromhex(flag.decode('ascii'))[:-1]
    
    return b"byu" + flag[3:]

start = time.time()
flag = solve(debug=True)
end = time.time()
print(f"Solve took {end - start:.4f} seconds. Flag: {flag}")