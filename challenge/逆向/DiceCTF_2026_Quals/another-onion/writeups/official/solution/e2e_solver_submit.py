#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import socket
import stat
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKDIR = ROOT / "e2e_work"
WORKDIR.mkdir(exist_ok=True)

BINARY_PATH = WORKDIR / "another_onion"
RECOVERED_PATH = WORKDIR / "recovered"

CHALLENGE_HOST = os.getenv("CHALLENGE_HOST", "challenge")
HTTP_PORT = int(os.getenv("CHALLENGE_HTTP_PORT", "8000"))
TCP_PORT = int(os.getenv("CHALLENGE_TOKEN_PORT", "31337"))
NSEGMENTS = os.getenv("NSEGMENTS")


def wait_for_binary_endpoint(max_attempts: int = 240, delay: float = 1.0) -> bytes:
    url = f"http://{CHALLENGE_HOST}:{HTTP_PORT}/"
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read()
            if not data:
                raise RuntimeError("empty binary payload")
            print(f"[solver] downloaded binary ({len(data)} bytes) from {url}")
            return data
        except Exception as exc:  # noqa: BLE001
            if attempt == max_attempts:
                raise RuntimeError(f"timed out waiting for {url}: {exc}") from exc
            if attempt % 10 == 0:
                print(f"[solver] waiting for challenge endpoint ({attempt}/{max_attempts})...")
            time.sleep(delay)
    raise RuntimeError("unreachable")


def run_checked(cmd: list[str]) -> None:
    print(f"[solver] running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}")


def extract_token(binary_output: bytes) -> str:
    text = binary_output.decode("utf-8", errors="replace")
    match = re.search(
        r"Congratulations!\s*Please submit the following token to get the flag:\s*([0-9a-fA-F]+)",
        text,
    )
    if match is not None:
        token = match.group(1)
        print(f"[solver] extracted token: {token}")
        return token
    raise RuntimeError(f"could not parse token from binary output: {text!r}")


def submit_token(token: str) -> str:
    with socket.create_connection((CHALLENGE_HOST, TCP_PORT), timeout=10) as sock:
        sock.settimeout(10)
        try:
            prompt = sock.recv(1024)
        except TimeoutError:
            prompt = b""
        if prompt:
            print(f"[solver] prompt: {prompt.decode('utf-8', errors='replace').rstrip()}")
        sock.sendall(token.encode() + b"\n")
        chunks = []
        while True:
            try:
                part = sock.recv(4096)
            except TimeoutError:
                break
            if not part:
                break
            chunks.append(part)
        response = b"".join(chunks).decode("utf-8", errors="replace").strip()
    return response


def main() -> int:
    data = wait_for_binary_endpoint()
    BINARY_PATH.write_bytes(data)
    BINARY_PATH.chmod(BINARY_PATH.stat().st_mode | stat.S_IXUSR)

    solve_cmd = ["python3", "solution/solve.py", str(BINARY_PATH), "-o", str(RECOVERED_PATH)]
    if NSEGMENTS:
        solve_cmd.insert(2, "--segments")
        solve_cmd.insert(3, str(int(NSEGMENTS)))
    run_checked(solve_cmd)

    with RECOVERED_PATH.open("rb") as rec_in:
        proc = subprocess.run([str(BINARY_PATH)], cwd=ROOT, stdin=rec_in, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"failed to run solved binary (rc={proc.returncode}): {proc.stderr.decode('utf-8', errors='replace')}"
        )
    token = extract_token(proc.stdout)

    response = submit_token(token)
    print(response)
    if "invalid token" in response.lower():
        raise RuntimeError("submission rejected by challenge service")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"[solver] error: {exc}", file=sys.stderr)
        raise SystemExit(1)
