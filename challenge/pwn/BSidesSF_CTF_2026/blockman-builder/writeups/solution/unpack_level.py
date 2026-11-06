#!/usr/bin/env python3
import argparse
import base64
import sys
import zlib


def decode_blob(data: bytes) -> bytes:
    raw = base64.b64decode(data)
    return zlib.decompress(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="Decode base64+zlib level data to ASCII edits.")
    parser.add_argument("path", nargs="?", default="-", help="Input file (default: stdin)")
    args = parser.parse_args()

    if args.path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(args.path, "rb") as f:
            data = f.read()

    data = b"".join(data.split())
    try:
        out = decode_blob(data)
    except Exception as exc:
        print(f"decode failed: {exc}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
