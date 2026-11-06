#!/usr/bin/env python3
"""
Starter skeleton for wreck-26's vellum.

On connect, the server base64-encodes a freshly-compiled ELF, sends it as
the first line (`VARIANT:<b64>\\n`), then execs the binary with stdin and
stdout wired to the socket. This stub handles step 1 — reading the ELF and
dumping its symbol table — and leaves the exploit to you.

The scribe reads two folios from you:

    puts("<banner>");
    puts("folio 1/2");   fgets(quill, 128, stdin);   printf(quill);
    puts("folio 2/2");   fgets(quill, 128, stdin);   printf(quill);
    if (break_seal()) reveal_relic();
    else              puts("the seal holds");

Everything about the binary that matters to the exploit — the .bss
address of the `seal` variable, the sigil value the seal must equal to
reveal the relic, and the stack layout printf sees — differs per variant.
Your exploit has to extract them from the handed-out ELF at run time.

Usage:
    python3 honest_solver.py HOST PORT
"""

import base64
import sys

from pwn import remote, ELF, context

context.arch = "amd64"
context.log_level = "warning"


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} HOST PORT", file=sys.stderr)
        return 2

    host, port = sys.argv[1], int(sys.argv[2])
    io = remote(host, port)

    hdr = io.recvline().strip()
    if not hdr.startswith(b"VARIANT:"):
        print(f"unexpected header: {hdr!r}", file=sys.stderr)
        return 1

    elf_bytes = base64.b64decode(hdr[len(b"VARIANT:"):])
    path = "./variant.elf"
    with open(path, "wb") as f:
        f.write(elf_bytes)

    elf = ELF(path, checksec=False)
    print(f"saved variant to {path} ({len(elf_bytes)} bytes)")
    print(f"entry:  0x{elf.entry:x}")
    print(f"symbols of interest:")
    for name in ("main", "break_seal", "reveal_relic", "seal"):
        if name in elf.symbols:
            print(f"  {name:14s} 0x{elf.symbols[name]:x}")

    # TODO:
    #   1. read the banner + "folio 1/2" prompt
    #   2. send a format-string probe that reveals the stack layout
    #   3. parse the leak to find the quill offset and the PIE base
    #   4. read the "folio 2/2" prompt
    #   5. send a payload that sets the seal variable to the sigil the
    #      binary compares it against — the sigil is baked into the ELF
    #      but not printed anywhere, so you'll need to recover it yourself
    #   6. if you get it right the next thing you read will be the flag
    io.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
