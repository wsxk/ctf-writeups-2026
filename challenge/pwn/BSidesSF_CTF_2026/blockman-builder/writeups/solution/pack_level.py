#!/usr/bin/env python3
import argparse
import base64
import sys
import zlib


def encode_text(data: bytes) -> bytes:
    compressed = zlib.compress(data, level=9)
    return base64.b64encode(compressed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Encode ASCII edits to base64+zlib level data.")
    parser.add_argument("path", nargs="?", default="-", help="Input file (default: stdin)")
    args = parser.parse_args()

    if args.path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(args.path, "rb") as f:
            data = f.read()

    try:
        out = encode_text(data)
    except Exception as exc:
        print(f"encode failed: {exc}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(out)
    sys.stdout.buffer.write(b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
