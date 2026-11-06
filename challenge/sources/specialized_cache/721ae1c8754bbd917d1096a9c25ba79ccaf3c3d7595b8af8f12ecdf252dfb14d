#!/usr/bin/env python3
import base64
import binascii
import os
import signal
import subprocess
import sys
import tempfile


TIMEOUT = int(os.environ.get("TIMEOUT", "2400"))
MAX_SOLVER = int(os.environ.get("MAX_SOLVER", str(16 * 1024 * 1024)))


def main() -> int:
    signal.alarm(TIMEOUT + 10)

    sys.stdout.write("Give me the b64 for your solver: ")
    sys.stdout.flush()
    b64 = sys.stdin.readline().strip()
    if not b64:
        print("empty input")
        return 1

    try:
        solver = base64.b64decode(b64, validate=True)
    except binascii.Error:
        print("invalid base64")
        return 1

    if not solver:
        print("empty solver")
        return 1
    if len(solver) > MAX_SOLVER:
        print("solver too large")
        return 1

    fd, path = tempfile.mkstemp(prefix="solver-", suffix=".bin")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(solver)
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
