#!/usr/bin/env python3
import argparse
import base64
import pathlib
import sys

from pwn import context, remote


def chunked(s: str, n: int):
    for i in range(0, len(s), n):
        yield s[i : i + n]


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload compressed solver over jail shell and execute it")
    parser.add_argument("host", nargs="?", default="localhost")
    parser.add_argument("port", nargs="?", type=int, default=5000)
    parser.add_argument("solver_xz", nargs="?", default="build/solver.xz")
    parser.add_argument("--chunk-size", type=int, default=768)
    parser.add_argument("--prompt-timeout", type=float, default=10.0)
    args = parser.parse_args()

    solver_path = pathlib.Path(args.solver_xz)
    if not solver_path.is_file():
        print(f"error: solver archive not found: {solver_path}", file=sys.stderr)
        return 1

    if args.chunk_size <= 0:
        print("error: --chunk-size must be > 0", file=sys.stderr)
        return 1

    context.log_level = "info"

    blob = base64.b64encode(solver_path.read_bytes()).decode("ascii")
    io = remote(args.host, args.port)

    try:
        # Jail boot + login shell can take a while; wait for shell prompt.
        io.recvuntil(b"$ ", timeout=args.prompt_timeout)
    except EOFError:
        print("error: connection closed before prompt", file=sys.stderr)
        return 1
    except Exception:
        print(f"error: did not receive shell prompt '$ ' within {args.prompt_timeout:.1f}s", file=sys.stderr)
        return 1

    io.sendline(b"set -e")
    io.sendline(b"TMP_B64=/tmp/solver_upload.b64")
    io.sendline(b"TMP_XZ=/tmp/solver.xz")
    io.sendline(b"TMP_BIN=/tmp/solver")
    io.sendline(b"rm -f \"$TMP_B64\" \"$TMP_XZ\" \"$TMP_BIN\"")

    for part in chunked(blob, args.chunk_size):
        io.sendline(f"echo '{part}' >> \"$TMP_B64\"".encode())

    io.sendline(b"base64 -d \"$TMP_B64\" > \"$TMP_XZ\"")
    io.sendline(b"xz -d -f \"$TMP_XZ\"")
    io.sendline(b"chmod +x \"$TMP_BIN\"")
    io.sendline(b'"$TMP_BIN"')

    io.interactive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
