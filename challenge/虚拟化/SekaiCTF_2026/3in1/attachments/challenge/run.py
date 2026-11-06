#!/usr/bin/env python3
import base64
import binascii
import os
import signal
import subprocess
import sys
import tempfile


TIMEOUT = int(os.environ.get("TIMEOUT", "180"))
MAX_PAYLOAD = int(os.environ.get("MAX_PAYLOAD", str(2 * 1024 * 1024)))


def main() -> int:
    signal.alarm(TIMEOUT + 5)

    sys.stdout.write("Give me the b64 for your exploit: ")
    sys.stdout.flush()
    b64 = sys.stdin.readline().strip()
    if not b64:
        print("empty input")
        return 1

    try:
        payload = base64.b64decode(b64, validate=True) + b"//"
    except binascii.Error:
        print("invalid base64")
        return 1

    if not payload:
        print("empty payload")
        return 1
    if len(payload) > MAX_PAYLOAD:
        print("payload too large")
        return 1

    fd, path = tempfile.mkstemp(prefix="challenge-", suffix=".js")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
        os.chmod(path, 0o644)

        return subprocess.run(
            ["/challenge/run.sh", path],
            stdin=subprocess.DEVNULL,
            timeout=TIMEOUT,
        ).returncode
    except subprocess.TimeoutExpired:
        print("timeout")
        return 124
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
